"""Cloud storage utilities for Vercel serverless functions"""
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CloudStorageService:
    """Cloudflare R2 storage service for Vercel (synchronous)"""
    
    def __init__(self):
        self.account_id = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
        self.r2_endpoint = os.environ.get('CLOUDFLARE_R2_ENDPOINT')
        self.access_key_id = os.environ.get('R2_ACCESS_KEY_ID')
        self.secret_access_key = os.environ.get('R2_SECRET_ACCESS_KEY')
        self.bucket_name = os.environ.get('R2_BUCKET_NAME')
        
        self.client = None
        
        # Initialize S3 client for R2
        self._init_client()
    
    def _init_client(self):
        """Initialize S3 client for Cloudflare R2"""
        try:
            if not all([self.account_id, self.access_key_id, self.secret_access_key, self.bucket_name]):
                raise ValueError("Missing required R2 credentials")
                
            self.client = boto3.client(
                's3',
                endpoint_url=self.r2_endpoint,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='auto'
            )
            
            logger.info(f"R2 client initialized for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize R2 client: {e}")
            raise
    
    def upload_file_sync(self, content: bytes, user_id: str, project_id: str, 
                        folder: str, filename: str, content_type: str) -> str:
        """Upload file to Cloudflare R2 (synchronous)"""
        try:
            # Create structured path
            file_path = f"users/{user_id}/projects/{project_id}/{folder}/{filename}"
            
            # Add metadata for 7-day retention
            metadata = {
                'retention-days': '7',
                'uploaded-at': str(__import__('time').time())
            }
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=content,
                ContentType=content_type,
                Metadata=metadata
            )
            
            # Return R2 URL
            file_url = f"{self.r2_endpoint}/{file_path}"
            logger.info(f"File uploaded to R2: {file_url}")
            
            return file_url
            
        except Exception as e:
            logger.error(f"R2 upload failed: {e}")
            raise
    
    async def upload_file(self, content: bytes, user_id: str, project_id: str, 
                         folder: str, filename: str, content_type: str) -> str:
        """Upload file to Cloudflare R2 (async wrapper)"""
        return self.upload_file_sync(content, user_id, project_id, folder, filename, content_type)
    
    def download_file_sync(self, file_url: str) -> bytes:
        """Download file from R2 (synchronous)"""
        try:
            # Extract file path from URL
            file_path = file_url.replace(f"{self.r2_endpoint}/", "")
            
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            
            return response['Body'].read()
            
        except Exception as e:
            logger.error(f"R2 download failed: {e}")
            raise
    
    async def download_file(self, file_url: str) -> bytes:
        """Download file from R2 (async wrapper)"""
        return self.download_file_sync(file_url)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage service information"""
        return {
            "service": "Cloudflare R2",
            "bucket": self.bucket_name,
            "account_id": self.account_id,
            "status": "connected" if self.client else "disconnected"
        }

# Global storage service instance
cloud_storage_service = CloudStorageService()