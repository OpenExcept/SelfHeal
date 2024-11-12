import boto3
import logging
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

class S3Storage:
    """A service class for interacting with AWS S3."""
    
    def __init__(self):
        """Initialize the S3 client."""
        self.s3_client = boto3.client('s3')
    
    def put_object(self, bucket_name: str, file_path: Union[str, Path], s3_key: str) -> bool:
        """
        Upload a file to S3.
        
        Args:
            bucket_name (str): The name of the S3 bucket
            file_path (Union[str, Path]): Local path to the file to upload
            s3_key (str): The key (path) where the file will be stored in S3
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            file_path = str(file_path)  # Convert Path to string if necessary
            self.s3_client.upload_file(file_path, bucket_name, s3_key)
            logger.info(f"Successfully uploaded {file_path} to s3://{bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            return False
    
    def get_object(self, bucket_name: str, s3_key: str, local_path: Union[str, Path]) -> bool:
        """
        Download a file from S3.
        
        Args:
            bucket_name (str): The name of the S3 bucket
            s3_key (str): The key (path) of the file in S3
            local_path (Union[str, Path]): Local path where the file should be saved
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            local_path = str(local_path)  # Convert Path to string if necessary
            self.s3_client.download_file(bucket_name, s3_key, local_path)
            logger.info(f"Successfully downloaded s3://{bucket_name}/{s3_key} to {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {str(e)}")
            return False
    
    def delete_object(self, bucket_name: str, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            bucket_name (str): The name of the S3 bucket
            s3_key (str): The key (path) of the file to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted s3://{bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {str(e)}")
            return False
    
    def list_objects(self, bucket_name: str, prefix: Optional[str] = None) -> list:
        """
        List objects in an S3 bucket, optionally under a specific prefix.
        
        Args:
            bucket_name (str): The name of the S3 bucket
            prefix (Optional[str]): The prefix to filter objects (like a folder path)
            
        Returns:
            list: List of object keys in the bucket
        """
        try:
            if prefix:
                response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            else:
                response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
            
        except ClientError as e:
            logger.error(f"Failed to list objects in S3: {str(e)}")
            return []