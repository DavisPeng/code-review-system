"""
AI Review Engine
Uses LLM for intelligent code review
"""
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import anthropic
import openai
from app.config import settings
from app.models.models import ReviewRule, RuleSet
from app.database import SessionLocal


@dataclass
class AIReviewIssue:
    """AI-generated review issue"""
    file_path: str
    line_number: int
    severity: str  # error, warning, info, suggestion
    category: str  # coding_standard, logic_error, performance, memory_safety, concurrency, maintainability
    message: str
    suggestion: str


@dataclass
class AIReviewResult:
    """Result of AI code review"""
    issues: List[AIReviewIssue]
    total_issues: int
    error_count: int
    warning_count: int
    info_count: int
    suggestion_count: int
    token_usage: int
    model: str
    success: bool
    error_message: Optional[str] = None


class AIReviewEngine:
    """AI-powered code review engine"""
    
    def __init__(self, provider: str = None):
        self.provider = provider or settings.AI_PROVIDER
        self.anthropic_client = None
        self.openai_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize API clients"""
        if self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def review(
        self,
        diff_content: str,
        file_path: str,
        rules: List[ReviewRule] = None,
        rulesets: List[RuleSet] = None,
        project_context: str = ""
    ) -> AIReviewResult:
        """
        Review code diff using AI
        
        Args:
            diff_content: Git diff content
            file_path: Path to the file being reviewed
            rules: Optional list of review rules
            rulesets: Optional list of rule sets
            project_context: Optional project context
            
        Returns:
            AIReviewResult with identified issues
        """
        # Build prompt
        system_prompt = self._build_system_prompt(rules, rulesets)
        user_prompt = self._build_user_prompt(diff_content, file_path, project_context)
        
        try:
            if self.provider == "anthropic":
                return self._review_anthropic(system_prompt, user_prompt)
            elif self.provider == "openai":
                return self._review_openai(system_prompt, user_prompt)
            else:
                return AIReviewResult(
                    issues=[],
                    total_issues=0,
                    error_count=0,
                    warning_count=0,
                    info_count=0,
                    suggestion_count=0,
                    token_usage=0,
                    model="",
                    success=False,
                    error_message=f"Unknown provider: {self.provider}"
                )
        except Exception as e:
            return AIReviewResult(
                issues=[],
                total_issues=0,
                error_count=0,
                warning_count=0,
                info_count=0,
                suggestion_count=0,
                token_usage=0,
                model="",
                success=False,
                error_message=str(e)
            )
    
    def _build_system_prompt(self, rules: List[ReviewRule] = None, rulesets: List[RuleSet] = None) -> str:
        """Build system prompt with rules"""
        prompt = """You are an expert C/C++ code reviewer. Your task is to review code changes and identify issues.

Review Categories:
- coding_standard: Code style and convention violations
- logic_error: Potential bugs and logic issues
- performance: Performance optimization opportunities
- memory_safety: Memory management issues ( leaks, null pointers, etc.)
- concurrency: Multi-threading issues
- maintainability: Code maintainability concerns
- security: Security vulnerabilities

Severity Levels:
- error: Critical issues that must be fixed
- warning: Important issues that should be fixed
- info: Informational observations
- suggestion: Optional improvements

Output Format:
You must output your review as a JSON array with the following structure:
```json
[
  {
    "file_path": "src/main.cpp",
    "line_number": 42,
    "severity": "warning",
    "category": "performance",
    "message": "Description of the issue",
    "suggestion": "Suggested fix"
  }
]
```

Important:
1. Only output valid JSON array
2. Do not include any additional text
3. line_number should be the approximate line in the diff where the issue occurs
4. Be concise but specific in your feedback
"""
        
        # Add custom rules if provided
        if rules:
            rule_sections = []
            for rule in rules:
                if rule.enabled and rule.prompt_section:
                    rule_sections.append(f"- {rule.name}: {rule.prompt_section}")
            
            if rule_sections:
                prompt += "\n\nAdditional Review Rules:\n" + "\n".join(rule_sections)
        
        return prompt
    
    def _build_user_prompt(self, diff_content: str, file_path: str, project_context: str) -> str:
        """Build user prompt with diff content"""
        prompt = f"""Please review the following code change in `{file_path}`:
"""
        if project_context:
            prompt += f"\nProject Context:\n{project_context}\n"
        
        prompt += f"""
Diff:
```
{diff_content}
```

Identify any issues and output as JSON:
"""
        return prompt
    
    def _review_anthropic(self, system_prompt: str, user_prompt: str) -> AIReviewResult:
        """Review using Anthropic Claude"""
        if not self.anthropic_client:
            return AIReviewResult(
                issues=[], total_issues=0, error_count=0, warning_count=0,
                info_count=0, suggestion_count=0, token_usage=0, model="",
                success=False, error_message="Anthropic client not initialized"
            )
        
        model = settings.CLAUDE_MODEL
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        # Extract JSON from response
        content = response.content[0].text
        issues = self._parse_json_response(content)
        
        token_usage = response.usage.input_tokens + response.usage.output_tokens
        
        return self._create_result(issues, token_usage, model)
    
    def _review_openai(self, system_prompt: str, user_prompt: str) -> AIReviewResult:
        """Review using OpenAI"""
        if not self.openai_client:
            return AIReviewResult(
                issues=[], total_issues=0, error_count=0, warning_count=0,
                info_count=0, suggestion_count=0, token_usage=0, model="",
                success=False, error_message="OpenAI client not initialized"
            )
        
        model = settings.OPENAI_MODEL
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=4096
        )
        
        content = response.choices[0].message.content
        issues = self._parse_json_response(content)
        
        token_usage = response.usage.total_tokens
        
        return self._create_result(issues, token_usage, model)
    
    def _parse_json_response(self, content: str) -> List[AIReviewIssue]:
        """Parse JSON response from AI"""
        issues = []
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', content)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array in raw content
            json_match = re.search(r'(\[[\s\S]*\])', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
        
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                for item in data:
                    issue = AIReviewIssue(
                        file_path=item.get("file_path", ""),
                        line_number=item.get("line_number", 0),
                        severity=item.get("severity", "info"),
                        category=item.get("category", "maintainability"),
                        message=item.get("message", ""),
                        suggestion=item.get("suggestion", "")
                    )
                    issues.append(issue)
        except json.JSONDecodeError:
            pass
        
        return issues
    
    def _create_result(self, issues: List[AIReviewIssue], token_usage: int, model: str) -> AIReviewResult:
        """Create AIReviewResult"""
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        info_count = sum(1 for i in issues if i.severity == "info")
        suggestion_count = sum(1 for i in issues if i.severity == "suggestion")
        
        return AIReviewResult(
            issues=issues,
            total_issues=len(issues),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            suggestion_count=suggestion_count,
            token_usage=token_usage,
            model=model,
            success=True
        )
    
    def review_large_diff(self, diff_chunks: List[Dict[str, str]], rules: List[ReviewRule] = None) -> AIReviewResult:
        """Review large diff by processing in chunks"""
        all_issues = []
        total_tokens = 0
        
        for chunk in diff_chunks:
            result = self.review(
                diff_content=chunk["diff"],
                file_path=chunk["file_path"],
                rules=rules
            )
            
            if result.success:
                all_issues.extend(result.issues)
                total_tokens += result.token_usage
        
        return AIReviewResult(
            issues=all_issues,
            total_issues=len(all_issues),
            error_count=sum(1 for i in all_issues if i.severity == "error"),
            warning_count=sum(1 for i in all_issues if i.severity == "warning"),
            info_count=sum(1 for i in all_issues if i.severity == "info"),
            suggestion_count=sum(1 for i in all_issues if i.severity == "suggestion"),
            token_usage=total_tokens,
            model=settings.CLAUDE_MODEL if self.provider == "anthropic" else settings.OPENAI_MODEL,
            success=True
        )


# Singleton instance
ai_review_engine = AIReviewEngine()