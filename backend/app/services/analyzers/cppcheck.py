"""
Cppcheck Static Analyzer
Integrates cppcheck for C/C++ code analysis
"""
import os
import subprocess
import re
import json
import xml.etree.ElementTree as ET
from typing import List, Optional
from .base import StaticAnalyzer, AnalysisIssue, AnalysisResult, Severity


class CppcheckAnalyzer(StaticAnalyzer):
    """Cppcheck analyzer implementation"""
    
    def __init__(self, binary_path: str = "cppcheck"):
        super().__init__(binary_path)
        self.enable_checks = ["all"]  # Enable all checks by default
    
    def is_available(self) -> bool:
        """Check if cppcheck is installed"""
        try:
            result = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def set_enable_checks(self, checks: List[str]):
        """Set checks to enable"""
        self.enable_checks = checks
    
    def analyze(self, file_path: str, compile_commands: str = None) -> AnalysisResult:
        """Analyze a single file with cppcheck"""
        if not self.is_available():
            return self._create_result(
                "cppcheck",
                [],
                success=False,
                error_message="cppcheck not found"
            )
        
        if not os.path.exists(file_path):
            return self._create_result(
                "cppcheck",
                [],
                success=False,
                error_message=f"File not found: {file_path}"
            )
        
        # Build command
        cmd = [
            self.binary_path,
            "--enable=" + ",".join(self.enable_checks),
            "--xml",  # Output in XML format
            "--quiet",
            "--template={file}:{line}:{severity}:{message}",
            file_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(file_path) or "."
            )
            
            issues = self._parse_xml_output(result.stdout)
            
            # cppcheck returns 0 even with warnings, non-zero only for errors
            # So we check if there's a critical error
            if result.returncode > 1:  # Serious error
                return self._create_result(
                    "cppcheck",
                    [],
                    success=False,
                    error_message=result.stderr or "Cppcheck execution failed"
                )
            
            return self._create_result("cppcheck", issues, success=True)
            
        except subprocess.TimeoutExpired:
            return self._create_result(
                "cppcheck",
                [],
                success=False,
                error_message="Analysis timeout"
            )
        except Exception as e:
            return self._create_result(
                "cppcheck",
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
        
        return self._create_result("cppcheck", all_issues, success=True)
    
    def _parse_xml_output(self, xml_output: str) -> List[AnalysisIssue]:
        """Parse cppcheck XML output"""
        issues = []
        
        if not xml_output.strip():
            return issues
        
        try:
            root = ET.fromstring(xml_output)
        except ET.ParseError:
            # Try to parse error messages from text output
            return self._parse_text_output(xml_output)
        
        # Find all errors
        for error in root.findall('.//error'):
            severity = error.get('severity', 'warning')
            msg = error.get('msg', '')
            id_code = error.get('id', '')
            
            # Get location
            location = error.find('location')
            if location is None:
                continue
                
            file_path = location.get('file', '')
            line = location.get('line', '0')
            
            try:
                line_number = int(line) if line else 0
            except ValueError:
                line_number = 0
            
            # Map severity
            if severity == 'error':
                sev = Severity.ERROR.value
            elif severity == 'warning':
                sev = Severity.WARNING.value
            elif severity == 'style':
                sev = Severity.INFO.value
            else:
                sev = Severity.INFO.value
            
            # Categorize
            category = self._categorize_error(id_code, msg)
            
            issues.append(AnalysisIssue(
                file_path=file_path,
                line_number=line_number,
                severity=sev,
                category=category,
                message=msg,
                suggestion=id_code,
                tool="cppcheck"
            ))
        
        return issues
    
    def _parse_text_output(self, text_output: str) -> List[AnalysisIssue]:
        """Fallback text parsing"""
        issues = []
        
        # Format: /path/to/file:line: (severity) message
        pattern = re.compile(
            r'(?P<file>[^:]+):(?P<line>\d+):\s*'
            r'\((?P<severity>[^)]+)\)\s*'
            r'(?P<message>.+)'
        )
        
        for match in pattern.finditer(text_output):
            severity = match.group('severity')
            msg = match.group('message')
            id_code = ""
            
            # Extract error ID if present
            id_match = re.search(r'\[([^\]]+)\]', msg)
            if id_match:
                id_code = id_match.group(1)
                msg = re.sub(r'\[([^\]]+)\]', '', msg).strip()
            
            # Map severity
            if severity == 'error':
                sev = Severity.ERROR.value
            else:
                sev = Severity.WARNING.value
            
            issues.append(AnalysisIssue(
                file_path=match.group('file'),
                line_number=int(match.group('line')),
                severity=sev,
                category=self._categorize_error(id_code, msg),
                message=msg,
                suggestion=id_code,
                tool="cppcheck"
            ))
        
        return issues
    
    def _categorize_error(self, error_id: str, message: str) -> str:
        """Categorize cppcheck error"""
        error_lower = (error_id + message).lower()
        
        if any(x in error_lower for x in ['memory', 'leak', 'pointer', 'null', 'alloc', 'free']):
            return "memory_safety"
        elif any(x in error_lower for x in ['performance', 'efficiency', 'slow', 'unnecessary']):
            return "performance"
        elif any(x in error_lower for x in ['security', 'buffer', 'overflow', 'insecure']):
            return "security"
        elif any(x in error_lower for x in ['style', 'readability', ' convention']):
            return "coding_standard"
        else:
            return "correctness"


# Singleton instance
cppcheck_analyzer = CppcheckAnalyzer()