"""
Created on 2026-01-28

@author: wf
"""

from basemkit.basetest import Basetest

from clientutils.webserver import ClientUtilsServer


class TestIcons(Basetest):
    """
    Test accessing icons
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.server = ClientUtilsServer()
        self.client = self.server.app.test_client()

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
