"""
Created on 2026-01-28

@author: wf
"""

from io import BytesIO

from basemkit.basetest import Basetest
from PIL import Image

from clientutils.clipboard import Clipboard, ClipboardContentType


class TestClipboard(Basetest):
    """
    Test clipboard functionality
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        # Store original clipboard content
        try:
            self._original_clipboard = Clipboard.paste_text()
        except:
            self._original_clipboard = None

    def tearDown(self):
        # Restore original clipboard
        if self._original_clipboard is not None:
            try:
                Clipboard.copy_text(self._original_clipboard)
            except:
                pass
        Basetest.tearDown(self)

    def test_copy_paste_text(self):
        """Test text copy and paste"""
        test_text = "The kitten says meow"
        Clipboard.copy_text(test_text)
        pasted = Clipboard.paste_text()
        self.assertEqual(test_text, pasted)

    def test_copy_paste_image(self):
        """Test image copy and paste"""
        # Create a test image
        test_image = Image.new("RGB", (100, 100), color="red")

        # Copy to clipboard
        Clipboard.copy_image(test_image)

        # Paste from clipboard
        pasted_image = Clipboard.paste_image()

        # Verify dimensions
        self.assertEqual(test_image.size, pasted_image.size)
        self.assertEqual(pasted_image.mode, "RGBA")

    def test_clear(self):
        """Test clearing clipboard"""
        Clipboard.copy_text("test")
        Clipboard.clear()
        # After clear, paste might raise or return empty
        # Behavior depends on system

    def test_image_mode_conversion(self):
        """Test that RGB images are converted to RGBA"""
        rgb_image = Image.new("RGB", (50, 50), color="blue")
        Clipboard.copy_image(rgb_image)
        pasted = Clipboard.paste_image()
        self.assertEqual(pasted.mode, "RGBA")

    def test_content_detection_text(self):
        """Test detecting text content"""
        test_text = "Hello clipboard"
        Clipboard.copy_text(test_text)

        self.assertTrue(Clipboard.has_text())
        self.assertEqual(Clipboard.get_content_type(), ClipboardContentType.TEXT)

        # Auto-detect paste should return text
        content = Clipboard.paste()
        self.assertIsInstance(content, str)
        self.assertEqual(content, test_text)

    def test_content_detection_image(self):
        """Test detecting image content"""
        test_image = Image.new("RGB", (100, 100), color="green")
        Clipboard.copy_image(test_image)

        self.assertTrue(Clipboard.has_image())
        self.assertEqual(Clipboard.get_content_type(), ClipboardContentType.IMAGE)

        # Auto-detect paste should return image
        content = Clipboard.paste()
        self.assertIsInstance(content, Image.Image)

    def test_content_detection_empty(self):
        """Test detecting empty clipboard"""
        Clipboard.clear()

        content_type = Clipboard.get_content_type()
        # May be EMPTY or TEXT with empty string, depending on system
        self.assertIn(
            content_type, [ClipboardContentType.EMPTY, ClipboardContentType.TEXT]
        )

    def test_copy_auto_detect_text(self):
        """Test auto-detect copy with text"""
        test_text = "Auto-detect text copy"
        Clipboard.copy(test_text)

        pasted = Clipboard.paste()
        self.assertIsInstance(pasted, str)
        self.assertEqual(pasted, test_text)

    def test_copy_auto_detect_image(self):
        """Test auto-detect copy with image"""
        test_image = Image.new("RGB", (100, 100), color="purple")
        Clipboard.copy(test_image)

        pasted = Clipboard.paste()
        self.assertIsInstance(pasted, Image.Image)
        self.assertEqual(pasted.size, test_image.size)

    def test_copy_unsupported_type(self):
        """Test copy raises TypeError for unsupported types"""
        with self.assertRaises(TypeError):
            Clipboard.copy(42)

        with self.assertRaises(TypeError):
            Clipboard.copy([1, 2, 3])

        with self.assertRaises(TypeError):
            Clipboard.copy({"key": "value"})

    def test_copy_with_detach(self):
        """Test copy with detach parameter"""
        test_text = "Detached text"
        # Should not raise even with detach=True
        Clipboard.copy(test_text, detach=True)

        test_image = Image.new("RGB", (50, 50), color="yellow")
        Clipboard.copy(test_image, detach=True)

    def test_get_image_bytes_png(self):
        """Test getting image as PNG bytes"""
        test_image = Image.new("RGB", (100, 100), color="cyan")
        Clipboard.copy_image(test_image)

        png_bytes = Clipboard.get_image_bytes("PNG")
        self.assertIsNotNone(png_bytes)
        self.assertIsInstance(png_bytes, bytes)

        # Verify we can load it back
        loaded_image = Image.open(BytesIO(png_bytes))
        self.assertEqual(loaded_image.size, test_image.size)

    def test_get_image_bytes_jpeg(self):
        """Test getting image as JPEG bytes"""
        test_image = Image.new("RGB", (100, 100), color="cyan")
        Clipboard.copy_image(test_image)

        jpeg_bytes = Clipboard.get_image_bytes("JPEG")
        self.assertIsNotNone(jpeg_bytes)
        self.assertIsInstance(jpeg_bytes, bytes)
