"""
Google Cloud Storage adapter for persistent data
Stores conversations and bot configs in GCS
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not installed. Using local storage fallback.")


class GCSStorage:
    """Handles persistent storage in Google Cloud Storage"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize GCS storage
        
        Args:
            bucket_name: GCS bucket name (defaults to env var GCS_BUCKET_NAME)
        """
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME')
        self.use_gcs = GCS_AVAILABLE and self.bucket_name
        
        if self.use_gcs:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"✅ GCS Storage initialized: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize GCS: {e}")
                self.use_gcs = False
                logger.info("Falling back to local storage")
        else:
            logger.info("Using local storage (GCS not configured)")
            
        # Local fallback directory
        self.local_dir = os.path.join(os.path.dirname(__file__), 'local_storage')
        os.makedirs(self.local_dir, exist_ok=True)
    
    def save_json(self, path: str, data: dict):
        """Save JSON data to GCS or local storage"""
        try:
            json_str = json.dumps(data, indent=2)
            
            if self.use_gcs:
                blob = self.bucket.blob(path)
                blob.upload_from_string(json_str, content_type='application/json')
                logger.debug(f"Saved to GCS: {path}")
            else:
                local_path = os.path.join(self.local_dir, path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'w') as f:
                    f.write(json_str)
                logger.debug(f"Saved locally: {local_path}")
                
        except Exception as e:
            logger.error(f"Error saving {path}: {e}")
            raise
    
    def load_json(self, path: str) -> Optional[dict]:
        """Load JSON data from GCS or local storage"""
        try:
            if self.use_gcs:
                blob = self.bucket.blob(path)
                if blob.exists():
                    json_str = blob.download_as_string()
                    return json.loads(json_str)
                else:
                    logger.debug(f"File not found in GCS: {path}")
                    return None
            else:
                local_path = os.path.join(self.local_dir, path)
                if os.path.exists(local_path):
                    with open(local_path, 'r') as f:
                        return json.load(f)
                else:
                    logger.debug(f"File not found locally: {local_path}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return None
    
    def save_sqlite_db(self, db_path: str, gcs_path: str):
        """Upload SQLite database to GCS"""
        try:
            if self.use_gcs and os.path.exists(db_path):
                blob = self.bucket.blob(gcs_path)
                blob.upload_from_filename(db_path)
                logger.info(f"Uploaded DB to GCS: {gcs_path}")
            else:
                logger.debug(f"DB not uploaded (GCS disabled or file missing): {db_path}")
                
        except Exception as e:
            logger.error(f"Error uploading DB {db_path}: {e}")
    
    def load_sqlite_db(self, gcs_path: str, local_path: str):
        """Download SQLite database from GCS"""
        try:
            if self.use_gcs:
                blob = self.bucket.blob(gcs_path)
                if blob.exists():
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    blob.download_to_filename(local_path)
                    logger.info(f"Downloaded DB from GCS: {gcs_path}")
                    return True
                else:
                    logger.debug(f"DB not found in GCS: {gcs_path}")
                    return False
            else:
                logger.debug("GCS disabled, using local DB")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading DB {gcs_path}: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """List files in GCS bucket with given prefix"""
        try:
            if self.use_gcs:
                blobs = self.bucket.list_blobs(prefix=prefix)
                return [blob.name for blob in blobs]
            else:
                # List local files
                local_prefix = os.path.join(self.local_dir, prefix)
                if os.path.exists(local_prefix):
                    return [os.path.join(prefix, f) for f in os.listdir(local_prefix)]
                return []
                
        except Exception as e:
            logger.error(f"Error listing files with prefix {prefix}: {e}")
            return []
    
    def backup_directory(self, local_dir: str, gcs_prefix: str):
        """Backup entire directory to GCS"""
        try:
            if not self.use_gcs:
                logger.debug(f"GCS disabled, skipping backup of {local_dir}")
                return False
                
            if not os.path.exists(local_dir):
                logger.warning(f"Directory not found: {local_dir}")
                return False
            
            import shutil
            import tempfile
            
            # Create a tar.gz of the directory
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
                tmp_path = tmp.name
            
            shutil.make_archive(tmp_path.replace('.tar.gz', ''), 'gztar', local_dir)
            
            # Upload to GCS
            blob = self.bucket.blob(f"{gcs_prefix}.tar.gz")
            blob.upload_from_filename(tmp_path)
            
            # Clean up temp file
            os.remove(tmp_path)
            
            logger.info(f"✅ Backed up {local_dir} to GCS: {gcs_prefix}.tar.gz")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up directory {local_dir}: {e}")
            return False
    
    def restore_directory(self, gcs_prefix: str, local_dir: str):
        """Restore directory from GCS"""
        try:
            if not self.use_gcs:
                logger.debug(f"GCS disabled, skipping restore of {gcs_prefix}")
                return False
            
            import shutil
            import tempfile
            
            blob = self.bucket.blob(f"{gcs_prefix}.tar.gz")
            
            if not blob.exists():
                logger.info(f"No backup found in GCS: {gcs_prefix}.tar.gz")
                return False
            
            # Download to temp file
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
                tmp_path = tmp.name
            
            blob.download_to_filename(tmp_path)
            
            # Extract
            os.makedirs(os.path.dirname(local_dir), exist_ok=True)
            shutil.unpack_archive(tmp_path, local_dir, 'gztar')
            
            # Clean up temp file
            os.remove(tmp_path)
            
            logger.info(f"✅ Restored {gcs_prefix} from GCS to {local_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring directory {gcs_prefix}: {e}")
            return False


# Global storage instance
gcs_storage = GCSStorage()


