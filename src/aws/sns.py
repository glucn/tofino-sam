import logging
import boto3
from botocore.exceptions import ClientError

import config


class SNS:
    """
    The client of AWS SNS
    """
    _client = None

    @classmethod
    def _get_client(cls):
        if not cls._client:
            session = boto3.session.Session()
            cls._client = session.client(
                service_name='sns',
                region_name=config.AWS_REGION
            )
        return cls._client

    @classmethod
    def publish(cls, target_arn, message, subject):
        try:
            cls._get_client().publish(TargetArn=target_arn, Message=message, Subject=subject)

        except ClientError as e:
            logging.error(e)
            raise e
