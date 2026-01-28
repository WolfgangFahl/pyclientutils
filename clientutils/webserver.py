"""
Simple REST server for serving file icons
"""

from pathlib import Path

from flask import Flask, send_from_directory


class ClientUtilsServer:
    """Serves static file icons via HTTP"""

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
        """Configure routes for static file serving"""
        # Get the icons directory path
        icons_dir = self.get_icons_directory()

        @self.app.route("/fileicon/<path:filename>")
        def serve_icon(filename):
            """Serve file icons"""
            return send_from_directory(icons_dir, filename)

    def start(self):
        """Start the web server"""
        self.app.run(host="0.0.0.0", port=self.port, debug=False)
