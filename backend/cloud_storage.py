import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os
import logging
from typing import Optional
from datetime import datetime, timedelta
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os
import logging
from typing import Optional
from datetime import datetime, timedelta
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class CloudStorageService:
    def __init__(self):
        # Load environment variables with fallbacks
        self.account_id = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
        self.bucket_name = os.environ.get('R2_BUCKET_NAME', 'video-generation-storage')
        self.access_key_id = os.environ.get('R2_ACCESS_KEY_ID')
        self.secret_access_key = os.environ.get('R2_SECRET_ACCESS_KEY')
        
        # Only initialize R2 if all credentials are available
        if not all([self.account_id, self.access_key_id, self.secret_access_key]):
            logger.warning("Missing R2 credentials, R2 will not be available")
            self.r2_client = None
            self.r2_available = False
            self.executor = None
            return
        
        # Use actual R2 credentials
        try:
            self.r2_client = boto3.client(
                's3',
                endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(signature_version='s3v4', region_name='auto')
            )
            
            # Test connection by listing buckets
            self.r2_client.list_buckets()
            self.r2_available = True
            logger.info("Successfully connected to Cloudflare R2")
            
            # Ensure bucket exists
            self._ensure_bucket_exists()
            
        except Exception as e:
            logger.error(f"R2 client initialization failed: {e}")
            self.r2_client = None
            self.r2_available = False
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4) if self.r2_available else None
    
    def _ensure_bucket_exists(self):
        """Ensure the R2 bucket exists"""
        try:
            self.r2_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"R2 bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.r2_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created R2 bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create R2 bucket: {str(create_error)}")
                    raise
            else:
                logger.error(f"Error checking R2 bucket: {str(e)}")
                raise
    
    def generate_file_key(self, user_id: str, project_id: str, file_type: str, filename: str) -> str:
        """Generate a structured file key for R2 storage"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
        clean_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        return f"users/{user_id}/projects/{project_id}/{file_type}/{clean_filename}"
    
    async def upload_file(self, file_content: bytes, user_id: str, project_id: str, 
                         file_type: str, filename: str, content_type: str) -> str:
        """Upload file to R2 or local storage"""
        if self.r2_available:
            return await self._upload_to_r2(file_content, user_id, project_id, 
                                           file_type, filename, content_type)
        else:
            return await self._upload_to_local(file_content, user_id, project_id, 
                                             file_type, filename)
    
    async def _upload_to_r2(self, file_content: bytes, user_id: str, project_id: str,
                           file_type: str, filename: str, content_type: str) -> str:
        """Upload file to Cloudflare R2"""
        try:
            file_key = self.generate_file_key(user_id, project_id, file_type, filename)
            
            # Set lifecycle tags for 7-day retention
            # Note: Tagging is not supported by Cloudflare R2, so we'll use metadata only
            # tagging = "RetentionDays=7&AutoDelete=true"
            
            # Use thread pool for upload
            def _upload():
                return self.r2_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Body=file_content,
                    ContentType=content_type,
                    # Tagging=tagging,  # Removed as not supported by Cloudflare R2
                    Metadata={
                        'user-id': user_id,
                        'project-id': project_id,
                        'file-type': file_type,
                        'upload-date': datetime.utcnow().isoformat(),
                        'expires-at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                        'retention-days': '7',
                        'auto-delete': 'true'
                    }
                )
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, _upload)
            
            # Return the full R2 URL
            r2_url = f"https://{self.account_id}.r2.cloudflarestorage.com/{self.bucket_name}/{file_key}"
            logger.info(f"Successfully uploaded to R2: {r2_url}")
            return r2_url
            
        except ClientError as e:
            logger.error(f"R2 upload failed: {e}")
            # Fallback to local storage
            return await self._upload_to_local(file_content, user_id, project_id, 
                                             file_type, filename)
    
    async def _upload_to_local(self, file_content: bytes, user_id: str, project_id: str,
                              file_type: str, filename: str) -> str:
        """Fallback: Upload file to local storage"""
        from pathlib import Path
        import aiofiles
        
        # Create directory structure
        upload_dir = Path(f"/tmp/uploads/users/{user_id}/projects/{project_id}/{file_type}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
        local_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        file_path = upload_dir / local_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"File saved locally at {file_path}")
        return str(file_path)
    
    async def get_download_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate a download URL (presigned for R2, direct for local)"""
        if self.r2_available and file_path.startswith('https://'):
            return await self._get_r2_download_url(file_path, expires_in)
        else:
            # For local files, return the path as-is (will be handled by download endpoint)
            return file_path
    
    async def _get_r2_download_url(self, r2_url: str, expires_in: int) -> str:
        """Generate presigned download URL for R2"""
        try:
            # Extract key from R2 URL
            file_key = r2_url.split(f'{self.bucket_name}/')[-1]
            
            def _generate_presigned_url():
                return self.r2_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': file_key},
                    ExpiresIn=expires_in
                )
            
            loop = asyncio.get_event_loop()
            presigned_url = await loop.run_in_executor(self.executor, _generate_presigned_url)
            
            return presigned_url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return r2_url  # Return original URL as fallback
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        if self.r2_available and file_path.startswith('https://'):
            return await self._delete_from_r2(file_path)
        else:
            return await self._delete_from_local(file_path)
    
    async def _delete_from_r2(self, r2_url: str) -> bool:
        """Delete file from R2"""
        try:
            file_key = r2_url.split(f'{self.bucket_name}/')[-1]
            
            def _delete():
                self.r2_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, _delete)
            
            logger.info(f"Successfully deleted from R2: {r2_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete from R2: {e}")
            return False
    
    async def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            from pathlib import Path
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete local file: {e}")
            return False
    
    async def cleanup_expired_files(self):
        """Clean up expired files (for local storage only, R2 handles this automatically)"""
        if not self.r2_available:
            # Implement local cleanup logic
            from pathlib import Path
            import time
            
            upload_root = Path("/tmp/uploads")
            if upload_root.exists():
                current_time = time.time()
                seven_days_ago = current_time - (7 * 24 * 60 * 60)
                
                for file_path in upload_root.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime < seven_days_ago:
                        try:
                            file_path.unlink()
                            logger.info(f"Deleted expired file: {file_path}")
                        except Exception as e:
                            logger.error(f"Failed to delete expired file {file_path}: {e}")
    
    def get_storage_info(self):
        """Get storage service information"""
        return {
            'service': 'Cloudflare R2' if self.r2_available else 'Local Storage (Fallback)',
            'bucket': self.bucket_name if self.r2_available else 'N/A',
            'account_id': self.account_id,
            'status': 'connected' if self.r2_available else 'fallback'
        }

# Global instance
cloud_storage_service = CloudStorageService()