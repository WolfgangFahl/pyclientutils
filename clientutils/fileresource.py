"""
Created on 2026-01-29

@author: wf
"""
import logging
import mimetypes
from pathlib import Path
import platform
import subprocess
from typing import Optional

from clientutils.fileaccess import FileAccess
from clientutils.fileinfo import FileInfo
from clientutils.pathmapping import PathMapping
from fastapi import HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, Response


logger = logging.getLogger(__name__)


class FileAccessResource:
    """Handles file access operations via REST endpoints"""

    def __init__(self, base_url: str, path_mapping: Optional[PathMapping] = None):
        """
        Construct file access resource.

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

    def render_short_info(self) -> str:
        """
        Render short info template matching original FreeMarker template.
        """
        def icon(name: str, alt: str = None, title: str = None) -> str:
            """Icon macro equivalent"""
            alt = alt or name
            title = title or name
            return f"<img src='{self.base_url}fileicon/{name}' alt='{alt}' title='{title}'/>"
        fileinfo=self.fileinfo
        # Generate action links from fileinfo
        downloadlink = fileinfo.get_action_link(self.base_url, "download")
        browselink = fileinfo.get_action_link(self.base_url, "browse")
        openlink = fileinfo.get_action_link(self.base_url, "open")
        openiconName = FileAccess.get_icon_name(fileinfo.file_path)

        # Get parent folder path
        folder_path = str(Path(fileinfo.path).parent)

        # Check if file exists
        if not Path(fileinfo.path).exists():
            content = f"<span style=\"color: #ff0000;\" title='{fileinfo.path} does not exist'>{icon('document_error.png')}{fileinfo.path}</span>"
        else:
            # Action links for files only
            action_links = ""
            if fileinfo.is_file:
                action_links = f"""
          <td>
              <a href="{downloadlink}" title="download {fileinfo.path}" target="_blank">{icon('document_down.png')}</a>
              <a href="{browselink}"   title="browse {fileinfo.path}" target="_blank">{icon('folder_view.png')}</a>
          </td>"""

            content = f"""<table>
        <tr>
          <td><a href="{openlink}" title="open {fileinfo.path}" target="_blank">{icon(openiconName)}</a></td>
          <td>
              <a href="{openlink}" title="open {fileinfo.path}" target="_blank">
                  <span style="font-size:12px;vertical-align: top">{folder_path}</span><br>
                  <span style="font-size:16px;vertical-align: bottom">{fileinfo.name}&nbsp;({fileinfo.size_formatted})</span>
              </a>
          </td>{action_links}
        </tr>
    </table>"""

        return content

    def render_default_info(self) -> str:
        """
        Render default info template - calls _render_short_info (no duplication!)
        """
        # Get shortinfo HTML by calling the other method
        shortinfo_html = self.render_short_info()
        fileinfo=self.fileinfo
        markup = f"""
<table>
    <tr><th>Name</th><th>length</th><th>size</th></tr>
    <tr><td>{fileinfo.name}</td><td>{fileinfo.size}</td><td>{fileinfo.size_formatted}</td></tr>
    <tr><td>{shortinfo_html}</td></tr>
</table>
"""
        return markup

    def get_fileinfo(self,filename:str):
        # Translate path if mapping exists
        if self.path_mapping:
            filename = self.path_mapping.translate(filename)

        file_path = Path(filename).resolve()

        # Create FileInfo object
        fileinfo = FileInfo(str(file_path))
        return fileinfo

    def render_info(
        self,
        template_name: str = "defaultinfo",
    ) -> str:
        """
        Render file info as HTML.
        """
        # Dispatch to appropriate renderer - they handle their own links!
        if template_name == "shortinfo":
            markup=self.render_short_info()
        else:
            markup=self.render_default_info()
        return markup

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
        self, filename: str, action: str = "info"
    ) -> Response:
        """
        Main handler for file access requests.

        Args:
            filename: Path to the file
            action: Action to perform (info, shortinfo, open, browse, download)

        Returns:
            FastAPI Response object

        Raises:
            HTTPException: For various error conditions
        """
        try:
            self.fileinfo=self.get_fileinfo(filename)
            # Check file exists
            if not self.fileinfo.exists:
                raise HTTPException(status_code=404, detail="File not found")

            # Handle different actions
            if action == "info":
                html = self.render_info("defaultinfo")
                return HTMLResponse(content=html)

            elif action == "shortinfo":
                html = self.render_info("shortinfo")
                return HTMLResponse(content=html)

            elif action == "download":
                if not self.fileinfo.is_file:
                    raise HTTPException(
                        status_code=400, detail="Cannot download directory"
                    )

                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(str(self.fileinfo.file_path))
                if mime_type is None:
                    mime_type = "application/octet-stream"

                fileresponse=FileResponse(
                    path=str(self.fileinfo.file_path),
                    media_type=mime_type,
                    filename=self.fileinfo.name,
                    headers={
                        "Content-Disposition": f'attachment; filename="{self.fileinfo.name}"',
                    },
                )
                return fileresponse

            elif action == "open":
                try:
                    self.open_file_in_desktop(self.fileinfo.file_path, open_parent=False)
                    return Response(status_code=204)
                except RuntimeError as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Server may be running in headless mode or file opening failed: {e}",
                    )

            elif action == "browse":
                try:
                    self.open_file_in_desktop(self.fileinfo.file_path, open_parent=True)
                    return Response(status_code=204)
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

    def add_file_routes(self, app):
        """
        Add file access routes to FastAPI application.

        Args:
            app: FastAPI application instance
        """

        @app.get(
            "/file",
            responses={
                200: {"description": "File information or download"},
                204: {"description": "File action completed (open/browse)"},
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
        ):
            """
            Access a file with various actions.

            - **info**: Display detailed file information
            - **shortinfo**: Display brief file information
            - **open**: Open file in default application
            - **browse**: Open file's parent directory
            - **download**: Download the file
            """
            return self.handle_file_access(filename, action)