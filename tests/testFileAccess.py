"""
Created on 2026-01-28

@author: wf
"""

from pathlib import Path
import tempfile

from basemkit.basetest import Basetest
from clientutils.fileaccess import FileAccess
from fastapi import FastAPI
from fastapi.testclient import TestClient

from clientutils.fileresource import FileAccessResource


class TestFileAccess(Basetest):
    """
    Test file access functionality
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

        # Create temporary directory and test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

        # Create test files
        self.test_text_file = self.test_dir / "test.txt"
        self.test_text_file.write_text("Hello, World!")

        self.test_pdf_file = self.test_dir / "document.pdf"
        self.test_pdf_file.write_bytes(b"PDF content here")

        self.test_image_file = self.test_dir / "image.png"
        self.test_image_file.write_bytes(b"PNG content")

        # Create subdirectory
        self.test_subdir = self.test_dir / "subdir"
        self.test_subdir.mkdir()

        self.port = 19998
        self.file_resource = FileAccessResource(
            base_url=f"http://localhost:{self.port}/"
        )
        self.app = FastAPI()
        self.file_resource.add_file_routes(self.app)
        self.client = TestClient(self.app)


    def tearDown(self):
        # Clean up temporary directory
        self.temp_dir.cleanup()
        Basetest.tearDown(self)

    def test_get_file_info(self):
        """Test getting file information"""
        file_info = self.file_resource.get_file_info(str(self.test_text_file))

        self.assertEqual(file_info["name"], "test.txt")
        self.assertTrue(file_info["is_file"])
        self.assertFalse(file_info["is_dir"])
        self.assertEqual(file_info["size"], 13)  # "Hello, World!" is 13 bytes
        self.assertEqual(file_info["extension"], "txt")
        self.assertIn("size_formatted", file_info)
        self.assertIn("modified", file_info)

    def test_get_directory_info(self):
        """Test getting directory information"""
        dir_info = self.file_resource.get_file_info(str(self.test_subdir))

        self.assertEqual(dir_info["name"], "subdir")
        self.assertFalse(dir_info["is_file"])
        self.assertTrue(dir_info["is_dir"])
        self.assertEqual(dir_info["type"], "Directory")

    def test_get_file_info_nonexistent(self):
        """Test getting info for non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.file_resource.get_file_info("/nonexistent/file.txt")

    def test_format_size(self):
        """Test size formatting"""
        test_cases = [
            (0, "0.00 B"),
            (500, "500.00 B"),
            (1024, "1.00 KB"),
            (1024 * 1024, "1.00 MB"),
            (1024 * 1024 * 1024, "1.00 GB"),
            (1024 * 1024 * 1024 * 1024, "1.00 TB"),
        ]

        for size, expected in test_cases:
            result = self.file_resource._format_size(size)
            self.assertEqual(result, expected)

    def test_get_icon_name_directory(self):
        """Test getting icon name for directory"""
        icon = FileAccess.get_icon_name(self.test_subdir)
        self.assertEqual(icon, "folder32x32.png")

    def test_get_icon_name_text_file(self):
        """Test getting icon name for text file"""
        icon = FileAccess.get_icon_name(self.test_text_file)
        self.assertEqual(icon, "txt32x32.png")

    def test_get_icon_name_pdf_file(self):
        """Test getting icon name for PDF file"""
        icon = FileAccess.get_icon_name(self.test_pdf_file)
        self.assertEqual(icon, "pdf32x32.png")

    def test_get_icon_name_no_extension(self):
        """Test getting icon name for file without extension"""
        no_ext_file = self.test_dir / "noext"
        no_ext_file.write_text("content")

        icon = FileAccess.get_icon_name(no_ext_file)
        self.assertEqual(icon, "file32x32.png")

    def test_get_action_link(self):
        """Test generating action links"""
        filename = "/path/to/file.txt"

        # Test info link
        info_link = self.file_resource.get_action_link(filename, "info")
        self.assertIn("filename=%2Fpath%2Fto%2Ffile.txt", info_link)
        self.assertIn("action=info", info_link)

        # Test download link
        download_link = self.file_resource.get_action_link(filename, "download")
        self.assertIn("action=download", download_link)

    def test_render_info_default_template(self):
        """Test rendering file info with default template"""
        file_info = self.file_resource.get_file_info(str(self.test_text_file))
        html = self.file_resource.render_info(file_info, "defaultinfo", noheader=False)

        self.assertIn("test.txt", html)
        self.assertIn("File Information", html)
        self.assertIn("Download", html)
        self.assertIn("Browse Folder", html)
        self.assertIn("Open File", html)

    def test_render_info_short_template(self):
        """Test rendering file info with short template"""
        file_info = self.file_resource.get_file_info(str(self.test_text_file))
        html = self.file_resource.render_info(file_info, "shortinfo", noheader=True)

        self.assertIn("test.txt", html)
        self.assertIn("Download", html)
        # Should be shorter than default
        self.assertLess(len(html), 1000)

    def test_render_info_no_header(self):
        """Test rendering info without header"""
        file_info = self.file_resource.get_file_info(str(self.test_text_file))
        html = self.file_resource.render_info(file_info, "defaultinfo", noheader=True)

        # Should not contain header div
        self.assertNotIn('<div class="header">', html)

    def test_handle_info_action(self):
        """Test handling info action via HTTP"""
        response = self.client.get(f"/file?filename={self.test_text_file}&action=info")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("test.txt", response.text)

    def test_handle_shortinfo_action(self):
        """Test handling shortinfo action via HTTP"""
        response = self.client.get(
            f"/file?filename={self.test_text_file}&action=shortinfo"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("test.txt", response.text)

    def test_handle_download_action(self):
        """Test handling download action via HTTP"""
        response = self.client.get(
            f"/file?filename={self.test_text_file}&action=download"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hello, World!")
        self.assertIn("attachment", response.headers["content-disposition"])
        self.assertIn("test.txt", response.headers["content-disposition"])

    def test_handle_download_directory_fails(self):
        """Test that downloading a directory fails"""
        response = self.client.get(f"/file?filename={self.test_subdir}&action=download")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot download directory", response.text)

    def test_handle_download_mime_type(self):
        """Test correct MIME type for download"""
        response = self.client.get(
            f"/file?filename={self.test_pdf_file}&action=download"
        )

        self.assertEqual(response.status_code, 200)
        # Check content-type header
        content_type = response.headers.get("content-type", "")
        self.assertTrue(
            "pdf" in content_type.lower()
            or "application/octet-stream" in content_type.lower()
        )

    def test_handle_nonexistent_file(self):
        """Test handling request for non-existent file"""
        response = self.client.get("/file?filename=/nonexistent/file.txt&action=info")

        self.assertEqual(response.status_code, 204)

    def test_handle_invalid_action(self):
        """Test handling invalid action"""
        response = self.client.get(
            f"/file?filename={self.test_text_file}&action=invalid"
        )

        self.assertEqual(response.status_code, 422)  # Validation error

    def test_handle_no_filename(self):
        """Test handling request without filename"""
        response = self.client.get("/file?action=info")

        self.assertEqual(response.status_code, 422)  # Validation error

    def test_handle_no_action(self):
        """Test handling request without action (should default to info)"""
        response = self.client.get(f"/file?filename={self.test_text_file}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("test.txt", response.text)

    def test_multiple_file_types(self):
        """Test handling different file types"""
        # Create files with different extensions
        extensions = ["txt", "pdf", "jpg", "png", "doc", "xlsx"]

        for ext in extensions:
            test_file = self.test_dir / f"test.{ext}"
            test_file.write_bytes(b"content")

            file_info = self.file_resource.get_file_info(str(test_file))
            self.assertEqual(file_info["extension"], ext)

            icon = FileAccess.get_icon_name(test_file)
            self.assertEqual(icon, f"{ext}32x32.png")

    def test_large_file_size_formatting(self):
        """Test formatting larger file sizes"""
        # Create a file with measurable size
        large_file = self.test_dir / "large.bin"
        large_file.write_bytes(b"x" * 2048)  # 2KB

        file_info = self.file_resource.get_file_info(str(large_file))
        self.assertIn("KB", file_info["size_formatted"])

    def test_file_with_special_characters(self):
        """Test handling files with special characters in name"""
        special_file = self.test_dir / "test file (copy).txt"
        special_file.write_text("content")

        file_info = self.file_resource.get_file_info(str(special_file))
        self.assertEqual(file_info["name"], "test file (copy).txt")

        response = self.client.get(f"/file?filename={special_file}&action=info")
        self.assertEqual(response.status_code, 200)

    def test_empty_file(self):
        """Test handling empty file"""
        empty_file = self.test_dir / "empty.txt"
        empty_file.write_text("")

        file_info = self.file_resource.get_file_info(str(empty_file))
        self.assertEqual(file_info["size"], 0)
        self.assertEqual(file_info["size_formatted"], "0.00 B")

        response = self.client.get(f"/file?filename={empty_file}&action=download")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

