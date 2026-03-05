"""
Clang-Tidy Static Analyzer
Integrates clang-tidy for C/C++ code analysis
"""
import os
import subprocess
import re
import json
from typing import List, Optional
from .base import StaticAnalyzer, AnalysisIssue, AnalysisResult, Severity


class ClangTidyAnalyzer(StaticAnalyzer):
    """Clang-tidy analyzer implementation"""
    
    def __init__(self, binary_path: str = "clang-tidy"):
        super().__init__(binary_path)
        self.checks = []
    
    def is_available(self) -> bool:
        """Check if clang-tidy is installed"""
        try:
            result = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def set_checks(self, checks: List[str]):
        """Set specific checks to run"""
        self.checks = checks
    
    def analyze(self, file_path: str, compile_commands: str = None) -> AnalysisResult:
        """Analyze a single file with clang-tidy"""
        if not self.is_available():
            return self._create_result(
                "clang-tidy",
                [],
                success=False,
                error_message="clang-tidy not found"
            )
        
        if not os.path.exists(file_path):
            return self._create_result(
                "clang-tidy",
                [],
                success=False,
                error_message=f"File not found: {file_path}"
            )
        
        # Build command
        cmd = [
            self.binary_path,
            file_path,
            "--quiet"  # Only output issues
        ]
        
        # Add specific checks if set
        if self.checks:
            cmd.extend(["-checks=" + ",".join(self.checks)])
        
        # Use compile_commands if provided
        if compile_commands and os.path.exists(compile_commands):
            cmd.extend(["-p", os.path.dirname(compile_commands)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(file_path)
            )
            
            issues = self._parse_output(result.stdout, result.stderr)
            return self._create_result("clang-tidy", issues, success=True)
            
        except subprocess.TimeoutExpired:
            return self._create_result(
                "clang-tidy",
                [],
                success=False,
                error_message="Analysis timeout"
            )
        except Exception as e:
            return self._create_result(
                "clang-tidy",
                [],
                success=False,
                error_message=str(e)
            )
    
    def analyze_diff(self, changed_files: List[str], compile_commands: str = None) -> AnalysisResult:
        """Analyze only changed files"""
        all_issues = []
        
        for file_path in changed_files:
            # Only analyze C/C++ files
            if not file_path.endswith(('.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx')):
                continue
                
            result = self.analyze(file_path, compile_commands)
            all_issues.extend(result.issues)
        
        return self._create_result("clang-tidy", all_issues, success=True)
    
    def _parse_output(self, stdout: str, stderr: str) -> List[AnalysisIssue]:
        """Parse clang-tidy output"""
        issues = []
        combined_output = stdout + "\n" + stderr
        
        # Parse format: /path/to/file:line:column: warning: message [check-name]
        pattern = re.compile(
            r'(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+'
            r'(?P<severity>error|warning|note):\s+'
            r'(?P<message>.+?)(?:\[(?P<check>[^\]]+)\])?\s*$',
            re.MULTILINE
        )
        
        for match in pattern.finditer(combined_output):
            severity = match.group('severity')
            if severity == 'note':
                continue  # Skip notes
            
            # Map severity
            if severity == 'error':
                sev = Severity.ERROR.value
                category = self._categorize_check(match.group('check') or "")
            else:
                sev = Severity.WARNING.value
                category = self._categorize_check(match.group('check') or "")
            
            issues.append(AnalysisIssue(
                file_path=match.group('file'),
                line_number=int(match.group('line')),
                severity=sev,
                category=category,
                message=match.group('message').strip(),
                suggestion=match.group('check'),
                tool="clang-tidy"
            ))
        
        return issues
    
    def _categorize_check(self, check_name: str) -> str:
        """Categorize clang-tidy check"""
        check_lower = check_name.lower()
        
        if any(x in check_lower for x in ['memory', 'malloc', 'new', 'delete', 'pointer', 'unique', 'shared']):
            return "memory_safety"
        elif any(x in check_lower for x in ['performance', 'efficiency', 'optimize']):
            return "performance"
        elif any(x in check_lower for x in ['security', 'insecure', 'buffer']):
            return "security"
        elif any(x in check_lower for x in ['readability', 'style', 'modernize', 'misc']):
            return "coding_standard"
        else:
            return "correctness"


# Singleton instance
clang_tidy_analyzer = ClangTidyAnalyzer()