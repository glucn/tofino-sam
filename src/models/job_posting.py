from __future__ import annotations
import logging

import os
import uuid
from datetime import datetime

from aws.dynamo_db import DynamoDB
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from config import DYNAMODB_TABLE_JOB_POSTING_ENV_KEY

_JOB_POSTING_TABLE_NAME = os.environ[DYNAMODB_TABLE_JOB_POSTING_ENV_KEY]


class JobPosting():
    """ Data model of Job Postings """
    id: str
    external_id: str
    url: str
    origin_url: str
    source: str
    title: str
    # company_id: str
    company_name: str
    location: str
    job_description: str
    posted_datetime: datetime
    created_datetime: datetime
    updated_datetime: datetime

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def to_dynamo_object(self) -> dict:
        serializer = TypeSerializer()
        ddb_item = {
            'Id': serializer.serialize(self.id)
            }

        if hasattr(self, 'external_id') and self.external_id:
            ddb_item['ExternalId'] = serializer.serialize(self.external_id)

        if hasattr(self, 'url') and self.url:
            ddb_item['Url'] = serializer.serialize(self.url)

        if hasattr(self, 'origin_url') and self.origin_url:
            ddb_item['OriginUrl'] = serializer.serialize(self.origin_url)

        if hasattr(self, 'source') and self.source:
            ddb_item['Source'] = serializer.serialize(self.source)

        if hasattr(self, 'title') and self.title:
            ddb_item['Title'] = serializer.serialize(self.title)
        
        if hasattr(self, 'company_name') and self.company_name:
            ddb_item['company_name'] = serializer.serialize(self.company_name)

        if hasattr(self, 'location') and self.location:
            ddb_item['LocationString'] = serializer.serialize(self.location)

        if hasattr(self, 'job_description') and self.job_description:
            ddb_item['JobDescription'] = serializer.serialize(self.job_description)

        if hasattr(self, 'posted_datetime') and self.posted_datetime:
            ddb_item['PostedDatetime'] = serializer.serialize(self.posted_datetime.isoformat())

        if hasattr(self, 'created_datetime') and self.created_datetime:
            ddb_item['CreatedDatetime'] = serializer.serialize(self.created_datetime.isoformat())

        if hasattr(self, 'updated_datetime') and self.updated_datetime:
            ddb_item['UpdatedDatetime'] = serializer.serialize(self.updated_datetime.isoformat())

        return ddb_item


    @classmethod
    def from_dynamo_object(cls, dynamo_object: dict) -> JobPosting:
        deserializer = TypeDeserializer()

        kwargs = {
            'id': deserializer.deserialize(dynamo_object.get('Id'))
        }

        kwargs['external_id'] = deserializer.deserialize(dynamo_object.get('ExternalId', {'S': ''}))
        kwargs['url'] = deserializer.deserialize(dynamo_object.get('Url', {'S': ''}))
        kwargs['origin_url'] = deserializer.deserialize(dynamo_object.get('OriginUrl', {'S': ''}))
        kwargs['source'] = deserializer.deserialize(dynamo_object.get('Source', {'S': ''}))
        kwargs['title'] = deserializer.deserialize(dynamo_object.get('Title', {'S': ''}))
        kwargs['company_name'] = deserializer.deserialize(dynamo_object.get('CompanyName', {'S': ''}))
        kwargs['location'] = deserializer.deserialize(dynamo_object.get('LocationString', {'S': ''}))
        kwargs['job_description'] = deserializer.deserialize(dynamo_object.get('JobDescription', {'S': ''}))
        kwargs['posted_datetime'] = datetime.fromisoformat(deserializer.deserialize(dynamo_object.get('PostedDatetime', {'S': '1970-01-01T00:00:00.000000'})))
        kwargs['created_datetime'] = datetime.fromisoformat(deserializer.deserialize(dynamo_object.get('CreatedDatetime', {'S': '1970-01-01T00:00:00.000000'})))
        kwargs['updated_datetime'] = datetime.fromisoformat(deserializer.deserialize(dynamo_object.get('UpdatedDatetime', {'S': '1970-01-01T00:00:00.000000'})))

        return cls(**kwargs)

def get_job_posting(job_posting_id: str) -> JobPosting:
    ddb_item = DynamoDB.get_item(table_name=_JOB_POSTING_TABLE_NAME, key_attr={'Id': job_posting_id})
    if ddb_item:
        return JobPosting.from_dynamo_object(ddb_item)
    else:
        return None

def get_job_posting_by_external_id(external_id: str) -> JobPosting:
    serializer = TypeSerializer()

    ddb_items = DynamoDB.query(
        table_name=_JOB_POSTING_TABLE_NAME,
        index_name='Index_ExternalId',   
        key_condition_expression='ExternalId = :externalId',
        expression_attribute_values={':externalId': serializer.serialize(external_id)}
    )
    if ddb_items:
        return JobPosting.from_dynamo_object(ddb_items[0])
    else:
        return None

def get_job_posting_by_origin_url(origin_url: str) -> JobPosting:
    serializer = TypeSerializer()

    ddb_items = DynamoDB.query(
        table_name=_JOB_POSTING_TABLE_NAME,
        index_name='Index_OriginUrl',
        key_condition_expression='OriginUrl = :originUrl',
        expression_attribute_values={':originUrl': serializer.serialize(origin_url)}
    )
    if ddb_items:
        return JobPosting.from_dynamo_object(ddb_items[0])
    else:
        return None

def create_job_posting(**kwargs) -> JobPosting:
    if 'id' not in kwargs:
        kwargs['id'] = str(uuid.uuid4())

    job_posting = JobPosting(**kwargs)
    job_posting.created_datetime = datetime.now()

    logging.info(f"Creating JobPosting {job_posting}")

    DynamoDB.put_item(
        table_name=_JOB_POSTING_TABLE_NAME,
        item=job_posting.to_dynamo_object()
    )

    return job_posting

def update_job_posting_origin_url(job_posting_id: str, origin_url: str) -> None:
    serializer = TypeSerializer()

    expression = (
        'SET '
        'OriginUrl = :originUrl,'
        'UpdatedDatetime = :now'
    )

    attribute_values = {
        ':job_posting_id': serializer.serialize(job_posting_id),
        ':originUrl': serializer.serialize(origin_url),
        ':now': serializer.serialize(datetime.now().isoformat())
    }

    DynamoDB.update_item(
        table_name=_JOB_POSTING_TABLE_NAME,
        key={'Id': serializer.serialize(job_posting_id)},
        update_expression=expression,
        expression_attribute_values=attribute_values,
        condition_expression='Id = :job_posting_id' # Only update when the Id exists
    )


def update_job_posting_from_parsed_info(job_posting_id: str, **kwargs) -> None:
    serializer = TypeSerializer()

    expression = 'SET '

    attribute_values = {
        ':job_posting_id': serializer.serialize(job_posting_id),
        ':now': serializer.serialize(datetime.now().isoformat())
    }

    if 'title' in kwargs:
        expression += 'Title = :title, '
        attribute_values[':title'] = serializer.serialize(kwargs['title'])

    if 'company_name' in kwargs:
        expression += 'CompanyName = :companyName, '
        attribute_values[':companyName'] = serializer.serialize(kwargs['company_name'])

    if 'location' in kwargs:
        expression += 'LocationString = :location, '
        attribute_values[':location'] = serializer.serialize(kwargs['location'])

    if 'job_description' in kwargs:
        expression += 'JobDescription = :jobDescription, '
        attribute_values[':jobDescription'] = serializer.serialize(_cleansing_string(kwargs['job_description']))

    if 'posted_datetime' in kwargs:
        expression += 'PostedDatetime = :postedDatetime, '
        attribute_values[':postedDatetime'] = serializer.serialize(kwargs['posted_datetime'].isoformat())

    expression += 'UpdatedDatetime = :now'

    DynamoDB.update_item(
        table_name=_JOB_POSTING_TABLE_NAME,
        key={'Id': serializer.serialize(job_posting_id)},
        update_expression=expression,
        expression_attribute_values=attribute_values,
        condition_expression='Id = :job_posting_id' # Only update when the Id exists
    )

def _cleansing_string(content: str) -> str:
    return content.replace(u'\ufeff', '')
