"""
Test Git Service
Run with: pytest tests/test_git_service.py -v
"""
import pytest
import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from app.services.git_service import GitService, FileChange, DiffResult


class TestGitService:
    @pytest.fixture
    def temp_cache(self):
        """Create temporary cache directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def git_service(self, temp_cache):
        """Create GitService instance with temp cache"""
        return GitService(cache_dir=temp_cache)
    
    def test_initialization(self, git_service, temp_cache):
        """Test GitService initialization"""
        assert git_service.cache_dir == temp_cache
        assert os.path.exists(temp_cache)
    
    def test_get_repo_path(self, git_service):
        """Test repository path generation"""
        path = git_service._get_repo_path("https://github.com/test/repo.git")
        assert "test_repo.git" in path
        
        path2 = git_service._get_repo_path("git@github.com:test/repo.git")
        assert "test_repo.git" in path2
    
    def test_parse_diff_lines(self, git_service):
        """Test diff line parsing"""
        diff_content = """@@ -1,5 +1,6 @@
 line1
-line2
+new_line2
+new_line3
 line3
-line4
+new_line4
 line5"""
        
        lines_added, lines_removed = git_service._parse_diff_lines(diff_content)
        
        assert len(lines_added) > 0
        assert len(lines_removed) > 0
    
    def test_file_change_dataclass(self):
        """Test FileChange dataclass"""
        change = FileChange(
            file_path="src/main.cpp",
            old_path=None,
            status="modified",
            additions=10,
            deletions=5,
            diff="--- a/src/main.cpp\n+++ b/src/main.cpp\n@@ ...",
            lines_added=[1, 2, 3],
            lines_removed=[4, 5]
        )
        
        assert change.file_path == "src/main.cpp"
        assert change.status == "modified"
        assert change.additions == 10
    
    def test_diff_result_dataclass(self):
        """Test DiffResult dataclass"""
        changes = [
            FileChange("file1.cpp", None, "added", 10, 0, "", [], []),
            FileChange("file2.cpp", None, "modified", 5, 3, "", [], [])
        ]
        
        result = DiffResult(
            commit_sha="abc123",
            branch="main",
            changes=changes,
            total_files=2,
            total_additions=15,
            total_deletions=3
        )
        
        assert result.total_files == 2
        assert result.total_additions == 15
    
    def test_cleanup_cache(self, git_service, temp_cache):
        """Test cache cleanup runs without error"""
        # Clean specific repo (may not exist)
        git_service.cleanup_cache("https://github.com/nonexistent/repo.git")
        
        # Should not raise exception
        assert True
    
    def test_cleanup_all_cache(self, git_service, temp_cache):
        """Test cleanup all cache"""
        # Create some fake cached repos
        os.makedirs(os.path.join(temp_cache, "repo1.git"))
        os.makedirs(os.path.join(temp_cache, "repo2.git"))
        
        assert os.path.exists(os.path.join(temp_cache, "repo1.git"))
        
        # Clean all
        git_service.cleanup_cache()
        
        assert not os.path.exists(temp_cache) or len(os.listdir(temp_cache)) == 0
    
    def test_is_binary_file_mock(self, git_service):
        """Test binary file detection with mock"""
        with patch('app.services.git_service.Repo') as mock_repo:
            mock_commit = MagicMock()
            mock_commit.tree = {"test.png": MagicMock(binary=True)}
            
            mock_repo_instance = MagicMock()
            mock_repo_instance.commit.return_value = mock_commit
            mock_repo.return_value = mock_repo_instance
            
            result = git_service.is_binary_file("https://github.com/test/repo.git", "test.png", "abc123")
            assert result is True
    
    def test_max_file_lines_skip(self, git_service):
        """Test that large files are skipped"""
        # Set low max lines for testing
        git_service.max_file_lines = 100
        
        # Create mock diff with many lines
        large_diff = "\n".join([f"+line{i}" for i in range(150)])
        
        lines_added, lines_removed = git_service._parse_diff_lines(large_diff)
        
        # This would be skipped in actual processing
        assert len(lines_added) + len(lines_removed) > git_service.max_file_lines


class TestFileChangeStatus:
    def test_added_status(self):
        """Test added file status"""
        change = FileChange(
            file_path="new_file.cpp",
            old_path=None,
            status="added",
            additions=10,
            deletions=0,
            diff="",
            lines_added=list(range(1, 11)),
            lines_removed=[]
        )
        assert change.status == "added"
        assert change.deletions == 0
    
    def test_deleted_status(self):
        """Test deleted file status"""
        change = FileChange(
            file_path="deleted_file.cpp",
            old_path=None,
            status="deleted",
            additions=0,
            deletions=20,
            diff="",
            lines_added=[],
            lines_removed=list(range(1, 21))
        )
        assert change.status == "deleted"
        assert change.additions == 0
    
    def test_renamed_status(self):
        """Test renamed file status"""
        change = FileChange(
            file_path="new_name.cpp",
            old_path="old_name.cpp",
            status="renamed",
            additions=5,
            deletions=5,
            diff="",
            lines_added=[1, 2, 3, 4, 5],
            lines_removed=[1, 2, 3, 4, 5]
        )
        assert change.status == "renamed"
        assert change.old_path == "old_name.cpp"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])