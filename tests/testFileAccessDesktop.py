"""
Created on 2026-01-28

@author: wf
"""
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from basemkit.basetest import Basetest
from fastapi.applications import FastAPI

from clientutils.fileaccess import FileAccessResource, add_file_routes


class TestFileAccessDesktopIntegration(Basetest):
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
        add_file_routes(self.app, self.file_resource)
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
        call_args = str(self.mock_run.call_args)
        self.assertIn(str(expected_path), call_args)

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

    def test_handle_open_action(self):
        """Test handling open action via HTTP"""
        response = self.client.get(f"/file?filename={self.test_text_file}&action=open")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("window.close", response.text)

    def test_handle_browse_action(self):
        """Test handling browse action via HTTP"""
        response = self.client.get(
            f"/file?filename={self.test_text_file}&action=browse"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("window.close", response.text)

    def test_open_file_subprocess_error(self):
        """Test handling subprocess error when opening file"""
        self.mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        with self.assertRaises(RuntimeError):
            self.file_resource.open_file_in_desktop(self.test_text_file)
