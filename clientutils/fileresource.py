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
from clientutils.fileinfo import FileInfo, Link
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
            icon_img= f"<img src='{self.base_url}fileicon/{name}' alt='{alt}' title='{title}'/>"
            return icon_img

        fileinfo = self.fileinfo

        # Generate action links from fileinfo
        download_url = fileinfo.get_action_url(self.base_url, "download")
        browse_url = fileinfo.get_action_url(self.base_url, "browse")
        open_url = fileinfo.get_action_url(self.base_url, "open")
        openiconName = FileAccess.get_icon_name(fileinfo.file_path)

        # Get parent folder path
        folder_path = str(Path(fileinfo.path).parent)

        # Check if file exists
        if not Path(fileinfo.path).exists():
            error_text = f"{icon('document_error.png')}{fileinfo.path}"
            content = f"<span style=\"color: #ff0000;\" title='{fileinfo.path} does not exist'>{error_text}</span>"
        else:
            # Action links for files only
            action_links = ""
            if fileinfo.is_file:
                download_icon = icon('document_down.png')
                browse_icon = icon('folder_view.png')
                download_link = Link.create(download_url, f"download {fileinfo.filename}", download_icon)
                browse_link = Link.create(browse_url, f"browse {fileinfo.filename}", browse_icon)

                action_links = f"""<td>{download_link}{browse_link}</td>"""

            file_span = f"""<span style="font-size:16px;vertical-align: bottom">{fileinfo.name}&nbsp;({fileinfo.size_formatted})</span>"""

            # Create the main open link
            open_icon = icon(openiconName)
            open_link_content = f"{file_span}"
            open_icon_link = Link.create(open_url, f"open {fileinfo.path}", open_icon)
            open_content_link = Link.create(open_url, f"open {fileinfo.path}", open_link_content)

            content = f"""<table class='wikitable' style='margin:auto text-align:left'>
            <tr>
              <td>{open_icon_link}</td>
              <td>{open_content_link}</td>
              {action_links}
            </tr>
        </table>"""

        return content

    def render_default_info(self) -> str:
            """
            Render default info with simple, clean styling
            """
            shortinfo_html = self.render_short_info()
            fileinfo = self.fileinfo
            server_row=""
            wiki_row=""
            if self.path_mapping:
                server=self.path_mapping.mount_config.server
                server_url=f"https://{server}{fileinfo.filename}"
                server_link=Link.create(server_url, f"open on {server}", fileinfo.filename)
                server_row=f"<tr><td>{server_link}</td></tr>"
                pme=self.path_mapping.get_mapping_for_path(fileinfo.filename)
                if pme:
                    relname=fileinfo.filename.removeprefix("/"+pme.name)
                    wiki_markup=f"{{{{File|{pme.name}|{relname}}}}}"
                    wiki_row=f"<tr><td><pre>{wiki_markup}</pre></td></tr>"
            markup=f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>File Info</title>
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
            <style>
                :root {{
                    --primary-color: #4752C4;
                    --text-light: white;
                    --border-width: 3px;
                    --spacing-medium: 10px;
                    --radius-medium: 8px;
                }}

                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}

                .info-table {{
                    border: var(--border-width) solid var(--primary-color);
                    border-radius: var(--radius-medium);
                    border-spacing: 0;
                    border-collapse: separate;
                    width: 100%;
                    max-width: 600px;
                    overflow: hidden;
                }}

                .info-table th,
                .info-table td {{
                    padding: var(--spacing-medium);
                    text-align: left;
                }}

                .info-table th {{
                    background-color: var(--primary-color);
                    color: var(--text-light);
                }}

                .link-button {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    color: var(--text-light);
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <table class="info-table">
                <tr>
                    <th>
                        <a href="https://github.com/WolfgangFahl/pyclientutils" class="link-button" target="_blank">
                            <span class="material-icons">memory</span>GITHUB
                        </a>
                    </th>
                </tr>
                <tr><td>{shortinfo_html}</td></tr>
                {server_row}
                {wiki_row}
                <tr><td>{fileinfo.path}</td></tr>
            </table>
        </body>
        </html>"""
            return markup

    def get_fileinfo(self,filename:str):
        """
        get the file info for the given filename
        """
        file_path=filename
        # Translate path if mapping exists
        if self.path_mapping:
            file_path = self.path_mapping.translate(filename)

        file_path = Path(file_path).resolve()

        # Create FileInfo object
        fileinfo = FileInfo(file_path=file_path,filename=filename)
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

    def handle_file_open_action(self, open_parent: bool = False) -> Response:
        """
        Handle file open/browse action and return appropriate response.

        Args:
            open_parent: If True, open parent directory instead of file

        Returns:
            Response with either HTML info or 204 status
        """
        info_html= self.render_info("defaultinfo")
        status_code=200
        try:
            self.open_file_in_desktop(self.fileinfo.file_path, open_parent=open_parent)
            # After successful open, return file info instead of empty 204
        except Exception as e:
            info_html+= f"<p style='color: red;'>Failed to open: {e}</p>"
            status_code=500
        response=HTMLResponse(content=info_html, status_code=status_code)
        return response

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
                return self.handle_file_open_action(open_parent=False)

            elif action == "browse":
                return self.handle_file_open_action(open_parent=True)

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