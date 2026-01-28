"""
Simple REST server for serving file icons and clipboard content
"""

from pathlib import Path

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import uvicorn

from clientutils.clipboard import Clipboard


class ClientUtilsServer:
    """Serves static file icons and clipboard content via HTTP"""

    # Supported image formats and their MIME types
    SUPPORTED_FORMATS = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "GIF": "image/gif",
        "BMP": "image/bmp",
        "WEBP": "image/webp",
    }

    def __init__(self, port: int = 9998):
        self.port = port
        self.app = FastAPI(
            title="ClientUtils Server",
            description="Serve file icons and clipboard content",
            version="1.0.0"
        )
        self._setup_routes()

    def get_icons_directory(self) -> Path:
        """
        Get the path to the icons directory.

        Returns:
            Path: Absolute path to the icons directory

        Raises:
            FileNotFoundError: If icons directory doesn't exist
        """
        # Try relative to this file
        icons_dir = Path(__file__).parent.parent / "clientutils_examples" / "icons"

        if not icons_dir.exists():
            # Try relative to current working directory
            icons_dir = Path.cwd() / "clientutils_examples" / "icons"

        if not icons_dir.exists():
            raise FileNotFoundError(f"Icons directory not found. Tried: {icons_dir}")

        return icons_dir.resolve()

    def _setup_routes(self):
        """Configure routes for static file serving and clipboard access"""
        try:
            icons_dir = self.get_icons_directory()
            # Mount static files - automatically handles file serving and closing
            self.app.mount(
                "/fileicon",
                StaticFiles(directory=str(icons_dir)),
                name="fileicon"
            )
        except FileNotFoundError as e:
            print(f"Warning: {e}")

        @self.app.get(
            "/clipboard",
            responses={
                200: {"description": "Clipboard image content"},
                204: {"description": "No image in clipboard"},
                400: {"description": "Unsupported format"},
                500: {"description": "Server error"}
            }
        )
        def clipboard_content(
            format: str = Query(
                default="PNG",
                description="Image format (PNG, JPEG, GIF, BMP, WEBP)",
                pattern="^(PNG|JPEG|JPG|GIF|BMP|WEBP)$"
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
                    detail=f"Unsupported format: {img_format}. Supported: {', '.join(self.SUPPORTED_FORMATS.keys())}"
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
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )


if __name__ == "__main__":
    server = ClientUtilsServer()
    server.start()