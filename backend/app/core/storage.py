"""NEXUS Storage Abstraction."""

import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile


class StorageInterface(ABC):
    """Abstract interface for storing and retrieving document files."""

    @abstractmethod
    async def store_file(self, file: UploadFile, tenant_id: uuid.UUID) -> str:
        """Store an uploaded file and return its storage URI."""
        pass

    @abstractmethod
    async def get_file_path(self, uri: str) -> Path:
        """Get the local filesystem path for a stored file (for parsing)."""
        pass

    @abstractmethod
    async def read_file(self, uri: str) -> bytes:
        """Read the entire file content into memory."""
        pass


class LocalDiskStorage(StorageInterface):
    """Local filesystem-based storage implementation."""

    def __init__(self, base_dir: str = "data/storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def store_file(self, file: UploadFile, tenant_id: uuid.UUID) -> str:
        # Prevent path traversal
        filename = Path(file.filename or "unnamed").name

        # Partition by tenant and unique ID
        file_id = uuid.uuid4().hex
        tenant_dir = self.base_dir / str(tenant_id)
        tenant_dir.mkdir(exist_ok=True)

        dest_path = tenant_dir / f"{file_id}_{filename}"

        # Copy content
        # UploadFile has read/write, but doing it in chunks or using shutil is better
        # For simple local implementation:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return f"local://{tenant_id}/{file_id}_{filename}"

    async def get_file_path(self, uri: str) -> Path:
        if not uri.startswith("local://"):
            raise ValueError(f"Invalid URI scheme for LocalDiskStorage: {uri}")

        rel_path = uri.replace("local://", "")
        # Prevent path traversal
        path = self.base_dir.joinpath(rel_path).resolve()

        if not path.is_relative_to(self.base_dir.resolve()):
            raise ValueError("Path traversal attempt detected")

        if not path.exists():
            raise FileNotFoundError(f"File not found: {uri}")

        return path

    async def read_file(self, uri: str) -> bytes:
        path = await self.get_file_path(uri)
        return path.read_bytes()


def get_storage_provider() -> StorageInterface:
    """Factory for getting the configured storage provider."""
    # In the future, this could be configured via settings (e.g., GCS, S3)
    return LocalDiskStorage()
