"""AWS S3 service for file operations."""

import boto3
import os
from botocore.exceptions import ClientError
from ..core.config import settings

class S3Service:
    """Service for AWS S3 file operations."""
    
    def __init__(self):
        """Initialize S3 client with AWS credentials from environment."""
        if not all([settings.aws_access_key_id, settings.aws_secret_access_key, settings.s3_bucket_name]):
            print("S3 credentials not fully configured")
            self.s3_client = None
            return
            
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.bucket_name = settings.s3_bucket_name
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download file from S3 to local path.
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save
            
        Returns:
            True if download successful, False otherwise
        """
        if not self.s3_client:
            return False
            
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except ClientError as e:
            print(f"S3 download failed: {e}")
            return False
    
    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """Upload local file to S3.
        
        Args:
            local_path: Local file path
            s3_key: S3 object key
            
        Returns:
            True if upload successful, False otherwise
        """
        if not self.s3_client:
            return False
            
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            return True
        except ClientError as e:
            print(f"S3 upload failed: {e}")
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.s3_client:
            return False
            
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

s3_service = S3Service()