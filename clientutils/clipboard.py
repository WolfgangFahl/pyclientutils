"""
Clipboard handling with content detection
"""

from enum import Enum
from io import BytesIO
from typing import Optional, Union

import copykitten
from PIL import Image


class ClipboardContentType(Enum):
    """Types of content that can be in clipboard"""

    TEXT = "text"
    IMAGE = "image"
    EMPTY = "empty"


class Clipboard:
    """
    Clipboard module with content detection
    """

    @staticmethod
    def get_content_type() -> ClipboardContentType:
        """
        Detect what type of content is in clipboard
        Note: This attempts to paste to detect type
        """
        # Try image first (usually more specific)
        if Clipboard.has_image():
            return ClipboardContentType.IMAGE

        # Try text
        if Clipboard.has_text():
            return ClipboardContentType.TEXT

        return ClipboardContentType.EMPTY

    @staticmethod
    def convert_image(img, img_format: str) -> Image.Image:
        """
        Convert image mode if necessary for the target format

        Args:
            img: PIL Image to convert
            img_format: Target format (e.g., 'PNG', 'JPEG')

        Returns:
            Converted PIL Image
        """
        if img_format.upper() == "JPEG":
            # JPEG doesn't support transparency
            if img.mode in ("RGBA", "LA", "P"):
                # Convert to RGB with white background
                # This is simpler and more reliable
                rgb_image = Image.new("RGB", img.size, (255, 255, 255))
                rgb_image.paste(img, (0, 0), img if img.mode in ("RGBA", "LA") else None)
                return rgb_image
            elif img.mode != "RGB":
                return img.convert("RGB")
        return img


    @staticmethod
    def get_image_bytes(img_format: str = "PNG") -> Optional[bytes]:
        """
        Get clipboard image content as bytes in the given format

        Args:
            img_format: Image format (e.g., 'PNG', 'JPEG'). Defaults to 'PNG'

        Returns:
            Image bytes if clipboard contains image, None otherwise
        """
        try:
            img = Clipboard.paste_image()
            if img is None:
                return None

            if isinstance(img, Image.Image):
                img=Clipboard.convert_image(img,img_format);
                buffer = BytesIO()
                img.save(buffer, format=img_format)
                buffer.seek(0)
                return buffer.getvalue()
        except Exception:
            pass
        return None

    @staticmethod
    def has_text() -> bool:
        """Check if clipboard contains text"""
        try:
            text = copykitten.paste()
            return bool(text)
        except:
            return False

    @staticmethod
    def has_image() -> bool:
        """Check if clipboard contains image"""
        try:
            copykitten.paste_image()
            return True
        except:
            return False

    @staticmethod
    def paste() -> Union[str, Image.Image, None]:
        """
        Auto-detect and paste content from clipboard
        Returns:
            str: if clipboard contains text
            Image.Image: if clipboard contains image
            None: if clipboard is empty
        """
        content_type = Clipboard.get_content_type()

        if content_type == ClipboardContentType.IMAGE:
            return Clipboard.paste_image()
        elif content_type == ClipboardContentType.TEXT:
            return Clipboard.paste_text()
        else:
            return None

    @staticmethod
    def copy(content: Union[str, Image.Image], detach: bool = False):
        """
        Auto-detect and copy content to clipboard

        Args:
            content: Either a string or PIL Image
            detach: Whether to detach from clipboard after copy

        Raises:
            TypeError: If content is not str or Image.Image
        """
        if isinstance(content, str):
            Clipboard.copy_text(content, detach=detach)
        elif isinstance(content, Image.Image):
            Clipboard.copy_image(content, detach=detach)
        else:
            raise TypeError(f"Unsupported content type: {type(content)}")

    @staticmethod
    def copy_text(text: str, detach: bool = False):
        """Copy text to clipboard"""
        copykitten.copy(text, detach=detach)

    @staticmethod
    def paste_text() -> str:
        """Paste text from clipboard"""
        return copykitten.paste()

    @staticmethod
    def copy_image(image: Image.Image, detach: bool = False):
        """Copy PIL Image to clipboard"""
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        pixels = image.tobytes()
        copykitten.copy_image(pixels, image.width, image.height, detach=detach)

    @staticmethod
    def paste_image() -> Image.Image:
        """Paste image from clipboard as PIL Image"""
        pixels, width, height = copykitten.paste_image()
        return Image.frombytes(mode="RGBA", size=(width, height), data=pixels)

    @staticmethod
    def clear():
        """Clear clipboard"""
        copykitten.clear()
