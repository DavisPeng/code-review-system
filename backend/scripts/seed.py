"""
Seed Script - Create default C++ rules
Run with: python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import ReviewRule, RuleSet


DEFAULT_CPP_RULES = [
    # Coding Standards
    {
        "name": "cpp-indentation",
        "description": "Use consistent indentation (4 spaces)",
        "category": "coding_standard",
        "severity": "warning",
        "pattern": r"^\t|    [^\s]",
    },
    {
        "name": "cpp-naming-convention",
        "description": "Follow naming conventions (snake_case for variables, PascalCase for classes)",
        "category": "coding_standard",
        "severity": "info",
    },
    {
        "name": "cpp-include-guards",
        "description": "Header files should have include guards",
        "category": "coding_standard",
        "severity": "warning",
    },
    {
        "name": "cpp-const-correctness",
        "description": "Use const for variables that should not be modified",
        "category": "coding_standard",
        "severity": "warning",
    },
    
    # Memory Safety
    {
        "name": "cpp-null-check",
        "description": "Check pointers for null before dereferencing",
        "category": "memory_safety",
        "severity": "error",
    },
    {
        "name": "cpp-memory-leak",
        "description": "Ensure dynamically allocated memory is freed",
        "category": "memory_safety",
        "severity": "error",
    },
    {
        "name": "cpp-buffer-overflow",
        "description": "Avoid buffer overflows by checking array bounds",
        "category": "memory_safety",
        "severity": "error",
    },
    {
        "name": "cpp-use-after-free",
        "description": "Avoid using pointers after memory is freed",
        "category": "memory_safety",
        "severity": "error",
    },
    {
        "name": "cpp-smart-pointers",
        "description": "Prefer smart pointers over raw pointers",
        "category": "memory_safety",
        "severity": "warning",
    },
    
    # Performance
    {
        "name": "cpp-avoid-unnecessary-copies",
        "description": "Avoid unnecessary copies of objects",
        "category": "performance",
        "severity": "warning",
    },
    {
        "name": "cpp-use-emplace",
        "description": "Use emplace instead of push for containers",
        "category": "performance",
        "severity": "info",
    },
    {
        "name": "cpp-reserve-vector",
        "description": "Reserve vector capacity when size is known",
        "category": "performance",
        "severity": "info",
    },
    
    # Concurrency
    {
        "name": "cpp-race-condition",
        "description": "Watch for race conditions in multithreaded code",
        "category": "concurrency",
        "severity": "error",
    },
    {
        "name": "cpp-thread-join",
        "description": "Ensure threads are joined before destruction",
        "category": "concurrency",
        "severity": "warning",
    },
    {
        "name": "cpp-mutex-deadlock",
        "description": "Avoid deadlock by consistent lock ordering",
        "category": "concurrency",
        "severity": "error",
    },
    
    # Logic Errors
    {
        "name": "cpp-uninitialized-variable",
        "description": "Variables should be initialized before use",
        "category": "logic_error",
        "severity": "error",
    },
    {
        "name": "cpp-divide-by-zero",
        "description": "Check for divide by zero",
        "category": "logic_error",
        "severity": "error",
    },
    {
        "name": "cpp-overflow-check",
        "description": "Check for integer overflow",
        "category": "logic_error",
        "severity": "warning",
    },
    
    # Maintainability
    {
        "name": "cpp-function-length",
        "description": "Keep functions short and focused (max 50 lines)",
        "category": "maintainability",
        "severity": "info",
    },
    {
        "name": "cpp-complexity",
        "description": "Avoid overly complex code (cyclomatic complexity < 10)",
        "category": "maintainability",
        "severity": "warning",
    },
    {
        "name": "cpp-magic-numbers",
        "description": "Avoid magic numbers, use constants",
        "category": "maintainability",
        "severity": "info",
    },
]

DEFAULT_RULESETS = [
    {
        "name": "cpp-basic",
        "description": "Basic C++ coding standards",
        "is_default": True,
        "rules": ["cpp-indentation", "cpp-naming-convention", "cpp-include-guards", "cpp-const-correctness"],
    },
    {
        "name": "cpp-memory-safety",
        "description": "Memory safety rules for C++",
        "is_default": False,
        "rules": ["cpp-null-check", "cpp-memory-leak", "cpp-buffer-overflow", "cpp-use-after-free", "cpp-smart-pointers"],
    },
    {
        "name": "cpp-performance",
        "description": "C++ performance optimization rules",
        "is_default": False,
        "rules": ["cpp-avoid-unnecessary-copies", "cpp-use-emplace", "cpp-reserve-vector"],
    },
]


def seed_rules(db):
    """Create default C++ rules"""
    print("Seeding C++ rules...")
    
    for rule_data in DEFAULT_CPP_RULES:
        existing = db.query(ReviewRule).filter(ReviewRule.name == rule_data["name"]).first()
        if existing:
            print(f"  - {rule_data['name']} already exists, skipping")
            continue
            
        rule = ReviewRule(**rule_data)
        db.add(rule)
        print(f"  + Created rule: {rule_data['name']}")
    
    db.commit()
    print(f"Seeded {len(DEFAULT_CPP_RULES)} rules")


def seed_rulesets(db):
    """Create default rule sets"""
    print("Seeding rule sets...")
    
    for ruleset_data in DEFAULT_RULESETS:
        rule_names = ruleset_data.pop("rules")
        
        existing = db.query(RuleSet).filter(RuleSet.name == ruleset_data["name"]).first()
        if existing:
            print(f"  - {ruleset_data['name']} already exists, skipping")
            continue
            
        ruleset = RuleSet(**ruleset_data)
        db.add(ruleset)
        db.flush()
        
        # Add rules to ruleset
        for rule_name in rule_names:
            rule = db.query(ReviewRule).filter(ReviewRule.name == rule_name).first()
            if rule:
                ruleset.rules.append(rule)
        
        print(f"  + Created ruleset: {ruleset_data['name']}")
    
    db.commit()
    print(f"Seeded {len(DEFAULT_RULESETS)} rule sets")


def main():
    db = SessionLocal()
    try:
        seed_rules(db)
        seed_rulesets(db)
        print("\n✅ Seeding completed successfully!")
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()