"""
Created on 2026-01-29

@author: wf
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from typing import Optional
class Link:
    """
    Link creation helper
    """
    @classmethod
    def create(cls, link: str, title: str, text: str) -> str:
        """Return HTML link markup with target=_blank.

        Args:
            link: URL destination (href attribute)
            title: Tooltip text on hover (title attribute)
            text: Visible clickable text

        Returns:
            HTML anchor tag with specified attributes
        """
        link_markup= f'<a href="{link}" title="{title}" target="_blank">{text}</a>'
        return link_markup

@dataclass
class FileInfo:
    """
    Object-oriented representation of file system information.
    """
    file_path: Path
    filename: Optional[str]=None
    _stat: object = field(init=False, repr=False)
    _exist: bool = field(init=False, repr=False)

    def __post_init__(self):
        """
        Initialize internal state and validate file existence.
        """
        if self.filename is None:
            self.filename=self.file_path.name
        self._exists=self.file_path.exists()
        if not self._exists:
            return

        self._stat = self.file_path.stat()
        # Ensure the exposed path is the resolved string, matching original dictionary behavior
        self.path = str(self.file_path)

    @property
    def name(self) -> str:
        name = self.file_path.name
        return name

    @property
    def size(self) -> int:
        size = self._stat.st_size
        return size

    @property
    def exists(self)->bool:
        return self._exists

    @property
    def size_formatted(self) -> str:
        """
        Return human-readable file size.
        """
        size = self.size
        formatted_size=FileInfo.format_size(size)
        return formatted_size

    @classmethod
    def format_size(cls,size:int)->str:
        formatted_size = ""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                formatted_size = f"{size:.2f} {unit}"
                return formatted_size
            size /= 1024.0
        formatted_size = f"{size:.2f} PB"
        return formatted_size

    @property
    def modified(self) -> str:
        timestamp = self._stat.st_mtime
        modified_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        return modified_str

    @property
    def type(self) -> str:
        file_type = "Directory" if self.file_path.is_dir() else "File"
        return file_type

    @property
    def extension(self) -> str:
        ext = (
            self.file_path.suffix.lstrip(".").lower()
            if self.file_path.is_file()
            else ""
        )
        return ext

    @property
    def is_file(self) -> bool:
        check = self.file_path.is_file()
        return check

    @property
    def is_dir(self) -> bool:
        check = self.file_path.is_dir()
        return check

    def get_action_url(self, base_url: str, action: str) -> str:
        """
        Generate action link for this file.

        Args:
            base_url: Base URL for the server
            action: Action type (info, download, open, browse)

        Returns:
            URL for the action
        """
        params = urlencode({"filename": self.filename, "action": action})  # Use self.path!
        url = f"{base_url}file?{params}"
        return url