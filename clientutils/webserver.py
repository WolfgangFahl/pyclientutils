"""
Simple REST server for serving file icons and clipboard content
"""

from pathlib import Path

from flask import Flask, Response, request, send_from_directory

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

    def __init__(self, port=9998):
        self.port = port
        self.app = Flask(__name__)
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
        icons_dir = self.get_icons_directory()

        @self.app.route("/fileicon/<path:filename>")
        def serve_icon(filename):
            """Serve file icons"""
            return send_from_directory(icons_dir, filename)

        @self.app.route("/clipboard")
        def clipboard_content():
            """
            Return clipboard image content as download

            Query Parameters:
                format: Image format (PNG, JPEG, GIF, BMP, WEBP). Default: PNG

            Examples:
                /clipboard              -> Returns PNG
                /clipboard?format=JPEG  -> Returns JPEG
            """
            try:
                # Get format parameter, default to PNG
                img_format = request.args.get("format", "PNG").upper()

                # Validate format
                if img_format not in self.SUPPORTED_FORMATS:
                    return Response(
                        f"Unsupported format: {img_format}. Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}",
                        status=400,
                    )

                # Get clipboard content in requested format
                image_bytes = Clipboard.get_image_bytes(img_format)

                if image_bytes is None:
                    return Response(status=204)  # NO_CONTENT

                # Get MIME type and file extension
                mime_type = self.SUPPORTED_FORMATS[img_format]
                extension = img_format.lower()

                return Response(
                    image_bytes,
                    mimetype=mime_type,
                    headers={
                        "Content-Disposition": f"attachment; filename=clipboard.{extension}"
                    },
                )
            except Exception as e:
                return Response(str(e), status=500)

    def start(self):
        """Start the web server"""
        self.app.run(host="0.0.0.0", port=self.port, debug=False)
