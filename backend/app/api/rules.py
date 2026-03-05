"""
Rules API
Endpoints for managing review rules and rule sets
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import ReviewRule, RuleSet

router = APIRouter()


# Pydantic schemas
class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    severity: str = "warning"
    pattern: Optional[str] = None
    prompt_section: Optional[str] = None
    enabled: bool = True


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    pattern: Optional[str] = None
    prompt_section: Optional[str] = None
    enabled: Optional[bool] = None


class RuleSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    severity: str
    pattern: Optional[str]
    prompt_section: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True


class RuleSetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False


class RuleSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None


class RuleSetSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_default: bool
    rules: List[RuleSchema] = []

    class Config:
        from_attributes = True


# Rules endpoints
@router.get("/rules", response_model=List[RuleSchema])
async def list_rules(
    category: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all review rules"""
    query = db.query(ReviewRule)

    if category:
        query = query.filter(ReviewRule.category == category)
    if enabled is not None:
        query = query.filter(ReviewRule.enabled == enabled)

    rules = query.all()
    return rules


@router.get("/rules/{rule_id}", response_model=RuleSchema)
async def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get rule by ID"""
    rule = db.query(ReviewRule).filter(ReviewRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return rule


@router.post("/rules", response_model=RuleSchema)
async def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    """Create a new rule"""
    existing = db.query(ReviewRule).filter(ReviewRule.name == rule.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule name already exists")

    db_rule = ReviewRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    return db_rule


@router.put("/rules/{rule_id}", response_model=RuleSchema)
async def update_rule(rule_id: int, rule: RuleUpdate, db: Session = Depends(get_db)):
    """Update a rule"""
    db_rule = db.query(ReviewRule).filter(ReviewRule.id == rule_id).first()

    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for key, value in rule.model_dump(exclude_unset=True).items():
        setattr(db_rule, key, value)

    db.commit()
    db.refresh(db_rule)

    return db_rule


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a rule"""
    db_rule = db.query(ReviewRule).filter(ReviewRule.id == rule_id).first()

    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(db_rule)
    db.commit()

    return {"message": "Rule deleted successfully"}


# Rule sets endpoints
@router.get("/rulesets", response_model=List[RuleSetSchema])
async def list_rulesets(db: Session = Depends(get_db)):
    """List all rule sets"""
    rule_sets = db.query(RuleSet).all()
    return rule_sets


@router.get("/rulesets/{ruleset_id}", response_model=RuleSetSchema)
async def get_ruleset(ruleset_id: int, db: Session = Depends(get_db)):
    """Get rule set by ID"""
    ruleset = db.query(RuleSet).filter(RuleSet.id == ruleset_id).first()

    if not ruleset:
        raise HTTPException(status_code=404, detail="Rule set not found")

    return ruleset


@router.post("/rulesets", response_model=RuleSetSchema)
async def create_ruleset(ruleset: RuleSetCreate, db: Session = Depends(get_db)):
    """Create a new rule set"""
    existing = db.query(RuleSet).filter(RuleSet.name == ruleset.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rule set name already exists")

    db_ruleset = RuleSet(**ruleset.model_dump())
    db.add(db_ruleset)
    db.commit()
    db.refresh(db_ruleset)

    return db_ruleset


@router.put("/rulesets/{ruleset_id}", response_model=RuleSetSchema)
async def update_ruleset(ruleset_id: int, ruleset: RuleSetUpdate, db: Session = Depends(get_db)):
    """Update a rule set"""
    db_ruleset = db.query(RuleSet).filter(RuleSet.id == ruleset_id).first()

    if not db_ruleset:
        raise HTTPException(status_code=404, detail="Rule set not found")

    for key, value in ruleset.model_dump(exclude_unset=True).items():
        setattr(db_ruleset, key, value)

    db.commit()
    db.refresh(db_ruleset)

    return db_ruleset


@router.post("/rulesets/{ruleset_id}/apply")
async def apply_ruleset_to_project(
    ruleset_id: int,
    project_id: int,
    db: Session = Depends(get_db)
):
    """Apply a rule set to a project"""
    from app.models.models import Project

    ruleset = db.query(RuleSet).filter(RuleSet.id == ruleset_id).first()
    if not ruleset:
        raise HTTPException(status_code=404, detail="Rule set not found")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Apply ruleset to project
    project.rule_sets.append(ruleset)
    db.commit()

    return {"message": f"Rule set '{ruleset.name}' applied to project '{project.name}'"}


@router.delete("/rulesets/{ruleset_id}")
async def delete_ruleset(ruleset_id: int, db: Session = Depends(get_db)):
    """Delete a rule set"""
    db_ruleset = db.query(RuleSet).filter(RuleSet.id == ruleset_id).first()

    if not db_ruleset:
        raise HTTPException(status_code=404, detail="Rule set not found")

    db.delete(db_ruleset)
    db.commit()

    return {"message": "Rule set deleted successfully"}