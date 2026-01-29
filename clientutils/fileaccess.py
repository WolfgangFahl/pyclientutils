"""
2026-01-28

File access resource for serving file information and downloads.

Provides REST endpoints for:
- File information display (HTML templates)
- File downloads
- Opening files in desktop applications
- Browsing file directories
"""
from importlib.resources import files, as_file
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
            icons_trav = files("clientutils_examples").joinpath("icons")
            # Convert to concrete Path - this works if icons is a real directory in the package
            icons_dir = Path(str(icons_trav))
            if icons_dir.exists():
                return icons_dir
        except (ModuleNotFoundError, FileNotFoundError, TypeError):
            pass

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




