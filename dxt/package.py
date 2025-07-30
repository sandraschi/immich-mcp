"""
DXT Packaging Script for ImmichMCP

This script handles the creation and validation of DXT packages for the ImmichMCP project.
It creates a complete DXT package including all source code, dependencies, and documentation.
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone
import hashlib
import subprocess
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dxt_package.log')
    ]
)
logger = logging.getLogger('dxt_packager')

class DXTPackager:
    """Handles the creation and validation of DXT packages."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the DXT packager with the path to the config file."""
        if config_path is None:
            # Use absolute path to dxt.json in the project root
            self.config_path = Path(__file__).parent.parent / 'dxt.json'
        else:
            self.config_path = Path(config_path)
            
        self.config: Dict[str, Any] = {}
        self.package_dir = Path('dist')
        self.version = "0.1.0"
        
    def load_config(self) -> bool:
        """Load and validate the DXT configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Basic validation
            required_fields = ['name', 'version', 'description', 'author']
            for field in required_fields:
                if field not in self.config:
                    logger.error(f"Missing required field in DXT config: {field}")
                    return False
            
            self.version = self.config.get('version', self.version)
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in DXT config: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading DXT config: {e}", exc_info=True)
            return False
    
    def create_manifest(self) -> Dict[str, Any]:
        """Create a comprehensive manifest for the DXT package."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Get git commit hash if available
        commit_hash = None
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            if result.returncode == 0:
                commit_hash = result.stdout.strip()
        except Exception as e:
            logger.warning(f"Could not get git commit hash: {e}")
        
        # Calculate checksum of the config
        config_content = json.dumps(self.config, sort_keys=True).encode('utf-8')
        checksum = hashlib.sha256(config_content).hexdigest()
        
        return {
            "name": self.config['name'],
            "version": self.version,
            "description": self.config.get('description', ''),
            "author": self.config.get('author', ''),
            "created_at": timestamp,
            "checksum": checksum,
            "commit_hash": commit_hash,
            "dependencies": self.config.get('dependencies', {}),
            "tags": self.config.get('tags', []),
            "entry_point": "src/immich_mcp/server.py",
            "python_requires": ">=3.11",
            "package_type": "mcp_plugin"
        }
    
    def _copy_directory(self, src: Path, dst: Path, exclude: Optional[List[str]] = None) -> None:
        """Copy directory contents, excluding specified patterns."""
        if exclude is None:
            exclude = []
            
        if not src.exists():
            return
            
        dst.mkdir(parents=True, exist_ok=True)
        
        for item in src.iterdir():
            if any(item.match(pattern) for pattern in exclude):
                continue
                
            if item.is_dir():
                self._copy_directory(item, dst / item.name, exclude)
            else:
                shutil.copy2(item, dst / item.name)
    
    def _get_git_files(self) -> List[Path]:
        """Get list of files tracked by git."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            if result.returncode == 0:
                return [Path(p) for p in result.stdout.splitlines()]
        except Exception as e:
            logger.warning(f"Could not get git files: {e}")
        
        # Fallback to walking the directory
        return list(Path(".").rglob("*"))
    
    def prepare_package(self) -> bool:
        """Prepare the DXT package with all necessary components."""
        try:
            # Create temp directory for package assembly
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 1. Create package directory structure
                package_name = f"{self.config['name'].lower().replace(' ', '-')}-{self.version}"
                package_root = temp_path / package_name
                
                # 2. Copy all project files (respecting .gitignore)
                project_root = Path(__file__).parent.parent
                exclude_dirs = [
                    '__pycache__', '*.pyc', '.git', '.github', '.vscode',
                    '*.egg-info', 'dist', 'build', '*.log', '*.dxt', '*.zip'
                ]
                
                # Copy source files
                src_dir = project_root / 'src'
                if src_dir.exists():
                    self._copy_directory(src_dir, package_root / 'src', exclude_dirs)
                
                # Copy dxt directory
                dxt_dir = project_root / 'dxt'
                if dxt_dir.exists():
                    self._copy_directory(dxt_dir, package_root / 'dxt', exclude_dirs)
                
                # Copy tests
                tests_dir = project_root / 'tests'
                if tests_dir.exists():
                    self._copy_directory(tests_dir, package_root / 'tests', exclude_dirs)
                
                # Copy configuration files
                for config_file in ['pyproject.toml', 'README.md', 'LICENSE', 'requirements.txt']:
                    if (project_root / config_file).exists():
                        shutil.copy2(project_root / config_file, package_root / config_file)
                
                # 3. Create manifest
                manifest = self.create_manifest()
                with open(package_root / 'manifest.json', 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2)
                
                # 4. Create requirements.txt if it doesn't exist
                if not (package_root / 'requirements.txt').exists():
                    try:
                        subprocess.run(
                            ["poetry", "export", "-f", "requirements.txt", "--output", "requirements.txt"],
                            cwd=package_root,
                            check=True
                        )
                    except Exception as e:
                        logger.warning(f"Could not generate requirements.txt: {e}")
                
                # 5. Create the package archive
                self.package_dir.mkdir(parents=True, exist_ok=True)
                dxt_file_path = self.package_dir / f"{package_name}.dxt"
                
                # Remove existing package if it exists
                if dxt_file_path.exists():
                    dxt_file_path.unlink()
                
                # Create zip archive with all files
                shutil.make_archive(
                    str(dxt_file_path.with_suffix('')),
                    'zip',
                    root_dir=temp_path,
                    base_dir=package_name
                )
                
                # Rename .zip to .dxt
                zip_path = dxt_file_path.with_suffix('.zip')
                zip_path.rename(dxt_file_path)
                
                logger.info(f"Created complete DXT package: {dxt_file_path}")
                logger.info(f"Package size: {dxt_file_path.stat().st_size / (1024*1024):.2f} MB")
                
                return True
            
        except Exception as e:
            logger.error(f"Error creating DXT package: {e}", exc_info=True)
            return False
    
    def package(self) -> bool:
        """Main method to create the DXT package."""
        logger.info("Starting DXT packaging process...")
        
        if not self.load_config():
            logger.error("Failed to load DXT configuration")
            return False
        
        logger.info(f"Packaging {self.config['name']} v{self.version}")
        
        if not self.prepare_package():
            logger.error("Failed to prepare DXT package")
            return False
        
        logger.info("DXT packaging completed successfully")
        return True


def main() -> int:
    """Main entry point for the DXT packaging script."""
    packager = DXTPackager()
    success = packager.package()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
