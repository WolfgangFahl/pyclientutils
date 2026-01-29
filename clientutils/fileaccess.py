"""
2026-01-28

File access resource for serving file information and downloads.

Provides REST endpoints for:
- File information display (HTML templates)
- File downloads
- Opening files in desktop applications
- Browsing file directories
"""

from datetime import datetime
import logging
import mimetypes
from pathlib import Path
import platform
import subprocess
from typing import Any, Dict, Optional

from fastapi import HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, Response

from clientutils.pathmapping import PathMapping


logger = logging.getLogger(__name__)


class FileAccessResource:
    """Handles file access operations via REST endpoints"""

    @staticmethod
    def _render_default_info(
        fileinfo: Dict[str, Any],
        baseurl: str,
        openiconName: str,
        downloadlink: str,
        browselink: str,
        openlink: str,
        noheader: bool,
    ) -> str:
        """Render default info template using f-strings."""

        icon_html = (
            f'<img src="{baseurl}fileicon/{openiconName}" class="icon" alt="icon">'
        )

        table_content = f"""
        <table class="info-table">
            <tr>
                <td>Name:</td>
                <td>{icon_html}{fileinfo['name']}</td>
            </tr>
            <tr>
                <td>Path:</td>
                <td>{fileinfo['path']}</td>
            </tr>
            <tr>
                <td>Size:</td>
                <td>{fileinfo['size_formatted']}</td>
            </tr>
            <tr>
                <td>Modified:</td>
                <td>{fileinfo['modified']}</td>
            </tr>
            <tr>
                <td>Type:</td>
                <td>{fileinfo['type']}</td>
            </tr>
        </table>

        <div class="actions">
            <h3>Actions:</h3>
            <a href="{downloadlink}" class="btn">Download</a>
            <a href="{browselink}" class="btn">Browse Folder</a>
            <a href="{openlink}" class="btn">Open File</a>
        </div>
        """

        if noheader:
            return table_content

        return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>File Info: {fileinfo['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .header {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .info-table td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            .info-table td:first-child {{ font-weight: bold; width: 200px; }}
            .actions {{ margin-top: 20px; }}
            .btn {{ display: inline-block; padding: 10px 20px; margin: 5px;
                   background: #007bff; color: white; text-decoration: none;
                   border-radius: 3px; }}
            .btn:hover {{ background: #0056b3; }}
            .icon {{ width: 32px; height: 32px; vertical-align: middle; margin-right: 10px; }}
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <h1>File Information</h1>
        </div>
        {table_content}
    </div>
    </body>
    </html>
    """

    @staticmethod
    def _render_short_info(
        fileinfo: Dict[str, Any], downloadlink: str, browselink: str, openlink: str
    ) -> str:
        """Render short info template using f-strings."""
        return f"""
    <div style="padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: #f9f9f9;">
        <strong>{fileinfo['name']}</strong><br>
        Size: {fileinfo['size_formatted']}<br>
        <a href="{downloadlink}">Download</a> |
        <a href="{browselink}">Browse</a> |
        <a href="{openlink}">Open</a>
    </div>
    """

    CLOSE_TAB_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>File Opened</title>
</head>
<body onload="window.close();">
    <p>File opened. This window will close automatically.</p>
    <script>
        setTimeout(function() {
            window.close();
        }, 1000);
    </script>
</body>
</html>
"""

    def __init__(self, base_url: str, path_mapping: Optional[PathMapping] = None):
        """
        construct file access resource.

        Args:
            base_url: Base URL for the server
            path_mapping: Optional path mapping configuration for translating
                logical paths to OS paths. If provided, will be used to map
                requested paths before resolving them to the filesystem.
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.path_mapping = path_mapping
        # Initialize mimetypes
        mimetypes.init()

    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get file information as a dictionary.

        Args:
            filepath: Path to the file

        Returns:
            Dictionary with file information

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(filepath).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        stat = file_path.stat()

        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "size_formatted": self._format_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "type": "Directory" if file_path.is_dir() else "File",
            "extension": (
                file_path.suffix.lstrip(".").lower() if file_path.is_file() else ""
            ),
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
        }

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def get_icon_name(self, file_path: Path) -> str:
        """
        Get icon name for the given file or folder.

        Args:
            file_path: Path object

        Returns:
            Icon filename
        """
        if file_path.is_dir():
            return "folder32x32.png"

        ext = file_path.suffix.lstrip(".").lower()
        return f"{ext}32x32.png" if ext else "file32x32.png"

    def get_action_link(self, filename: str, action: str) -> str:
        """
        Generate action link for a file.

        Args:
            filename: File path
            action: Action type (info, download, open, browse)

        Returns:
            URL for the action
        """
        from urllib.parse import urlencode

        params = urlencode({"filename": filename, "action": action})
        return f"{self.base_url}file?{params}"

    def render_info(
        self,
        fileinfo: Dict[str, Any],
        template_name: str = "defaultinfo",
        noheader: bool = False,
    ) -> str:
        """
        Render file info as HTML.

        Args:
            fileinfo: File information dictionary
            template_name: Template to use (defaultinfo or shortinfo)
            noheader: Whether to omit header

        Returns:
            Rendered HTML
        """
        file_path = Path(fileinfo["path"])

        # Prepare common context
        baseurl = self.base_url
        openiconName = self.get_icon_name(file_path)
        downloadlink = self.get_action_link(fileinfo["path"], "download")
        browselink = self.get_action_link(fileinfo["path"], "browse")
        openlink = self.get_action_link(fileinfo["path"], "open")

        if template_name == "shortinfo":
            return self._render_short_info(fileinfo, downloadlink, browselink, openlink)
        else:
            return self._render_default_info(
                fileinfo,
                baseurl,
                openiconName,
                downloadlink,
                browselink,
                openlink,
                noheader,
            )

    def open_file_in_desktop(self, file_path: Path, open_parent: bool = False) -> bool:
        """
        Open file or directory in the desktop's default application.

        Args:
            file_path: Path to file or directory
            open_parent: If True, open parent directory instead

        Returns:
            True if successful

        Raises:
            RuntimeError: If operation fails
        """
        target = file_path.parent if open_parent else file_path

        if not target.exists():
            raise FileNotFoundError(f"Path not found: {target}")

        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(target)], check=True)
            elif system == "Windows":
                subprocess.run(["explorer", str(target)], check=True)
            else:  # Linux and others
                subprocess.run(["xdg-open", str(target)], check=True)
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to open file: {e}")

    def handle_file_access(
        self, filename: str, action: str = "info", noheader: bool = True
    ) -> Response:
        """
        Main handler for file access requests.

        Args:
            filename: Path to the file
            action: Action to perform (info, shortinfo, open, browse, download)
            noheader: Whether to omit header in HTML responses

        Returns:
            FastAPI Response object

        Raises:
            HTTPException: For various error conditions
        """
        try:
            # Translate path if mapping exists
            if self.path_mapping:
                filename = self.path_mapping.translate(filename)

            file_path = Path(filename).resolve()

            # Check file exists
            if not file_path.exists():
                raise HTTPException(status_code=204, detail="File not found")

            # Handle different actions
            if action == "info":
                fileinfo = self.get_file_info(str(file_path))
                html = self.render_info(fileinfo, "defaultinfo", noheader)
                return HTMLResponse(content=html)

            elif action == "shortinfo":
                fileinfo = self.get_file_info(str(file_path))
                html = self.render_info(fileinfo, "shortinfo", noheader)
                return HTMLResponse(content=html)

            elif action == "download":
                if not file_path.is_file():
                    raise HTTPException(
                        status_code=400, detail="Cannot download directory"
                    )

                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type is None:
                    mime_type = "application/octet-stream"

                return FileResponse(
                    path=str(file_path),
                    media_type=mime_type,
                    filename=file_path.name,
                    headers={
                        "Content-Disposition": f'attachment; filename="{file_path.name}"',
                    },
                )

            elif action == "open":
                try:
                    self.open_file_in_desktop(file_path, open_parent=False)
                    return HTMLResponse(content=self.CLOSE_TAB_HTML)
                except RuntimeError as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Server may be running in headless mode or file opening failed: {e}",
                    )

            elif action == "browse":
                try:
                    self.open_file_in_desktop(file_path, open_parent=True)
                    return HTMLResponse(content=self.CLOSE_TAB_HTML)
                except RuntimeError as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Server may be running in headless mode or directory browsing failed: {e}",
                    )

            else:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling file access: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


def add_file_routes(app, file_resource: FileAccessResource):
    """
    Add file access routes to FastAPI application.

    Args:
        app: FastAPI application instance
        file_resource: FileAccessResource instance
    """

    @app.get(
        "/file",
        responses={
            200: {"description": "File information or download"},
            204: {"description": "File not found"},
            400: {"description": "Invalid request"},
            404: {"description": "File not found"},
            500: {"description": "Server error"},
        },
        tags=["file"],
    )
    def access_file(
        filename: str = Query(..., description="Path to the file"),
        action: str = Query(
            default="info",
            description="Action to perform",
            pattern="^(info|shortinfo|open|browse|download)$",
        ),
        noheader: bool = Query(default=True, description="Omit HTML header"),
    ):
        """
        Access a file with various actions.

        - **info**: Display detailed file information
        - **shortinfo**: Display brief file information
        - **open**: Open file in default application
        - **browse**: Open file's parent directory
        - **download**: Download the file
        """
        return file_resource.handle_file_access(filename, action, noheader)
