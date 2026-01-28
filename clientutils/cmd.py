"""
Command line entry point
"""

from argparse import ArgumentParser, Namespace

from basemkit.base_cmd import BaseCmd

from clientutils.clipboard import Clipboard
from clientutils.version import Version
from clientutils.webserver import ClientUtilsServer


class ClientUtilsCmd(BaseCmd):
    """Command Line Interface"""

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        parser = super().getArgParser(description, version_msg)
        parser.add_argument("--start", action="store_true", help="start the webserver")
        parser.add_argument(
            "--host",
            dest="host",
            default="0.0.0.0",
            help="host to bind (default: 0.0.0.0)",
        )
        parser.add_argument(
            "--port",
            dest="port",
            type=int,
            default=9998,
            help="port for the webserver (default: 9998)",
        )
        parser.add_argument(
            "--no-file-access",
            dest="no_file_access",
            action="store_true",
            help="disable file access routes",
        )
        parser.add_argument(
            "--icons-dir",
            dest="icons_dir",
            default=None,
            help="path to icons directory",
        )
        parser.add_argument(
            "--external-base-url",
            dest="external_base_url",
            default=None,
            help="external base URL used by file routes (e.g. https://clientutils.example.com/)",
        )
        parser.add_argument(
            "--log-level",
            dest="log_level",
            default="info",
            choices=["critical", "error", "warning", "info", "debug", "trace"],
            help="uvicorn log level",
        )
        return parser

    def handle_args(self, args: Namespace) -> bool:
        handled = super().handle_args(args)
        if handled:
            return True

        if args.debug:
            Clipboard.debug = True

        if args.start:
            enable_file_access = not bool(args.no_file_access)
            server = ClientUtilsServer(
                host=args.host,
                port=args.port,
                enable_file_access=enable_file_access,
                icons_dir=args.icons_dir,
                external_base_url=args.external_base_url,
                log_level=args.log_level,
            )
            print(
                f"Starting ClientUtils server on {args.host}:{args.port} (file access: {enable_file_access})"
            )
            server.start()
            return True
        return False


def main(argv=None):
    """Main entry point."""
    exit_code = ClientUtilsCmd.main(Version(), argv)
    return exit_code


if __name__ == "__main__":
    main()
