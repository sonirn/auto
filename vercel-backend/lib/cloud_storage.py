"""Cloud storage service for Vercel serverless functions"""
import os
import boto3
import uuid
import logging
from typing import Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)

class CloudStorageService:
    """Cloudflare R2 storage service"""
    
    def __init__(self):
        self.account_id = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
        self.r2_endpoint = os.environ.get('CLOUDFLARE_R2_ENDPOINT')
        self.access_key_id = os.environ.get('R2_ACCESS_KEY_ID')
        self.secret_access_key = os.environ.get('R2_SECRET_ACCESS_KEY')
        self.bucket_name = os.environ.get('R2_BUCKET_NAME')
        
        self.s3_client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        if all([self.account_id, self.r2_endpoint, self.access_key_id, self.secret_access_key, self.bucket_name]):
            try:
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=self.r2_endpoint,
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name='auto'
                )
                logger.info("Cloudflare R2 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize R2 client: {e}")
                self.s3_client = None
        else:
            logger.warning("R2 credentials not complete, using fallback storage")
    
    def upload_file_sync(self, content: bytes, user_id: str, project_id: str, 
                        folder: str, filename: str, content_type: str) -> str:
        """Upload file to R2 storage (synchronous)"""
        try:
            if not self.s3_client:
                raise Exception("R2 client not initialized")
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
            unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
            
            # Create structured file path
            file_key = f"users/{user_id}/projects/{project_id}/{folder}/{unique_filename}"
            
            # Prepare metadata for 7-day retention
            expiration_date = datetime.utcnow() + timedelta(days=7)
            metadata = {
                'user-id': user_id,
                'project-id': project_id,
                'folder': folder,
                'original-filename': filename,
                'upload-timestamp': timestamp,
                'expires-at': expiration_date.isoformat()
            }
            
            # Upload file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=content,
                ContentType=content_type,
                Metadata=metadata
            )
            
            # Generate file URL
            file_url = f"{self.r2_endpoint}/{self.bucket_name}/{file_key}"
            logger.info(f"File uploaded successfully: {file_url}")
            
            return file_url
            
        except Exception as e:
            logger.error(f"Error uploading file to R2: {e}")
            # Fallback to local storage for development
            return self._fallback_local_storage(content, user_id, project_id, folder, filename)
    
    async def upload_file(self, content: bytes, user_id: str, project_id: str, 
                         folder: str, filename: str, content_type: str) -> str:
        """Upload file to R2 storage (async)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.upload_file_sync, 
            content, user_id, project_id, folder, filename, content_type
        )
    
    def download_file_sync(self, file_url: str) -> bytes:
        """Download file from R2 storage (synchronous)"""
        try:
            if not self.s3_client:
                raise Exception("R2 client not initialized")
            
            # Extract file key from URL
            file_key = file_url.split(f"{self.bucket_name}/")[-1]
            
            # Download file
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            return response['Body'].read()
            
        except Exception as e:
            logger.error(f"Error downloading file from R2: {e}")
            raise e
    
    async def download_file(self, file_url: str) -> bytes:
        """Download file from R2 storage (async)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.download_file_sync, 
            file_url
        )
    
    def delete_file_sync(self, file_url: str) -> bool:
        """Delete file from R2 storage (synchronous)"""
        try:
            if not self.s3_client:
                return False
            
            # Extract file key from URL
            file_key = file_url.split(f"{self.bucket_name}/")[-1]
            
            # Delete file
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            logger.info(f"File deleted successfully: {file_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from R2: {e}")
            return False
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from R2 storage (async)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.delete_file_sync, 
            file_url
        )
    
    def _fallback_local_storage(self, content: bytes, user_id: str, project_id: str, 
                               folder: str, filename: str) -> str:
        """Fallback to local storage for development"""
        import tempfile
        from pathlib import Path
        
        # Create temp directory structure
        temp_dir = Path(tempfile.gettempdir()) / "ai_video_uploads" / user_id / project_id / folder
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = filename.split('.')[-1] if '.' in filename else 'bin'
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        file_path = temp_dir / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"File saved locally (fallback): {file_path}")
        return str(file_path)
    
    def get_storage_info(self):
        """Get storage service information"""
        if self.s3_client:
            return {
                'service': 'Cloudflare R2',
                'bucket': self.bucket_name,
                'endpoint': self.r2_endpoint,
                'status': 'connected'
            }
        else:
            return {
                'service': 'Local Storage (Fallback)',
                'status': 'fallback'
            }

# Create global cloud storage service instance
cloud_storage_service = CloudStorageService()