import io
import logging

import boto3
from botocore.exceptions import ClientError

import config


class S3:
    """
    The client of AWS S3
    """
    _client = None

    @classmethod
    def _get_client(cls):
        if not cls._client:
            session = boto3.session.Session()
            cls._client = session.client(
                service_name='s3',
                region_name=config.AWS_REGION
            )
        return cls._client

    @classmethod
    def does_object_exist(cls, bucket: str, key: str) -> bool:
        """
        Check if an object exists, using head_object() API
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.head_object
        """
        if not bucket:
            raise ValueError(u'bucket is required')

        if not key:
            raise ValueError(u'key is required')

        try:
            cls._get_client().head_object(
                Bucket=bucket,
                Key=key,
            )

            return True # No error, so the object exists

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False # 404 error, so the object does not eixst

            logging.error(e)
            raise e

    @classmethod
    def download_file_str(cls, bucket: str, key: str, encoding: str = 'utf-8') -> str:
        """
        Download an object from S3 to a string.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.download_fileobj

        :param bucket:
        :param key:
        :param encoding:
        :return:
        """
        if not bucket:
            raise ValueError(u'bucket is required')

        if not key:
            raise ValueError(u'key is required')

        try:
            bytes_buffer = io.BytesIO()

            cls._get_client().download_fileobj(
                Bucket=bucket,
                Key=key,
                Fileobj=bytes_buffer
            )

            byte_value = bytes_buffer.getvalue()
            return byte_value.decode(encoding)

        except ClientError as e:
            # TODO: change back to logging.error
            logging.warning(e)
            raise e

    @classmethod
    def upload_file_obj(cls, file: object, bucket: str, key: str) -> None:
        """
        Upload a file-like object to S3.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.upload_fileobj

        :param file:
        :param bucket:
        :param key:
        :return:
        """
        if not file:
            raise ValueError(u'file is require')

        if not bucket:
            raise ValueError(u'bucket is required')

        if not key:
            raise ValueError(u'key is required')

        try:
            cls._get_client().upload_fileobj(file, bucket, key)

        except ClientError as e:
            # TODO: change back to logging.error
            logging.warning(e)
            raise e
