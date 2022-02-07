from datetime import datetime
from random import randint
from uuid import uuid4


def lambda_handler(event, context):
    
    # TODO: fetch the job posting from S3
    # TODO: parse the info and store in DB

    object_key = event['s3_key']
    
    return {}
