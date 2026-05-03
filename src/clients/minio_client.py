import logging
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from src.core.settings import settings

logger = logging.getLogger(__name__)


class MinioClient:
    def __init__(self):
        self._client = None
        self.bucket_name = settings.MINIO_BUCKET_NAME

    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=settings.MINIO_SECURE
            )
            self._ensure_bucket_exists()
        return self._client

    def _ensure_bucket_exists(self):
        try:
            if not self._client.bucket_exists(self.bucket_name):
                self._client.make_bucket(self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created successfully")
            else:
                logger.info(f"Bucket '{self.bucket_name}' already exists")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    async def upload_file(
            self,
            file_data: BinaryIO,
            object_name: str,
            content_type: str = "application/pdf",
            metadata: dict = None
    ) -> str:
        try:
            file_size = file_data.seek(0, 2)
            file_data.seek(0)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata=metadata or {}
            )

            logger.info(f"File '{object_name}' uploaded successfully")
            return object_name

        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    async def delete_file(self, object_name: str) -> bool:
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"File '{object_name}' deleted successfully")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False


minio_client = MinioClient()
