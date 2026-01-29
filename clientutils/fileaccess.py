"""
2026-01-28

File access resource for serving file information and downloads.

Provides REST endpoints for:
- File information display (HTML templates)
- File downloads
- Opening files in desktop applications
- Browsing file directories
"""
import importlib.resources
from pathlib import Path

class FileAccess:
    """
    File Access
    """

    @classmethod
    def get_icons_directory(cls) -> Path:
        """
        Get the path to the icons directory.
    
        Returns:
            Path: Absolute path to the icons directory
    
        Raises:
            FileNotFoundError: If icons directory doesn't exist
        """
        try:
            # Use importlib.resources for packaged distributions
            with importlib.resources.path('clientutils_examples', 'icons') as icons_path:
                icons_dir = Path(icons_path)
        except (ModuleNotFoundError, FileNotFoundError):
            # Fallback for development
            icons_dir = Path(__file__).parent.parent / "clientutils_examples" / "icons"
        
        if not icons_dir.exists():
            raise FileNotFoundError(f"Icons directory not found at {icons_dir}")
        
        return icons_dir
    
    @classmethod
    def get_icon_name(cls, file_path: Path) -> str:
        """
        Get icon name for the given file or folder.

        Args:
            file_path: Path object

        Returns:
            Icon filename
        """
        icon_name=None
        if file_path.is_dir():
            icon_name="folder32x32.png"
        else:
            ext = file_path.suffix.lstrip(".").lower()
            icon_name=f"{ext}32x32.png" if ext else "file32x32.png"
        return icon_name




