"""
Google Cloud Storage client with local fallback
"""
import os
from pathlib import Path
from typing import Optional, List, BinaryIO
from loguru import logger

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("Google Cloud Storage libraries not available, using local storage fallback")


class GCSClient:
    """
    Google Cloud Storage client with automatic local fallback
    """
    
    def __init__(self):
        """Initialize GCS client or local storage fallback"""
        self.use_gcs = False
        self.bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.local_storage_root = Path('data/gcs_local')
        
        if GCS_AVAILABLE and self.bucket_name:
            try:
                # Try to initialize GCS client
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                
                # Test connection
                self.bucket.exists()
                self.use_gcs = True
                logger.info(f"Connected to GCS bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"Failed to connect to GCS: {e}. Using local storage.")
                self._setup_local_storage()
        else:
            logger.info("GCS not configured, using local storage")
            self._setup_local_storage()
    
    def _setup_local_storage(self):
        """Setup local storage structure"""
        self.use_gcs = False
        self.local_storage_root.mkdir(parents=True, exist_ok=True)
        
        # Create standard directories
        for subdir in ['deals', 'templates', 'logs', 'documents', 'reports']:
            (self.local_storage_root / subdir).mkdir(exist_ok=True)
        
        logger.info(f"Local storage initialized at: {self.local_storage_root}")
    
    def upload_file(
        self,
        local_path: str,
        destination_path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to GCS or local storage
        
        Args:
            local_path: Path to local file
            destination_path: Destination path in bucket
            content_type: MIME type of file
        
        Returns:
            Path to uploaded file
        """
        local_path = Path(local_path)
        
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        if self.use_gcs:
            try:
                blob = self.bucket.blob(destination_path)
                blob.upload_from_filename(str(local_path), content_type=content_type)
                logger.info(f"Uploaded to GCS: gs://{self.bucket_name}/{destination_path}")
                return f"gs://{self.bucket_name}/{destination_path}"
            except Exception as e:
                logger.error(f"GCS upload failed: {e}. Falling back to local storage.")
                return self._upload_local(local_path, destination_path)
        else:
            return self._upload_local(local_path, destination_path)
    
    def _upload_local(self, local_path: Path, destination_path: str) -> str:
        """Upload to local storage"""
        dest_path = self.local_storage_root / destination_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        import shutil
        shutil.copy2(local_path, dest_path)
        
        logger.info(f"Copied to local storage: {dest_path}")
        return str(dest_path)
    
    def download_file(
        self,
        source_path: str,
        destination_path: str
    ) -> str:
        """
        Download file from GCS or local storage
        
        Args:
            source_path: Path in bucket or local storage
            destination_path: Local destination path
        
        Returns:
            Path to downloaded file
        """
        destination_path = Path(destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.use_gcs:
            try:
                blob = self.bucket.blob(source_path)
                blob.download_to_filename(str(destination_path))
                logger.info(f"Downloaded from GCS: {source_path}")
                return str(destination_path)
            except NotFound:
                logger.error(f"File not found in GCS: {source_path}")
                raise
            except Exception as e:
                logger.error(f"GCS download failed: {e}")
                raise
        else:
            source_full_path = self.local_storage_root / source_path
            if not source_full_path.exists():
                raise FileNotFoundError(f"File not found: {source_full_path}")
            
            import shutil
            shutil.copy2(source_full_path, destination_path)
            logger.info(f"Copied from local storage: {source_path}")
            return str(destination_path)
    
    def upload_bytes(
        self,
        data: bytes,
        destination_path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload bytes directly to GCS or local storage
        
        Args:
            data: Bytes to upload
            destination_path: Destination path
            content_type: MIME type
        
        Returns:
            Path to uploaded data
        """
        if self.use_gcs:
            try:
                blob = self.bucket.blob(destination_path)
                blob.upload_from_string(data, content_type=content_type)
                logger.info(f"Uploaded bytes to GCS: {destination_path}")
                return f"gs://{self.bucket_name}/{destination_path}"
            except Exception as e:
                logger.error(f"GCS upload failed: {e}. Falling back to local storage.")
                return self._upload_bytes_local(data, destination_path)
        else:
            return self._upload_bytes_local(data, destination_path)
    
    def _upload_bytes_local(self, data: bytes, destination_path: str) -> str:
        """Upload bytes to local storage"""
        dest_path = self.local_storage_root / destination_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        dest_path.write_bytes(data)
        logger.info(f"Saved bytes to local storage: {dest_path}")
        return str(dest_path)
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in GCS or local storage
        
        Args:
            prefix: Path prefix to filter
        
        Returns:
            List of file paths
        """
        if self.use_gcs:
            try:
                blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
                return [blob.name for blob in blobs]
            except Exception as e:
                logger.error(f"Failed to list GCS files: {e}")
                return []
        else:
            search_path = self.local_storage_root / prefix if prefix else self.local_storage_root
            if not search_path.exists():
                return []
            
            files = []
            for item in search_path.rglob('*'):
                if item.is_file():
                    # Return relative path from storage root
                    rel_path = item.relative_to(self.local_storage_root)
                    files.append(str(rel_path).replace('\\', '/'))
            
            return files
    
    def delete_file(self, path: str) -> bool:
        """
        Delete file from GCS or local storage
        
        Args:
            path: Path to file
        
        Returns:
            True if deleted successfully
        """
        if self.use_gcs:
            try:
                blob = self.bucket.blob(path)
                blob.delete()
                logger.info(f"Deleted from GCS: {path}")
                return True
            except NotFound:
                logger.warning(f"File not found in GCS: {path}")
                return False
            except Exception as e:
                logger.error(f"Failed to delete from GCS: {e}")
                return False
        else:
            file_path = self.local_storage_root / path
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted from local storage: {path}")
                return True
            else:
                logger.warning(f"File not found in local storage: {path}")
                return False
    
    def get_deal_path(self, deal_id: str, category: str = "") -> str:
        """
        Get standardized path for deal files
        
        Args:
            deal_id: Deal identifier
            category: Category (documents, reports, analysis)
        
        Returns:
            Path string
        """
        if category:
            return f"deals/{deal_id}/{category}"
        return f"deals/{deal_id}"
    
    def file_exists(self, path: str) -> bool:
        """
        Check if file exists
        
        Args:
            path: Path to check
        
        Returns:
            True if exists
        """
        if self.use_gcs:
            try:
                blob = self.bucket.blob(path)
                return blob.exists()
            except Exception:
                return False
        else:
            return (self.local_storage_root / path).exists()


# Global client instance
_gcs_client: Optional[GCSClient] = None


def get_gcs_client() -> GCSClient:
    """
    Get global GCS client instance
    
    Returns:
        GCSClient instance
    """
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = GCSClient()
    return _gcs_client
