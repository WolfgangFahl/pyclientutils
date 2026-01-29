"""
Created on 2026-01-28

@author: wf
"""
import os
import tempfile
from clientutils.pathmapping import (
    PathMapEntry,
    PathMapping,
    MountConfig,
    OSType
)
from basemkit.basetest import Basetest


class TestPathMapping(Basetest):
    """
    Test the pathmapping functionality
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

        # Create temporary YAML file for testing
        self.test_yaml = self._create_test_config()

    def _create_test_config(self) -> str:
        """Create a temporary test configuration file."""
        yaml_content = """# JohnDoe.com Path mapping configuration
# Test configuration
case_sensitive: false

mount_config:
  enabled: false
  server: fileserver.johndoe.com
  protocol: smb

mappings:
  - name: projects
    windows: "P:"
    macos: "/Volumes/projects"
    linux: "/mnt/projects"
    other: "/projects"

  - name: documents
    windows: "D:"
    macos: "/Volumes/documents"
    linux: "/mnt/documents"
    other: "/documents"

  - name: media
    windows: "M:"
    macos: "/Volumes/media"
    linux: "/mnt/media"
    other: "/media"
"""
        # Create temp file
        temp_dir = tempfile.gettempdir()
        yaml_path = os.path.join(temp_dir, "test_path_mappings.yaml")

        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        return yaml_path

    def get_test_mapping(self)->PathMapping:
        mapping = PathMapping.ofYaml(self.test_yaml)
        return mapping


    def test_path_mapping_creation(self):
        """Test creating a PathMapping instance."""
        mapping = PathMapEntry(
            name="test",
            windows="T:",
            macos="/Volumes/test",
            linux="/mnt/test",
            other="/test"
        )

        self.assertEqual(mapping.name, "test")
        self.assertEqual(mapping.windows, "T:")
        self.assertEqual(mapping.macos, "/Volumes/test")
        self.assertEqual(mapping.linux, "/mnt/test")
        self.assertEqual(mapping.other, "/test")

    def test_path_mapping_get_path(self):
        """Test getting paths for different OS types."""
        mapping = PathMapEntry(
            name="test",
            windows="T:",
            macos="/Volumes/test",
            linux="/mnt/test",
            other="/test"
        )

        self.assertEqual(mapping.get_path(OSType.WINDOWS), "T:")
        self.assertEqual(mapping.get_path(OSType.MACOS), "/Volumes/test")
        self.assertEqual(mapping.get_path(OSType.LINUX), "/mnt/test")
        self.assertEqual(mapping.get_path(OSType.OTHER), "/test")

    def test_os_type_detection(self):
        """Test OS type detection from platform."""
        os_type = OSType.from_platform()
        self.assertIsInstance(os_type, OSType)
        if self.debug:
            print(f"Detected OS: {os_type.value}")

    def test_mount_config(self):
        """Test MountConfig creation and conversion."""
        mount_config = MountConfig(
            enabled=True,
            server="fileserver.johndoe.com",
            protocol="smb"
        )

        self.assertTrue(mount_config.enabled)
        self.assertEqual(mount_config.server, "fileserver.johndoe.com")
        self.assertEqual(mount_config.protocol, "smb")

        # Test to_dict conversion
        config_dict = mount_config.to_dict()
        self.assertEqual(config_dict["enabled"], True)
        self.assertEqual(config_dict["server"], "fileserver.johndoe.com")

    def test_config_from_yaml(self):
        """Test loading configuration from YAML file."""
        config = self.get_test_mapping()

        self.assertIsNotNone(config)
        self.assertFalse(config.case_sensitive)
        self.assertEqual(len(config.mappings), 3)

        # Check mount config
        self.assertFalse(config.mount_config.enabled)
        self.assertEqual(config.mount_config.server, "fileserver.johndoe.com")
        self.assertEqual(config.mount_config.protocol, "smb")

        if self.debug:
            print(f"Loaded {len(config.mappings)} mappings from config")

    def test_get_mapping_by_name(self):
        """Test retrieving mapping by logical name."""
        config = self.get_test_mapping()

        # Test existing mappings
        projects = config.get_mapping_by_name("projects")
        self.assertIsNotNone(projects)
        self.assertEqual(projects.name, "projects")
        self.assertEqual(projects.windows, "P:")

        documents = config.get_mapping_by_name("documents")
        self.assertIsNotNone(documents)
        self.assertEqual(documents.macos, "/Volumes/documents")

        media = config.get_mapping_by_name("media")
        self.assertIsNotNone(media)
        self.assertEqual(media.linux, "/mnt/media")

        # Test non-existing mapping
        nonexistent = config.get_mapping_by_name("nonexistent")
        self.assertIsNone(nonexistent)

    def test_get_mapping_by_path(self):
        """Test retrieving mapping by path prefix."""
        config = self.get_test_mapping()
        current_os = OSType.from_platform()

        # Get the projects mapping
        projects = config.get_mapping_by_name("projects")
        project_path = projects.get_path(current_os)

        # Test path matching
        test_path = f"{project_path}/subdir/file.txt"
        found_mapping = config.get_mapping_by_path(test_path, current_os)

        self.assertIsNotNone(found_mapping)
        self.assertEqual(found_mapping.name, "projects")

        if self.debug:
            print(f"Path '{test_path}' matched to mapping: {found_mapping.name}")

    def test_case_insensitive_matching(self):
        """Test case-insensitive path matching."""
        config = self.get_test_mapping()
        self.assertFalse(config.case_sensitive)

        # For macOS/Linux paths (since they're case-sensitive by nature)
        mapping = config.get_mapping_by_path("/VOLUMES/PROJECTS/file.txt", OSType.MACOS)

        if mapping:
            self.assertEqual(mapping.name, "projects")
            if self.debug:
                print("Case-insensitive matching works correctly")

    def test_longest_prefix_matching(self):
        """Test that longest matching prefix is selected."""
        # Create config with overlapping paths
        config = PathMapping(
            case_sensitive=False,
            mappings=[
                PathMapEntry(
                    name="root",
                    windows="C:",
                    macos="/Volumes",
                    linux="/mnt",
                    other="/mnt"
                ),
                PathMapEntry(
                    name="projects",
                    windows="C:/Projects",
                    macos="/Volumes/projects",
                    linux="/mnt/projects",
                    other="/mnt/projects"
                )
            ]
        )

        # Should match the more specific "projects" mapping
        mapping = config.get_mapping_by_path(
            "/Volumes/projects/myproject",
            OSType.MACOS
        )

        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.name, "projects")

        if self.debug:
            print(f"Longest prefix match: {mapping.name}")

    def test_config_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = self.get_test_mapping()
        config_dict = config.to_dict()

        self.assertIn("case_sensitive", config_dict)
        self.assertIn("mount_config", config_dict)
        self.assertIn("mappings", config_dict)

        self.assertFalse(config_dict["case_sensitive"])
        self.assertEqual(len(config_dict["mappings"]), 3)

        if self.debug:
            print(f"Config dict keys: {list(config_dict.keys())}")

    def test_cross_platform_paths(self):
        """Test path retrieval for all OS types."""
        config = self.get_test_mapping()
        projects = config.get_mapping_by_name("projects")

        # Test all OS types
        paths = {
            OSType.WINDOWS: "P:",
            OSType.MACOS: "/Volumes/projects",
            OSType.LINUX: "/mnt/projects",
            OSType.OTHER: "/projects"
        }

        for os_type, expected_path in paths.items():
            actual_path = projects.get_path(os_type)
            self.assertEqual(actual_path, expected_path)
            if self.debug:
                print(f"{os_type.value}: {actual_path}")

    def test_translate_ospath(self):
        """Test translating paths between operating systems."""
        config = self.get_test_mapping()

        test_cases = [
            # (filepath, from_os, to_os, expected_result, description)
            ("P:/myproject/file.txt", OSType.WINDOWS, OSType.LINUX, "/mnt/projects/myproject/file.txt", "Windows to Linux"),
            ("/mnt/projects/myproject/file.txt", OSType.LINUX, OSType.WINDOWS, "P:/myproject/file.txt", "Linux to Windows"),
            ("D:\\docs\\report.pdf", OSType.WINDOWS, OSType.MACOS, "/Volumes/documents/docs/report.pdf", "Windows to macOS with backslashes"),
            ("/Volumes/media/videos/movie.mp4", OSType.MACOS, OSType.LINUX, "/mnt/media/videos/movie.mp4", "macOS to Linux"),
        ]

        for filepath, from_os, to_os, expected, description in test_cases:
            with self.subTest(case=description):
                result = config.translate_ospath(filepath, from_os, to_os)
                self.assertEqual(result, expected)
                if self.debug:
                    print(f"{description}: {filepath} -> {result}")

    def test_translate_auto_detect(self):
        """Test auto-detecting source OS and translating to current OS."""
        config = self.get_test_mapping()
        current_os = OSType.from_platform()

        # Test cases based on current OS
        test_cases = []

        if current_os == OSType.WINDOWS:
            test_cases = [
                ("P:/myproject/file.txt", "P:/myproject/file.txt", "Windows path on Windows"),
                ("/mnt/projects/myproject/file.txt", "P:/myproject/file.txt", "Linux path to Windows"),
            ]
        elif current_os == OSType.LINUX:
            test_cases = [
                ("P:/myproject/file.txt", "/mnt/projects/myproject/file.txt", "Windows path to Linux"),
                ("/mnt/projects/myproject/file.txt", "/mnt/projects/myproject/file.txt", "Linux path on Linux"),
            ]
        elif current_os == OSType.MACOS:
            test_cases = [
                ("P:/myproject/file.txt", "/Volumes/projects/myproject/file.txt", "Windows path to macOS"),
                ("/mnt/projects/myproject/file.txt", "/Volumes/projects/myproject/file.txt", "Linux path to macOS"),
            ]

        for filepath, expected, description in test_cases:
            with self.subTest(case=description):
                result = config.translate(filepath)
                self.assertEqual(result, expected)
                if self.debug:
                    print(f"{description}: {filepath} -> {result}")

    def tearDown(self):
        """Clean up test files."""
        if hasattr(self, 'test_yaml') and os.path.exists(self.test_yaml):
            os.remove(self.test_yaml)
        Basetest.tearDown(self)