"""
Command line entry point
"""

from argparse import ArgumentParser, Namespace

from basemkit.base_cmd import BaseCmd

import clientutils
from clientutils.clipboard import Clipboard
from clientutils.webserver import ClientUtilsServer


class Version:
    """Version information"""

    name = "clientutils"
    version = clientutils.__version__
    description = "MediaWiki Client Utilties"
    doc_url = "https://media.bitplan.com/index.php?title=CPSA-A-Analysis"
    updated = "2026-01-28"


class ClientUtilsCmd(BaseCmd):
    """Command Line Interface"""

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        """get the argument parser"""
        parser = super().getArgParser(description, version_msg)
        parser.add_argument(
            "--start",
            action="store_true",
            help="start the webserver",
        )
        parser.add_argument(
            "--port",
            dest="port",
            type=int,
            default=9998,
            help="port for the webserver (default: 9998)",
        )
        return parser

    def handle_args(self, args: Namespace) -> bool:
        """Handle the parsed arguments"""
        # Let base class handle standard args (--about, --debug, etc.)
        handled = super().handle_args(args)
        if handled:
            return True

        if args.debug:
            Clipboard.debug = True

        # Now handle our custom args
        if args.start:
            server = ClientUtilsServer(port=args.port)
            print(f"Starting ClientUtils server on port {args.port}...")
            server.start()
            return True  # Signal we handled it

        # If --start not provided, just exit normally
        return False


def main(argv=None):
    """Main entry point."""
    exit_code = ClientUtilsCmd.main(Version(), argv)
    return exit_code


if __name__ == "__main__":
    main()
