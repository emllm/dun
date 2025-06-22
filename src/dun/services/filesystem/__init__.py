"""File system service for handling file operations."""
import os
import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple, Union

from dun.core.protocols import ServiceProtocol
from dun.config.settings import get_settings


class FileSystemService(ServiceProtocol):
    """Service for file system operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self._temp_dir: Optional[Path] = None
    
    @property
    def name(self) -> str:
        return "filesystem"
    
    @property
    def is_available(self) -> bool:
        return True  # File system is always available
    
    async def initialize(self) -> None:
        """Initialize the file system service."""
        # Ensure all required directories exist
        for dir_path in [
            self.settings.DATA_DIR,
            self.settings.LOGS_DIR,
            self.settings.CACHE_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def shutdown(self) -> None:
        """Clean up any temporary resources."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
    
    def get_temp_dir(self, prefix: str = "dun_") -> Path:
        """Get or create a temporary directory."""
        if self._temp_dir is None or not self._temp_dir.exists():
            self._temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        return self._temp_dir
    
    def is_writable(self, path: Union[str, Path]) -> bool:
        """Check if a path is writable."""
        path = Path(path).resolve()
        
        # If it's a file, check its parent directory
        if path.is_file() or path.suffix:
            path = path.parent
        
        # Create the directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        # Test write permission
        test_file = path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, IOError):
            return False
    
    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Ensure a directory exists and is writable."""
        path = Path(path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        
        if not self.is_writable(path):
            raise PermissionError(f"Directory is not writable: {path}")
        
        return path
    
    def find_files(
        self,
        directory: Union[str, Path],
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> List[Path]:
        """Find files with given extensions in a directory."""
        directory = Path(directory).resolve()
        
        if not directory.exists() or not directory.is_dir():
            return []
        
        extensions = [ext.lower() for ext in (extensions or [])]
        found_files = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for ext in extensions or [""]:
            if ext and not ext.startswith("."):
                ext = f".{ext}"
            
            for file_path in directory.glob(f"{pattern}{ext}"):
                if file_path.is_file():
                    found_files.append(file_path)
        
        return sorted(found_files)
    
    def read_file(self, file_path: Union[str, Path], binary: bool = False) -> Union[str, bytes]:
        """Read file content."""
        mode = "rb" if binary else "r"
        with open(file_path, mode) as f:
            return f.read()
    
    def write_file(
        self,
        file_path: Union[str, Path],
        content: Union[str, bytes],
        binary: bool = False,
        create_parents: bool = True,
    ) -> Path:
        """Write content to a file."""
        file_path = Path(file_path)
        
        if create_parents:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "wb" if binary or isinstance(content, bytes) else "w"
        with open(file_path, mode) as f:
            f.write(content)
        
        return file_path
    
    def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False,
    ) -> Path:
        """Copy a file to a new location."""
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        if destination.exists():
            if not overwrite:
                raise FileExistsError(f"Destination file exists and overwrite=False: {destination}")
            if destination.is_dir():
                destination = destination / source.name
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        if source.is_file():
            shutil.copy2(source, destination)
        else:
            shutil.copytree(source, destination, dirs_exist_ok=overwrite)
        
        return destination
    
    def move_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False,
    ) -> Path:
        """Move a file to a new location."""
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        if destination.exists():
            if not overwrite:
                raise FileExistsError(f"Destination exists and overwrite=False: {destination}")
            if destination.is_file():
                destination.unlink()
            else:
                shutil.rmtree(destination)
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        
        return destination
    
    def delete_file(self, path: Union[str, Path], missing_ok: bool = True) -> None:
        """Delete a file or directory."""
        path = Path(path)
        
        if not path.exists():
            if not missing_ok:
                raise FileNotFoundError(f"Path not found: {path}")
            return
        
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)
    
    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "dun_",
        dir: Optional[Union[str, Path]] = None,
        text: bool = False,
    ) -> Tuple[Path, BinaryIO]:
        """Create a temporary file and return its path and file object."""
        dir_path = Path(dir) if dir else self.get_temp_dir()
        dir_path.mkdir(parents=True, exist_ok=True)
        
        mode = 'w+' if text else 'w+b'
        file_obj = tempfile.NamedTemporaryFile(
            mode=mode,
            prefix=prefix,
            suffix=suffix,
            dir=str(dir_path),
            delete=False
        )
        return Path(file_obj.name), file_obj
    
    def get_size(self, path: Union[str, Path]) -> int:
        """Get size of a file or directory in bytes."""
        path = Path(path)
        
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
        else:
            raise FileNotFoundError(f"Path not found: {path}")
    
    def get_mime_type(self, path: Union[str, Path]) -> str:
        """Get MIME type of a file."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type or "application/octet-stream"
    
    def create_archive(
        self,
        source_dir: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        format: str = "zip"
    ) -> Path:
        """Create an archive of a directory."""
        source_dir = Path(source_dir)
        
        if not output_path:
            output_path = source_dir.with_suffix(f".{format}")
        else:
            output_path = Path(output_path)
        
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.make_archive(
            str(output_path.with_suffix('')),
            format,
            root_dir=source_dir.parent,
            base_dir=source_dir.name
        )
        
        return output_path
    
    def extract_archive(
        self,
        archive_path: Union[str, Path],
        extract_dir: Optional[Union[str, Path]] = None,
        format: Optional[str] = None
    ) -> Path:
        """Extract an archive to a directory."""
        archive_path = Path(archive_path)
        
        if not extract_dir:
            extract_dir = archive_path.parent / archive_path.stem
        else:
            extract_dir = Path(extract_dir)
        
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.unpack_archive(str(archive_path), str(extract_dir), format)
        
        return extract_dir


# Global file system service instance
fs = FileSystemService()
