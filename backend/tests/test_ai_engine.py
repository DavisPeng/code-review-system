"""
Test AI Review Engine
Run with: pytest tests/test_ai_engine.py -v
"""
import pytest
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from app.services.ai_engine import AIReviewEngine, AIReviewIssue, AIReviewResult


class TestAIReviewIssue:
    def test_create_issue(self):
        """Test creating AI review issue"""
        issue = AIReviewIssue(
            file_path="src/main.cpp",
            line_number=10,
            severity="warning",
            category="performance",
            message="Unnecessary copy",
            suggestion="Use const reference"
        )
        
        assert issue.file_path == "src/main.cpp"
        assert issue.severity == "warning"


class TestAIReviewResult:
    def test_create_result(self):
        """Test creating AI review result"""
        issues = [
            AIReviewIssue("f1.cpp", 1, "error", "memory", "msg1", "fix1"),
            AIReviewIssue("f1.cpp", 2, "warning", "style", "msg2", "fix2"),
            AIReviewIssue("f1.cpp", 3, "info", "style", "msg3", "fix3"),
        ]
        
        result = AIReviewResult(
            issues=issues,
            total_issues=3,
            error_count=1,
            warning_count=1,
            info_count=1,
            suggestion_count=0,
            token_usage=1000,
            model="claude-3-opus",
            success=True
        )
        
        assert result.total_issues == 3
        assert result.error_count == 1
        assert result.success is True


class TestAIReviewEngine:
    def test_initialization(self):
        """Test engine initialization"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            mock_settings.OPENAI_API_KEY = ""
            
            engine = AIReviewEngine()
            assert engine.provider == "anthropic"
    
    def test_build_system_prompt(self):
        """Test system prompt building"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            prompt = engine._build_system_prompt()
            
            assert "You are an expert C/C++ code reviewer" in prompt
            assert "coding_standard" in prompt
            assert "severity" in prompt
    
    def test_build_system_prompt_with_rules(self):
        """Test system prompt with custom rules"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            
            # Create mock rules
            mock_rules = [
                MagicMock(
                    enabled=True,
                    name="test-rule",
                    prompt_section="Check for memory leaks",
                    category="memory_safety"
                )
            ]
            
            prompt = engine._build_system_prompt(rules=mock_rules)
            
            assert "test-rule" in prompt
    
    def test_build_user_prompt(self):
        """Test user prompt building"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            diff = """@@ -1,3 +1,4 @@
+int new_function() { return 0; }
 int main() { return 0; }
"""
            prompt = engine._build_user_prompt(diff, "src/main.cpp", "")
            
            assert "src/main.cpp" in prompt
            assert "new_function" in prompt
    
    def test_build_user_prompt_with_context(self):
        """Test user prompt with project context"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            prompt = engine._build_user_prompt("diff", "src/main.cpp", "This is a 3D printer slicer")
            
            assert "3D printer slicer" in prompt
    
    def test_parse_json_response(self):
        """Test JSON response parsing"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            
            json_content = '''[
                {
                    "file_path": "src/main.cpp",
                    "line_number": 10,
                    "severity": "warning",
                    "category": "performance",
                    "message": "Unnecessary copy",
                    "suggestion": "Use const reference"
                }
            ]'''
            
            issues = engine._parse_json_response(json_content)
            
            assert len(issues) == 1
            assert issues[0].file_path == "src/main.cpp"
            assert issues[0].severity == "warning"
    
    def test_parse_json_in_markdown(self):
        """Test parsing JSON in markdown code block"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            
            content = '''Here is my review:

```json
[
  {
    "file_path": "test.cpp",
    "line_number": 5,
    "severity": "error",
    "category": "memory_safety",
    "message": "Memory leak",
    "suggestion": "Free the memory"
  }
]
```

Let me know if you have questions.'''
            
            issues = engine._parse_json_response(content)
            
            assert len(issues) == 1
            assert issues[0].severity == "error"
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            
            issues = engine._parse_json_response("This is not JSON")
            
            assert len(issues) == 0
    
    def test_create_result_helper(self):
        """Test result creation helper"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            
            engine = AIReviewEngine()
            
            issues = [
                AIReviewIssue("f1.cpp", 1, "error", "memory", "msg1", "fix1"),
                AIReviewIssue("f1.cpp", 2, "warning", "style", "msg2", "fix2"),
                AIReviewIssue("f1.cpp", 3, "suggestion", "style", "msg3", "fix3"),
            ]
            
            result = engine._create_result(issues, 500, "claude-3-opus")
            
            assert result.error_count == 1
            assert result.warning_count == 1
            assert result.suggestion_count == 1
            assert result.token_usage == 500
    
    def test_review_unknown_provider(self):
        """Test review with unknown provider"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "unknown"
            
            engine = AIReviewEngine()
            
            result = engine.review("diff", "test.cpp")
            
            assert result.success is False
            assert "Unknown provider" in result.error_message
    
    @patch('app.services.ai_engine.anthropic.Anthropic')
    def test_review_anthropic_mock(self, mock_anthropic):
        """Test Anthropic review with mock"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            mock_settings.CLAUDE_MODEL = "claude-3-opus-20240229"
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            
            # Mock response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='[{"file_path": "test.cpp", "line_number": 1, "severity": "warning", "category": "style", "message": "Test", "suggestion": "Fix"}]')]
            mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
            
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client
            
            engine = AIReviewEngine()
            result = engine.review("diff", "test.cpp")
            
            assert result.success is True
    
    @patch('app.services.ai_engine.openai.OpenAI')
    def test_review_openai_mock(self, mock_openai):
        """Test OpenAI review with mock"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "openai"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_API_KEY = "test-key"
            
            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='[{"file_path": "test.cpp", "line_number": 1, "severity": "error", "category": "memory", "message": "Leak", "suggestion": "Free"}]'))]
            mock_response.usage = MagicMock(total_tokens=150)
            
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            engine = AIReviewEngine()
            result = engine.review("diff", "test.cpp")
            
            assert result.success is True
            assert result.error_count == 1


class TestReviewLargeDiff:
    def test_review_chunks(self):
        """Test reviewing large diff in chunks"""
        with patch('app.services.ai_engine.settings') as mock_settings:
            mock_settings.AI_PROVIDER = "anthropic"
            mock_settings.CLAUDE_MODEL = "claude-3-opus"
            
            engine = AIReviewEngine()
            
            chunks = [
                {"file_path": "src/file1.cpp", "diff": "diff1"},
                {"file_path": "src/file2.cpp", "diff": "diff2"},
            ]
            
            # Mock the review method
            with patch.object(engine, 'review') as mock_review:
                mock_review.return_value = AIReviewResult(
                    issues=[AIReviewIssue("f.cpp", 1, "warning", "style", "msg", "fix")],
                    total_issues=1, error_count=0, warning_count=1,
                    info_count=0, suggestion_count=0, token_usage=100,
                    model="claude-3-opus", success=True
                )
                
                result = engine.review_large_diff(chunks)
                
                assert result.total_issues == 2  # 2 chunks * 1 issue each
                assert result.token_usage == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])