"""
Created on 2026-01-28

@author: wf
"""

import os
from io import BytesIO

from basemkit.basetest import Basetest
from fastapi.testclient import TestClient
from PIL import Image

from clientutils.clipboard import Clipboard
from clientutils.webserver import ClientUtilsServer


class TestClientUtilsServer(Basetest):
    """
    Test accessing icons
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.server = ClientUtilsServer()
        # Use FastAPI's TestClient instead of Flask's test_client()
        self.client = TestClient(self.server.app)
        # Store original clipboard content
        try:
            self._original_clipboard = Clipboard.paste()
        except:
            self._original_clipboard = None
        icon_dir = self.server.get_icons_directory()
        test_image_path = f"{icon_dir}/xls32x32.png"
        self.assertTrue(os.path.isfile(test_image_path))
        # Load as PIL Image first and copy to clipboard
        test_image = Image.open(test_image_path)

        Clipboard.copy(test_image)

    def tearDown(self):
        # Restore original clipboard
        if self._original_clipboard is not None:
            try:
                Clipboard.copy(self._original_clipboard)
            except:
                pass
        Basetest.tearDown(self)

    def expected_icons(self):
        """Generator yielding full expected icon names"""
        for ext in ["jpg", "mp4", "xls"]:
            yield f"{ext}32x32.png"

    def test_get_icons_directory(self):
        """Test the get_icons_directory method"""
        icons_dir = self.server.get_icons_directory()
        self.assertTrue(icons_dir.exists())
        self.assertTrue(icons_dir.is_dir())
        # Check for expected icon files
        for icon_name in self.expected_icons():
            icon_path = icons_dir / icon_name
            self.assertTrue(icon_path.exists(), f"Missing icon: {icon_name}")

    def test_icons(self):
        """
        Test accessing icons via static REST call
        """
        for icon in self.expected_icons():
            response = self.client.get(f"/fileicon/{icon}")
            self.assertEqual(response.status_code, 200)

    def test_clipboard_endpoint(self):
        """Test clipboard REST endpoint"""
        response = self.client.get("/clipboard")
        self.assertIn(response.status_code, [200])
        # FastAPI uses response.headers for content-type
        self.assertEqual(response.headers["content-type"], "image/png")
        # Retrieve and verify the image content
        # FastAPI uses .content instead of .data
        image_data = BytesIO(response.content)
        image = Image.open(image_data)

        # Check size
        self.assertEqual(image.size, (32, 32), "Image should be 32x32 pixels")

        # Check format
        self.assertEqual(image.format, "PNG", "Image should be PNG format")

        # Check mode (optional - typically "RGBA" or "RGB")
        self.assertIn(image.mode, ["RGB", "RGBA"], "Image should be RGB or RGBA")
