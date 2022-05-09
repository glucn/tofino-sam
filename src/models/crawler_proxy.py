import os
from datetime import datetime

from aws.dynamo_db import DynamoDB
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from config import DYNAMODB_TABLE_CRAWLER_PROXY_ENV_KEY

_CRAWLER_PROXY_TABLE_NAME = os.environ[DYNAMODB_TABLE_CRAWLER_PROXY_ENV_KEY]

class CrawlerProxy():
    """ Data model of crawler proxy """
    id: str
    region: str
    arn: str
    deactivated_epoch_second: int
    deactivated_count: int

    def __init__(self, dynamo_object):
        deserializer = TypeDeserializer()

        self.id = deserializer.deserialize(dynamo_object.get('Id'))
        self.region = deserializer.deserialize(dynamo_object.get('Region'))
        self.arn = deserializer.deserialize(dynamo_object.get('Arn'))
        self.deactivated_epoch_second = int(deserializer.deserialize(dynamo_object.get('DeactivatedEpochSecond')))
        self.deactivated_count = int(deserializer.deserialize(dynamo_object.get('DeactivatedCount')))


def get_crawler_proxy(proxy_id: str):
    ddb_item = DynamoDB.get_item(table_name=_CRAWLER_PROXY_TABLE_NAME, key_attr={'Id': proxy_id})
    return CrawlerProxy(ddb_item)

def list_active_crawler_proxy(last_deactivate_datetime: datetime):
    serializer = TypeSerializer()

    filter_expression = 'DeactivatedEpochSecond < :last_deactivate'
    attribute_values = {':last_deactivate': serializer.serialize(int(last_deactivate_datetime.timestamp()))}

    ddb_items = DynamoDB.scan(
        table_name=_CRAWLER_PROXY_TABLE_NAME,
        filter_expression=filter_expression,
        expression_attribute_values=attribute_values
    )

    return [CrawlerProxy(ddb_item) for ddb_item in ddb_items]

def deactivate_crawler_proxy(proxy_id) -> None:
    serializer = TypeSerializer()

    expression = (
        'SET '
        'DeactivatedEpochSecond = :deactivatedEpochSecond, '
        'DeactivatedCount = DeactivatedCount + :inc, '
        'UpdatedDatetime = :now'
    )

    attribute_values = {
        ':proxy_id': serializer.serialize(proxy_id),
        ':deactivatedEpochSecond': serializer.serialize(int(datetime.now().timestamp())),
        ':inc': serializer.serialize(1),
        ':now': serializer.serialize(datetime.now().isoformat())
    }

    DynamoDB.update_item(
        table_name=_CRAWLER_PROXY_TABLE_NAME,
        key={'Id': serializer.serialize(proxy_id)},
        update_expression=expression,
        expression_attribute_values=attribute_values,
        condition_expression='Id = :proxy_id' # Only update when the Id exists
    )
