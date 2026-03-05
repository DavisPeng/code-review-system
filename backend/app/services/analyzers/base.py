"""
Static Analyzer Base Class
Abstract interface for static code analysis tools
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class Severity(Enum):
    """Issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(Enum):
    """Issue categories"""
    CODING_STANDARD = "coding_standard"
    MEMORY_SAFETY = "memory_safety"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CORRECTNESS = "correctness"
    STYLE = "style"


@dataclass
class AnalysisIssue:
    """Represents a single analysis issue"""
    file_path: str
    line_number: int
    severity: str
    category: str
    message: str
    suggestion: Optional[str] = None
    tool: str = ""


@dataclass
class AnalysisResult:
    """Result of static analysis"""
    tool: str
    issues: List[AnalysisIssue]
    total_issues: int
    error_count: int
    warning_count: int
    info_count: int
    success: bool
    error_message: Optional[str] = None


class StaticAnalyzer(ABC):
    """Abstract base class for static analyzers"""
    
    def __init__(self, binary_path: str = None):
        self.binary_path = binary_path
    
    @abstractmethod
    def analyze(self, file_path: str, compile_commands: str = None) -> AnalysisResult:
        """
        Analyze a single file
        
        Args:
            file_path: Path to source file
            compile_commands: Optional compile_commands.json path for clang-based tools
            
        Returns:
            AnalysisResult with found issues
        """
        pass
    
    @abstractmethod
    def analyze_diff(self, changed_files: List[str], compile_commands: str = None) -> AnalysisResult:
        """
        Analyze only changed files (incremental analysis)
        
        Args:
            changed_files: List of file paths that changed
            compile_commands: Optional compile_commands.json path
            
        Returns:
            AnalysisResult with found issues
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the analyzer is installed and available"""
        pass
    
    def _create_result(
        self, 
        tool_name: str, 
        issues: List[AnalysisIssue], 
        success: bool = True, 
        error_message: str = None
    ) -> AnalysisResult:
        """Helper to create AnalysisResult"""
        error_count = sum(1 for i in issues if i.severity == Severity.ERROR.value)
        warning_count = sum(1 for i in issues if i.severity == Severity.WARNING.value)
        info_count = sum(1 for i in issues if i.severity == Severity.INFO.value)
        
        return AnalysisResult(
            tool=tool_name,
            issues=issues,
            total_issues=len(issues),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            success=success,
            error_message=error_message
        )