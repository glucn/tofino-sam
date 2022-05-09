import logging

import boto3
from botocore.exceptions import ClientError

import config

class DynamoDB:
    """
    The client of AWS DynamoDB
    """
    _client = None

    @classmethod
    def _get_client(cls):
        if not cls._client:
            session = boto3.session.Session()
            cls._client = session.client(
                service_name='dynamodb',
                region_name=config.AWS_REGION
            )
        return cls._client

    @classmethod
    def get_item(cls, table_name: str, key_attr: dict) -> dict:
        if not table_name:
            raise ValueError(u'table_name is required')

        if not key_attr:
            raise ValueError(u'key_attr is required')

        try:
            response = cls._get_client().get_item(TableName=table_name, Key=key_attr)
        except ClientError as e:
            logging.warning(f'GetItem got error: [{e.response}]')
            raise e

        return response['Item']

    @classmethod
    def put_item(cls, table_name: str, item: dict, expression_attribute_values: dict=None) -> dict:
        if not table_name:
            raise ValueError(u'table_name is required')

        if not item:
            raise ValueError(u'item is required')

        kwargs = {
            'TableName': table_name,
            'Item': item
        }

        if expression_attribute_values:
            kwargs['ExpressionAttributeValues'] = expression_attribute_values

        try:
            response = cls._get_client().put_item(**kwargs)
        except ClientError as e:
            logging.warning('PutItem got error: [%s]/[%s]' % (e.response['Error']['Code'], e.response['Error']['Message']))
            raise e
        
        return response

    @classmethod
    def update_item(cls, table_name: str, key: dict, update_expression: str, condition_expression: str=None, expression_attribute_values: dict=None) -> dict:
        if not table_name:
            raise ValueError(u'table_name is required')

        if not key:
            raise ValueError(u'key is required')

        if not update_expression:
            raise ValueError(u'update_expression is required')

        kwargs = {
            'TableName': table_name,
            'Key': key,
            'UpdateExpression': update_expression
        }

        if condition_expression:
            kwargs['ConditionExpression'] = condition_expression

        if expression_attribute_values:
            kwargs['ExpressionAttributeValues'] = expression_attribute_values

        try:
            response = cls._get_client().update_item(**kwargs)
        except ClientError as e:
            logging.warning('UpdateItem got error: [%s]/[%s]' % (e.response['Error']['Code'], e.response['Error']['Message']))
            raise e
        
        return response

    @classmethod
    def query(cls, table_name: str, index_name: str=None, key_condition_expression: str=None, filter_expression: str=None, projection_expression: str=None, expression_attribute_values: dict=None) -> list[dict]:
        if not table_name:
            raise ValueError(u'table_name is required')

        kwargs = {
            'TableName': table_name,
        }

        if index_name:
            kwargs['IndexName'] = index_name

        if key_condition_expression:
            kwargs['KeyConditionExpression'] = key_condition_expression

        if filter_expression:
            kwargs['FilterExpression'] = filter_expression
        
        if projection_expression:
            kwargs['ProjectionExpression'] = projection_expression

        if expression_attribute_values:
            kwargs['ExpressionAttributeValues'] = expression_attribute_values

        try:
            response = cls._get_client().query(**kwargs)
        except ClientError as e:
            logging.warning('Query got error: [%s]/[%s]' % (e.response['Error']['Code'], e.response['Error']['Message']))
            raise e

        return response['Items']

    @classmethod
    def scan(cls, table_name: str, index_name: str=None, filter_expression: str=None, projection_expression: str=None, expression_attribute_values: dict = None) -> list[dict]:
        if not table_name:
            raise ValueError(u'table_name is required')

        kwargs = {
            'TableName': table_name,
        }

        if index_name:
            kwargs['IndexName'] = index_name

        if filter_expression:
            kwargs['FilterExpression'] = filter_expression
        
        if projection_expression:
            kwargs['ProjectionExpression'] = projection_expression

        if expression_attribute_values:
            kwargs['ExpressionAttributeValues'] = expression_attribute_values

        try:
            response = cls._get_client().scan(**kwargs)
        except ClientError as e:
            logging.warning('Scan got error: [%s]/[%s]' % (e.response['Error']['Code'], e.response['Error']['Message']))
            raise e

        return response['Items']
