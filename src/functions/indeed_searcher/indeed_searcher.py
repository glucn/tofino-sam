from datetime import datetime
from random import randint
from uuid import uuid4


def lambda_handler(event, context):

    # TODO: fetch the search result page
    # TODO: parse it

    # Mocked result of a job search result
    result = {
        "job_postings": [
            {"url": "https://example.com/1"},
            {"url": "https://example.com/2"}
        ]  # Urls of job postings
    }
    return result
