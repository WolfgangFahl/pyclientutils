"""
Created on 2026-01-28

@author: wf
"""
"""
Path mapping configuration using dataclasses.
Supports cross-platform path normalization.
"""
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import platform
from basemkit.yamlable import lod_storable

class OSType(Enum):
    """Operating system types."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    OTHER = "other"

    @classmethod
    def from_platform(cls) -> 'OSType':
        """Detect current OS type."""
        system = platform.system().lower()
        if system == "windows":
            return cls.WINDOWS
        elif system == "darwin":
            return cls.MACOS
        elif system == "linux":
            return cls.LINUX
        else:
            return cls.OTHER


@lod_storable
class PathMapEntry:
    """
    Represents a single logical path mapping across OS types.

    Attributes:
        name: Logical name of the path (e.g., "bitplan", "backup")
        windows: Windows path (e.g., "X:")
        macos: macOS path (e.g., "/Volumes/bitplan")
        linux: Linux path (e.g., "/bitplan")
        other: Generic/other OS path (e.g., "/bitplan")
    """
    name: str
    windows: str
    macos: str
    linux: str
    other: str

    def get_path(self, os_type: OSType) -> str:
        """Get path for specific OS type."""
        mapping = {
            OSType.WINDOWS: self.windows,
            OSType.MACOS: self.macos,
            OSType.LINUX: self.linux,
            OSType.OTHER: self.other,
        }
        return mapping[os_type]

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "windows": self.windows,
            "macos": self.macos,
            "linux": self.linux,
            "other": self.other,
        }


@lod_storable
class MountConfig:
    """
    Configuration for automounting.

    Attributes:
        enabled: Whether automounting is enabled
        server: Server name/IP for network mounts
        protocol: Mount protocol (smb, nfs, etc.)
    """
    enabled: bool = False
    server: Optional[str] = None
    protocol: str = "smb"

    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "enabled": self.enabled,
            "server": self.server,
            "protocol": self.protocol,
        }


@lod_storable
class PathMapping:
    """
    Overall configuration for path mappings.

    Attributes:
        mappings: List of path mappings
        mount_config: Automount configuration
        case_sensitive: Whether paths are case-sensitive
    """
    mappings: List[PathMapEntry] = field(default_factory=list)
    mount_config: MountConfig = field(default_factory=MountConfig)
    case_sensitive: bool = True

    @classmethod
    def default_yaml_path(cls):
        yaml_path = os.path.join(os.path.expanduser("~"), ".clientutils", "path_mappings.yaml")
        yaml_path = os.path.realpath(yaml_path)
        return yaml_path

    @classmethod
    def ofYaml(cls, yaml_path: str = None) -> "PathMapping":
        """
        Load configuration from YAML file.

        Args:
            yaml_path: Path to YAML file. If None, uses default path
                      relative to resources/path_mappings.yaml

        Returns:
            PathMappingConfig instance
        """
        if yaml_path is None:
            yaml_path=PathMapping.default_yaml_path()
        # Use the lod_storable yamlable to load from YAML
        pm= cls.load_from_yaml_file(yaml_path)
        return pm


    def get_mapping_by_path(
        self,
        path: str,
        os_type: OSType
    ) -> Optional[PathMapEntry]:
        """
        Find mapping that matches the given path prefix.

        Args:
            path: Path to check
            os_type: OS type of the path

        Returns:
            Matching PathMapping or None
        """
        path_str = str(path)
        if not self.case_sensitive:
            path_str = path_str.lower()

        # Sort by length descending to match longest prefix first
        sorted_mappings = sorted(
            self.mappings,
            key=lambda m: len(m.get_path(os_type)),
            reverse=True
        )

        for mapping in sorted_mappings:
            prefix = mapping.get_path(os_type)
            if not self.case_sensitive:
                prefix = prefix.lower()

            if path_str.startswith(prefix):
                return mapping

        return None

    def get_mapping_by_name(self, name: str) -> Optional[PathMapEntry]:
        """Get mapping by logical name."""
        for mapping in self.mappings:
            if mapping.name == name:
                return mapping
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "case_sensitive": self.case_sensitive,
            "mount_config": self.mount_config.to_dict(),
            "mappings": [m.to_dict() for m in self.mappings],
        }

    def translate_ospath(self, filepath: str, from_os: OSType = None, to_os: OSType = None) -> str:
        """Translate path from one OS to another."""
        if from_os is None:
            from_os = OSType.from_platform()
        if to_os is None:
            to_os = OSType.from_platform()

        filepath = filepath.replace("\\", "/")
        target_path = filepath  # Default to original path

        mapping = self.get_mapping_by_path(filepath, from_os)
        if mapping:
            source = mapping.get_path(from_os)
            target = mapping.get_path(to_os)

            if not self.case_sensitive and filepath.lower().startswith(source.lower()):
                target_path = target + filepath[len(source):]
            elif filepath.startswith(source):
                target_path = filepath.replace(source, target, 1)

        return target_path

    def translate(self, filepath: str) -> str:
        """
        Translate path to current OS, auto-detecting source OS.

        Source OS detection: Windows if drive letter present (e.g., C:, X:), otherwise Linux.

        Args:
            filepath: Path to translate

        Returns:
            Translated path for current OS
        """
        # Detect source OS: Windows if drive letter present, otherwise Linux
        from_os = OSType.WINDOWS if len(filepath) >= 2 and filepath[1] == ':' else OSType.LINUX

        # Target is always current platform
        to_os = OSType.from_platform()

        return self.translate_ospath(filepath, from_os, to_os)

