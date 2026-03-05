"""
Git Service - Extract code changes from git repositories
"""
import os
import re
import shutil
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from git import Repo, GitCommandError
from app.config import settings


@dataclass
class FileChange:
    """Represents a single file change"""
    file_path: str
    old_path: Optional[str]  # For renamed files
    status: str  # added, modified, deleted, renamed
    additions: int
    deletions: int
    diff: str
    lines_added: List[int]
    lines_removed: List[int]


@dataclass
class DiffResult:
    """Result of git diff extraction"""
    commit_sha: str
    branch: str
    changes: List[FileChange]
    total_files: int
    total_additions: int
    total_deletions: int


class GitService:
    """Service for extracting git diffs"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or settings.GIT_CACHE_DIR
        self.max_file_lines = settings.GIT_MAX_FILE_LINES
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_repo_path(self, repo_url: str) -> str:
        """Get local cache path for a repository"""
        # Create a safe folder name from URL
        safe_name = repo_url.replace("/", "_").replace(":", "_")
        return os.path.join(self.cache_dir, safe_name)
    
    def clone_or_pull(self, repo_url: str) -> str:
        """Clone repository if not exists, otherwise pull latest"""
        repo_path = self._get_repo_path(repo_url)
        
        if os.path.exists(repo_path):
            # Pull latest changes
            try:
                repo = Repo(repo_path)
                origin = repo.remotes.origin
                origin.pull()
                return repo_path
            except GitCommandError as e:
                # If pull fails, remove and re-clone
                print(f"Pull failed, re-cloning: {e}")
                shutil.rmtree(repo_path)
        
        # Clone repository
        Repo.clone_from(repo_url, repo_path)
        return repo_path
    
    def extract_diff(self, repo_url: str, commit_sha: str, base_commit: str = None) -> DiffResult:
        """Extract diff for a specific commit"""
        repo_path = self.clone_or_pull(repo_url)
        repo = Repo(repo_path)
        
        # Get commit
        try:
            commit = repo.commit(commit_sha)
        except ValueError:
            raise ValueError(f"Commit {commit_sha} not found")
        
        # Get parent commit for diff
        if base_commit:
            base = repo.commit(base_commit)
        elif commit.parents:
            base = commit.parents[0]
        else:
            # First commit - compare with empty tree
            base = None
        
        # Get diff
        if base:
            diff = commit.diff(base)
        else:
            diff = commit.diff(None)  # Compare with empty tree
        
        changes = []
        total_additions = 0
        total_deletions = 0
        
        for item in diff:
            # Skip binary files
            if item.b_blob or item.a_blob:
                # Check if binary
                if (item.b_blob and item.b_blob.data_stream.read(8000)) or \
                   (item.a_blob and item.a_blob.data_stream.read(8000)):
                    continue
            
            # Get status
            if item.new_file:
                status = "added"
            elif item.deleted_file:
                status = "deleted"
            elif item.renamed:
                status = "renamed"
            else:
                status = "modified"
            
            # Get diff content
            try:
                diff_content = item.diff.decode('utf-8', errors='ignore') if isinstance(item.diff, bytes) else item.diff
            except:
                diff_content = ""
            
            # Parse diff to get line numbers
            lines_added, lines_removed = self._parse_diff_lines(diff_content)
            
            # Skip files that are too large
            total_lines = len(lines_added) + len(lines_removed)
            if total_lines > self.max_file_lines:
                print(f"Skipping {item.a_path}: too large ({total_lines} lines)")
                continue
            
            file_change = FileChange(
                file_path=item.a_path or item.b_path,
                old_path=item.a_path if item.renamed else None,
                status=status,
                additions=len(lines_added),
                deletions=len(lines_removed),
                diff=diff_content,
                lines_added=lines_added,
                lines_removed=lines_removed
            )
            
            changes.append(file_change)
            total_additions += len(lines_added)
            total_deletions += len(lines_removed)
        
        # Get branch name
        branch = ""
        try:
            branch = repo.active_branch.name
        except:
            pass
        
        return DiffResult(
            commit_sha=commit_sha,
            branch=branch,
            changes=changes,
            total_files=len(changes),
            total_additions=total_additions,
            total_deletions=total_deletions
        )
    
    def _parse_diff_lines(self, diff_content: str) -> tuple:
        """Parse diff content to extract added and removed line numbers"""
        lines_added = []
        lines_removed = []
        
        # Parse unified diff format
        # @@ -old_start,old_count +new_start,new_count @@
        hunk_pattern = re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
        
        old_start = 0
        new_start = 0
        
        for line in diff_content.split('\n'):
            hunk_match = hunk_pattern.search(line)
            if hunk_match:
                # Get starting line numbers
                old_start = int(hunk_match.group(1))
                new_start = int(hunk_match.group(3))
                continue
            
            # Count additions and deletions
            if line.startswith('+') and not line.startswith('+++'):
                if new_start > 0:
                    lines_added.append(new_start)
                new_start += 1
            elif line.startswith('-') and not line.startswith('---'):
                if old_start > 0:
                    lines_removed.append(old_start)
                old_start += 1
        
        return lines_added, lines_removed
    
    def get_commit_info(self, repo_url: str, commit_sha: str) -> Dict[str, Any]:
        """Get detailed commit information"""
        repo_path = self.clone_or_pull(repo_url)
        repo = Repo(repo_path)
        
        try:
            commit = repo.commit(commit_sha)
        except ValueError:
            raise ValueError(f"Commit {commit_sha} not found")
        
        return {
            "sha": commit.hexsha,
            "short_sha": commit.hexsha[:7],
            "message": commit.message,
            "author": str(commit.author),
            "author_email": commit.author.email,
            "committed_date": commit.committed_date,
            "parents": [p.hexsha for p in commit.parents]
        }
    
    def is_binary_file(self, repo_url: str, file_path: str, commit_sha: str) -> bool:
        """Check if a file is binary"""
        repo_path = self.clone_or_pull(repo_url)
        repo = Repo(repo_path)
        
        try:
            commit = repo.commit(commit_sha)
            blob = commit.tree[file_path]
            return blob.binary
        except:
            return False
    
    def cleanup_cache(self, repo_url: str = None):
        """Clean up cached repositories"""
        if repo_url:
            repo_path = self._get_repo_path(repo_url)
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
        else:
            # Clean all cached repos
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir)


# Singleton instance
git_service = GitService()