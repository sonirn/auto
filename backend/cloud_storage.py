import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os
import logging
from typing import Optional
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class CloudStorageService:
    def __init__(self):
        self.account_id = os.environ['CLOUDFLARE_ACCOUNT_ID']
        self.bucket_name = os.environ.get('R2_BUCKET_NAME', 'video-generation-storage')
        
        # For now, we'll use a fallback since we don't have the actual R2 keys
        # This allows the app to continue working while we get proper credentials
        try:
            self.r2_client = boto3.client(
                's3',
                endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID', 'fallback'),
                aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY', 'fallback'),
                config=Config(signature_version='s3v4', region_name='auto')
            )
            self.r2_available = True
        except Exception as e:
            logger.warning(f"R2 client initialization failed, using local storage fallback: {e}")
            self.r2_client = None
            self.r2_available = False
    
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
            tagging = "RetentionDays=7&AutoDelete=true"
            
            self.r2_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=content_type,
                Tagging=tagging,
                Metadata={
                    'user-id': user_id,
                    'project-id': project_id,
                    'file-type': file_type,
                    'upload-date': datetime.utcnow().isoformat(),
                    'expires-at': (datetime.utcnow() + timedelta(days=7)).isoformat()
                }
            )
            
            # Return the full R2 URL
            return f"https://{self.account_id}.r2.cloudflarestorage.com/{self.bucket_name}/{file_key}"
            
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
            
            presigned_url = self.r2_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expires_in
            )
            
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
            
            self.r2_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
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

# Global instance
cloud_storage_service = CloudStorageService()