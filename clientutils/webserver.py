"""

ClientUtils Server with clipboard, file access, and path mapping support

WF 2026-01-28 migrated from 2015 Java Jersey RESTful solution
"""

from typing import Optional

from clientutils.clipboard import Clipboard
from clientutils.fileaccess import FileAccessResource, FileAccess
from clientutils.pathmapping import PathMapping, OSType
from clientutils.version import Version
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import uvicorn


class ClientUtilsServer:
    """Serves static file icons, clipboard content, and file access via HTTP"""

    # Supported image formats and their MIME types
    SUPPORTED_FORMATS = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "GIF": "image/gif",
        "BMP": "image/bmp",
        "WEBP": "image/webp",
    }

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9998,
        enable_file_access: bool = True,
        external_base_url: Optional[str] = None,
        path_mapping_yaml_path: Optional[str] = None,
        log_level: str = "info",

    ):
        """
        Args:
            host: the host/iface to bind (default "0.0.0.0")
            port: the port to listen on (default 9998)
            enable_file_access: whether to register file access routes
            external_base_url: optional base URL for FileAccessResource (overrides host/port)
            path_mapping_yaml_path: optional path to YAML path mapping configuration
            log_level: uvicorn log level
        """
        self.host = host
        self.port = port
        self.enable_file_access = enable_file_access
        self.external_base_url = external_base_url
        self.path_mapping_yaml_path = path_mapping_yaml_path
        self.log_level = log_level
        self.path_mapping: Optional[PathMapping] = None
        self.os_type = OSType.from_platform()
        if self.path_mapping_yaml_path:
            try:
                self.path_mapping = PathMapping.ofYaml(self.path_mapping_yaml_path)
            except Exception as e:
                print(f"Warning: failed to load path mapping from '{self.path_mapping_yaml_path}': {e}")
                self.path_mapping = None

        self.app = FastAPI(
            title=Version.name,
            description=Version.description,
            version=Version.version,
        )
        self._setup_routes()

    def _setup_routes(self):
        """Configure routes for static file serving, clipboard access, and file operations"""
        try:
            icons_dir = FileAccess.get_icons_directory()
            # Mount static files - automatically handles file serving and closing
            self.app.mount(
                "/fileicon", StaticFiles(directory=str(icons_dir)), name="fileicon"
            )
        except FileNotFoundError as e:
            print(f"Warning: {e}")

        # Add file access routes if enabled
        if self.enable_file_access:
            base_url = f"http://localhost:{self.port}/"
            file_resource = FileAccessResource(base_url=base_url,path_mapping=self.path_mapping)
            file_resource.add_file_routes(self.app)

        @self.app.get(
            "/clipboard",
            responses={
                200: {"description": "Clipboard image content"},
                204: {"description": "No image in clipboard"},
                400: {"description": "Unsupported format"},
                500: {"description": "Server error"},
            },
            tags=["clipboard"],
        )
        def clipboard_content(
            format: str = Query(
                default="PNG",
                description="Image format (PNG, JPEG, GIF, BMP, WEBP)",
                pattern="^(PNG|JPEG|JPG|GIF|BMP|WEBP)$",
            )
        ):
            """
            Get clipboard image content as download.

            Returns the current clipboard image in the specified format.
            """
            img_format = format.upper()

            # Validate format
            if img_format not in self.SUPPORTED_FORMATS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported format: {img_format}. Supported: {', '.join(self.SUPPORTED_FORMATS.keys())}",
                )

            try:
                # Get clipboard content in requested format
                image_bytes = Clipboard.get_image_bytes(img_format)

                if image_bytes is None:
                    return Response(status_code=204)  # NO_CONTENT

                # Get MIME type and file extension
                mime_type = self.SUPPORTED_FORMATS[img_format]
                extension = img_format.lower()

                return Response(
                    content=image_bytes,
                    media_type=mime_type,
                    headers={
                        "Content-Disposition": f"attachment; filename=clipboard.{extension}"
                    },
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def start(self):
        """Start the web server using uvicorn (async ASGI server)"""
        print(f"Starting ClientUtils Server on http://0.0.0.0:{self.port}")
        if self.enable_file_access:
            print(
                f"  - File access: http://localhost:{self.port}/file?filename=<path>&action=<info|download|open|browse>"
            )
        print(
            f"  - Clipboard: http://localhost:{self.port}/clipboard?format=<PNG|JPEG|...>"
        )
        print(f"  - File icons: http://localhost:{self.port}/fileicon/<icon_name>")
        print(f"  - API docs: http://localhost:{self.port}/docs")

        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")


if __name__ == "__main__":
    server = ClientUtilsServer()
    server.start()
