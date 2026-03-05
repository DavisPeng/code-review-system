"""
Test Static Analyzer
Run with: pytest tests/test_static_analyzer.py -v
"""
import pytest
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from app.services.analyzers.base import StaticAnalyzer, AnalysisIssue, AnalysisResult, Severity
from app.services.analyzers.clang_tidy import ClangTidyAnalyzer
from app.services.analyzers.cppcheck import CppcheckAnalyzer


class TestAnalysisIssue:
    def test_create_issue(self):
        """Test creating an analysis issue"""
        issue = AnalysisIssue(
            file_path="src/main.cpp",
            line_number=10,
            severity="error",
            category="memory_safety",
            message="Memory leak detected",
            suggestion="Use smart pointer",
            tool="cppcheck"
        )
        
        assert issue.file_path == "src/main.cpp"
        assert issue.line_number == 10
        assert issue.severity == "error"


class TestAnalysisResult:
    def test_create_result(self):
        """Test creating analysis result"""
        issues = [
            AnalysisIssue("f1.cpp", 1, "error", "memory", "msg1"),
            AnalysisIssue("f1.cpp", 2, "warning", "style", "msg2"),
            AnalysisIssue("f1.cpp", 3, "info", "style", "msg3"),
        ]
        
        result = AnalysisResult(
            tool="test",
            issues=issues,
            total_issues=3,
            error_count=1,
            warning_count=1,
            info_count=1,
            success=True
        )
        
        assert result.total_issues == 3
        assert result.error_count == 1
        assert result.success is True


class TestStaticAnalyzerBase:
    def test_create_result_helper(self):
        """Test base class helper method"""
        class TestAnalyzer(StaticAnalyzer):
            def analyze(self, file_path, compile_commands=None):
                pass
            def analyze_diff(self, changed_files, compile_commands=None):
                pass
            def is_available(self):
                return True
        
        analyzer = TestAnalyzer()
        
        issues = [
            AnalysisIssue("f1.cpp", 1, "error", "memory", "msg1"),
            AnalysisIssue("f1.cpp", 2, "warning", "style", "msg2"),
        ]
        
        result = analyzer._create_result("test", issues, True)
        
        assert result.total_issues == 2
        assert result.error_count == 1
        assert result.warning_count == 1


class TestClangTidyAnalyzer:
    def test_initialization(self):
        """Test ClangTidyAnalyzer initialization"""
        analyzer = ClangTidyAnalyzer()
        assert analyzer.binary_path == "clang-tidy"
    
    def test_custom_binary_path(self):
        """Test custom binary path"""
        analyzer = ClangTidyAnalyzer("/usr/bin/clang-tidy-14")
        assert analyzer.binary_path == "/usr/bin/clang-tidy-14"
    
    def test_set_checks(self):
        """Test setting checks"""
        analyzer = ClangTidyAnalyzer()
        analyzer.set_checks(["readability-*", "modernize-*"])
        assert "readability-*" in analyzer.checks
    
    def test_is_available_mock(self):
        """Test is_available with mock"""
        analyzer = ClangTidyAnalyzer()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert analyzer.is_available() is True
            
            mock_run.return_value = MagicMock(returncode=1)
            assert analyzer.is_available() is False
    
    def test_parse_output(self):
        """Test clang-tidy output parsing"""
        analyzer = ClangTidyAnalyzer()
        
        output = """/path/to/file.cpp:10:5: warning: variable 'x' is uninitialized [clang-analyzer-core.Uninitialized]
/path/to/file.cpp:20:10: error: memory leak [modernize-use-nullptr]
"""
        issues = analyzer._parse_output(output, "")
        
        assert len(issues) == 2
        assert issues[0].severity == "warning"
        assert issues[1].severity == "error"
    
    def test_categorize_check(self):
        """Test check categorization"""
        analyzer = ClangTidyAnalyzer()
        
        assert analyzer._categorize_check("clang-analyzer-core.Memory") == "memory_safety"
        assert analyzer._categorize_check("readability-*)") == "coding_standard"
        assert analyzer._categorize_check("performance-*)") == "performance"
        assert analyzer._categorize_check("security-*)") == "security"


class TestCppcheckAnalyzer:
    def test_initialization(self):
        """Test CppcheckAnalyzer initialization"""
        analyzer = CppcheckAnalyzer()
        assert analyzer.binary_path == "cppcheck"
        assert "all" in analyzer.enable_checks
    
    def test_custom_binary_path(self):
        """Test custom binary path"""
        analyzer = CppcheckAnalyzer("/usr/bin/cppcheck")
        assert analyzer.binary_path == "/usr/bin/cppcheck"
    
    def test_set_enable_checks(self):
        """Test setting enable checks"""
        analyzer = CppcheckAnalyzer()
        analyzer.set_enable_checks(["memory", "style"])
        assert "memory" in analyzer.enable_checks
    
    def test_is_available_mock(self):
        """Test is_available with mock"""
        analyzer = CppcheckAnalyzer()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert analyzer.is_available() is True
    
    def test_parse_xml_output(self):
        """Test XML output parsing"""
        analyzer = CppcheckAnalyzer()
        
        xml = """<?xml version="1.0" ?>
<results version="2">
    <errors>
        <error id="memoryLeak" severity="error" msg="Memory leak">
            <location file="src/main.cpp" line="10"/>
        </error>
        <error id="uninitvar" severity="warning" msg="Uninitialized variable">
            <location file="src/main.cpp" line="20"/>
        </error>
    </errors>
</results>"""
        
        issues = analyzer._parse_xml_output(xml)
        
        assert len(issues) == 2
        assert issues[0].severity == "error"
        assert issues[1].severity == "warning"
    
    def test_categorize_error(self):
        """Test error categorization"""
        analyzer = CppcheckAnalyzer()
        
        assert analyzer._categorize_error("memoryLeak", "Memory leak") == "memory_safety"
        assert analyzer._categorize_error("uninitvar", "Uninitialized variable") == "correctness"
        assert analyzer._categorize_error("performance", "Performance issue") == "performance"


class TestIncrementalAnalysis:
    def test_clang_tidy_incremental(self):
        """Test clang-tidy incremental analysis"""
        analyzer = ClangTidyAnalyzer()
        
        with patch.object(analyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = AnalysisResult(
                tool="clang-tidy", issues=[], total_issues=0,
                error_count=0, warning_count=0, info_count=0, success=True
            )
            
            result = analyzer.analyze_diff(["src/main.cpp", "src/utils.cpp"])
            assert result.tool == "clang-tidy"
            assert mock_analyze.call_count == 2
    
    def test_cppcheck_incremental(self):
        """Test cppcheck incremental analysis"""
        analyzer = CppcheckAnalyzer()
        
        with patch.object(analyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = AnalysisResult(
                tool="cppcheck", issues=[], total_issues=0,
                error_count=0, warning_count=0, info_count=0, success=True
            )
            
            result = analyzer.analyze_diff(["src/main.cpp", "src/test.c"])
            assert result.tool == "cppcheck"
            assert mock_analyze.call_count == 2


class TestNonCppFiles:
    def test_clang_tidy_skips_non_cpp(self):
        """Test clang-tidy skips non-C++ files"""
        analyzer = ClangTidyAnalyzer()
        
        with patch.object(analyzer, 'analyze') as mock_analyze:
            result = analyzer.analyze_diff([
                "src/main.py",  # Skip
                "src/test.js",  # Skip
                "src/main.cpp",  # Analyze
            ])
            
            # Only main.cpp should be analyzed
            assert mock_analyze.call_count == 1
    
    def test_cppcheck_skips_non_cpp(self):
        """Test cppcheck skips non-C++ files"""
        analyzer = CppcheckAnalyzer()
        
        with patch.object(analyzer, 'analyze') as mock_analyze:
            result = analyzer.analyze_diff([
                "src/main.py",
                "src/test.js",
                "src/main.cpp",
            ])
            
            assert mock_analyze.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])