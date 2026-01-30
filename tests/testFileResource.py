"""
Created on 2026-01-28

@author: wf
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from basemkit.basetest import Basetest
from fastapi.applications import FastAPI
from fastapi.testclient import TestClient
from clientutils.fileresource import FileAccessResource


class TestFileAccessResourceDesktop(Basetest):
    """Tests for desktop integration features (refactored to reduce duplication)"""

    def setUp(self, debug=True, profile=True):
        """Set up test environment with mocked subprocess"""
        Basetest.setUp(self, debug=debug, profile=profile)

        # Create test environment (same as parent class)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.test_text_file = self.test_dir / "test.txt"
        self.test_text_file.write_text("Hello, World!")
        self.port = 19998
        self.file_resource = FileAccessResource(
            base_url=f"http://localhost:{self.port}/"
        )
        self.app = FastAPI()
        self.file_resource.add_file_routes(self.app)
        self.client = TestClient(self.app)

        # Set up mocking (this is the DRY part)
        self.subprocess_patch = patch(
            "subprocess.run", return_value=MagicMock(returncode=0)
        )
        self.mock_run = self.subprocess_patch.start()

    def tearDown(self):
        """Clean up patches and temp files"""
        self.subprocess_patch.stop()
        self.temp_dir.cleanup()
        Basetest.tearDown(self)

    def _assert_subprocess_called_with_path(self, expected_path):
        """Helper to assert subprocess was called with expected path"""
        self.mock_run.assert_called_once()

        # Get the actual arguments passed to subprocess.run
        args, kwargs = self.mock_run.call_args

        # The command should be the first positional argument (a list like ['explorer', 'path'])
        command = args[0]

        # The path should be the last element in the command list
        actual_path = command[-1] if isinstance(command, list) else str(command)

        # Normalize both paths for comparison to handle any path differences
        expected_path_normalized = str(Path(expected_path).resolve())
        actual_path_normalized = str(Path(actual_path).resolve())

        self.assertEqual(expected_path_normalized, actual_path_normalized)

    @patch("subprocess.run")
    def test_open_file_subprocess_error(self, mock_run):
        """Test handling subprocess error when opening file"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        with self.assertRaises(RuntimeError):
            self.file_resource.open_file_in_desktop(self.test_text_file)

    def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        import concurrent.futures

        def make_request():
            return self.client.get(f"/file?filename={self.test_text_file}&action=info")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All requests should succeed
        for response in results:
            self.assertEqual(response.status_code, 200)

    def test_path_resolution(self):
        """Test that paths are resolved correctly"""
        fileinfo = self.file_resource.get_fileinfo(self.test_text_file)
        # Path should be absolute
        self.assertTrue(Path(fileinfo.path).is_absolute())


    def test_open_file_in_desktop(self):
        """Test opening file in desktop application"""
        result = self.file_resource.open_file_in_desktop(
            self.test_text_file, open_parent=False
        )

        self.assertTrue(result)
        self._assert_subprocess_called_with_path(self.test_text_file)

    def test_open_parent_directory(self):
        """Test opening parent directory"""
        result = self.file_resource.open_file_in_desktop(
            self.test_text_file, open_parent=True
        )

        self.assertTrue(result)
        self._assert_subprocess_called_with_path(self.test_text_file.parent)

    def test_open_nonexistent_file_fails(self):
        """Test opening non-existent file fails"""
        nonexistent = self.test_dir / "nonexistent.txt"

        with self.assertRaises(FileNotFoundError):
            self.file_resource.open_file_in_desktop(nonexistent)


