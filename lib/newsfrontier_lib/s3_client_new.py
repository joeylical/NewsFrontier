"""
Enhanced S3 Client for NewsFrontier - Database-configurable S3 operations.

This module provides S3 upload and download functionality with configuration
stored in the database and encrypted credential storage.
"""

import logging
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import uuid
from datetime import datetime

from .config_service import get_config, ConfigKeys

logger = logging.getLogger(__name__)


class EnhancedS3Client:
    """Enhanced S3 client with database configuration and encrypted credentials."""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup S3 client with database configuration."""
        try:
            # Get configuration from database (with fallback to environment)
            region = self.config.get(ConfigKeys.S3_REGION, fallback_env=True)
            endpoint = self.config.get_encrypted(ConfigKeys.S3_ENDPOINT, fallback_env=True)
            bucket = self.config.get(ConfigKeys.S3_BUCKET, fallback_env=True)
            access_key = self.config.get_encrypted(ConfigKeys.S3_ACCESS_KEY_ID, fallback_env=True)
            secret_key = self.config.get_encrypted(ConfigKeys.S3_SECRET_KEY, fallback_env=True)
            
            if not all([region, endpoint, bucket, access_key, secret_key]):
                logger.warning("S3 configuration incomplete, S3 operations will not be available")
                logger.debug(f"S3 config status - region: {'✓' if region else '✗'}, "
                           f"endpoint: {'✓' if endpoint else '✗'}, "
                           f"bucket: {'✓' if bucket else '✗'}, "
                           f"access_key: {'✓' if access_key else '✗'}, "
                           f"secret_key: {'✓' if secret_key else '✗'}")
                return
            
            # Configure S3 client
            self.client = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Test connection
            self.client.head_bucket(Bucket=bucket)
            logger.info("Enhanced S3 client initialized successfully")
            
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
    
    def get_bucket_name(self) -> Optional[str]:
        """Get the configured bucket name."""
        return self.config.get(ConfigKeys.S3_BUCKET, fallback_env=True)
    
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
        
        bucket = self.get_bucket_name()
        if not bucket:
            logger.error("S3 bucket not configured")
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
                Bucket=bucket,
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
        
        bucket = self.get_bucket_name()
        if not bucket:
            logger.error("S3 bucket not configured")
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': s3_key},
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
        
        bucket = self.get_bucket_name()
        if not bucket:
            logger.error("S3 bucket not configured")
            return False
        
        try:
            self.client.delete_object(Bucket=bucket, Key=s3_key)
            logger.info(f"Successfully deleted image from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected delete error: {e}")
            return False
    
    def list_images(self, prefix: str = "covers/", max_keys: int = 100) -> List[str]:
        """
        List images in S3 bucket with given prefix.
        
        Args:
            prefix: S3 key prefix to filter by
            max_keys: Maximum number of keys to return
            
        Returns:
            List of S3 keys
        """
        if not self.is_available():
            logger.error("S3 client not available")
            return []
        
        bucket = self.get_bucket_name()
        if not bucket:
            logger.error("S3 bucket not configured")
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []
                
        except ClientError as e:
            logger.error(f"S3 list failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected list error: {e}")
            return []


# Global instance for easy access
enhanced_s3_client = EnhancedS3Client()


def get_enhanced_s3_client() -> EnhancedS3Client:
    """Get the global enhanced S3 client instance."""
    return enhanced_s3_client


def upload_cover_image(image_data: bytes, date_str: str) -> Optional[str]:
    """Upload cover image with date-based naming."""
    filename = f"covers/daily_cover_{date_str}.png"
    return enhanced_s3_client.upload_image(image_data, filename)


def get_cover_image_url(s3_key: str) -> Optional[str]:
    """Get presigned URL for cover image."""
    return enhanced_s3_client.get_image_url(s3_key, expires_in=7200)  # 2 hours