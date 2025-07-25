"""
DXT Packaging Script for ImmichMCP

This script handles the creation and validation of DXT packages for the ImmichMCP project.
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import hashlib

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
        """Create a manifest for the DXT package."""
        timestamp = datetime.utcnow().isoformat()
        
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
            "file_count": 1,  # Only the config file for now
            "tags": self.config.get('tags', []),
            "dependencies": self.config.get('dependencies', {})
        }
    
    def prepare_package(self) -> bool:
        """Prepare the DXT package directory and files."""
        try:
            # Create package directory
            package_name = f"{self.config['name'].lower().replace(' ', '-')}-{self.version}"
            package_path = self.package_dir / package_name
            
            if package_path.exists():
                logger.warning(f"Package directory {package_path} already exists, removing...")
                shutil.rmtree(package_path)
            
            package_path.mkdir(parents=True, exist_ok=True)
            
            # Create manifest
            manifest = self.create_manifest()
            with open(package_path / 'manifest.json', 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            # Copy DXT config
            shutil.copy2(self.config_path, package_path / 'dxt.json')
            
            # Copy README if exists
            readme_src = self.config_path.parent / 'README.md'
            if readme_src.exists():
                shutil.copy2(readme_src, package_path / 'README.md')
            
            # Create package archive
            archive_format = 'zip'  # or 'tar', 'gztar', 'bztar', 'xztar'
            archive_base_name = str(self.package_dir / package_name)
            shutil.make_archive(
                archive_base_name,
                archive_format,
                root_dir=self.package_dir,
                base_dir=package_name
            )
            
            logger.info(f"Created DXT package: {archive_base_name}.{archive_format}")
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
