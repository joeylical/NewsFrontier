"""
S3 Client for NewsFrontier - S3 storage operations.

This module provides S3 upload and download functionality for storing
cover images and other assets.
"""

import os
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client for uploading and managing files."""
    
    def __init__(self):
        self.region = os.getenv('S3API_REGION')
        self.endpoint = os.getenv('S3API_ENDPOINT')
        self.bucket = os.getenv('S3API_BUCKET')
        self.access_key = os.getenv('S3API_KEY_ID')
        self.secret_key = os.getenv('S3API_KEY')
        
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup S3 client with configuration."""
        if not all([self.region, self.endpoint, self.bucket, self.access_key, self.secret_key]):
            logger.warning("S3 configuration incomplete, S3 operations will not be available")
            return
        
        try:
            # Configure S3 client
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            # Test connection
            self.client.head_bucket(Bucket=self.bucket)
            logger.info("S3 client initialized successfully")
            
        except NoCredentialsError:
            logger.error("S3 credentials not found")
            self.client = None
        except ClientError as e:
            logger.error(f"S3 setup failed: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected S3 setup error: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if S3 client is available."""
        return self.client is not None
    
    def upload_image(self, image_data: bytes, filename: str = None, content_type: str = "image/png") -> Optional[str]:
        """
        Upload image to S3 and return the S3 key.
        
        Args:
            image_data: Binary image data
            filename: Optional filename, will generate UUID if not provided
            content_type: MIME type of the image
            
        Returns:
            S3 key of uploaded file or None if failed
        """
        if not self.is_available():
            logger.error("S3 client not available")
            return None
        
        if not image_data:
            logger.error("No image data provided")
            return None
        
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]
                filename = f"covers/{timestamp}_{unique_id}.png"
            
            # Ensure filename has covers/ prefix
            if not filename.startswith('covers/'):
                filename = f"covers/{filename}"
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=image_data,
                ContentType=content_type,
                Metadata={
                    'uploaded_at': datetime.now().isoformat(),
                    'source': 'newsfrontier_cover_generator'
                }
            )
            
            logger.info(f"Successfully uploaded image to S3: {filename}")
            return filename
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            return None
    
    def get_image_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for accessing image.
        
        Args:
            s3_key: S3 key of the image
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if failed
        """
        if not self.is_available():
            logger.error("S3 client not available")
            return None
        
        if not s3_key:
            logger.error("No S3 key provided")
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected URL generation error: {e}")
            return None
    
    def delete_image(self, s3_key: str) -> bool:
        """
        Delete image from S3.
        
        Args:
            s3_key: S3 key of the image to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.error("S3 client not available")
            return False
        
        if not s3_key:
            logger.error("No S3 key provided")
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"Successfully deleted image from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected delete error: {e}")
            return False


# Global instance for easy access
s3_client = S3Client()


def get_s3_client() -> S3Client:
    """Get the global S3 client instance."""
    return s3_client


def upload_cover_image(image_data: bytes, date_str: str) -> Optional[str]:
    """Upload cover image with date-based naming."""
    filename = f"covers/daily_cover_{date_str}.png"
    return s3_client.upload_image(image_data, filename)


def get_cover_image_url(s3_key: str) -> Optional[str]:
    """Get presigned URL for cover image."""
    return s3_client.get_image_url(s3_key, expires_in=7200)  # 2 hours