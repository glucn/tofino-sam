import logging
import os
from io import BytesIO
from urllib.parse import parse_qs, urlparse, urlunparse

from aws.s3 import S3
from config import BUCKET_INDEED_JOB_POSTING_ENV_KEY
from crawler.proxies_manager import ProxiesManager
from exceptions.exceptions import MalFormedMessageException, RetryableException
from models.job_posting import (create_job_posting,
                                get_job_posting_by_external_id,
                                get_job_posting_by_origin_url,
                                update_job_posting_origin_url)

_SOURCE = 'ca.indeed.com'
_UPLOAD_BUCKET = os.environ[BUCKET_INDEED_JOB_POSTING_ENV_KEY]

logging.getLogger().setLevel(logging.INFO)

def lambda_handler(event, context):
    # Input: {"url":"https://ca.indeed.com/rc/clk?jk=1b9d06ebdd34033a&fccid=3002307a9e5b4706&vjs=3"}

    logging.info("Entering Indeed Downloader lambda_handler")
    
    url = _parse_event(event)
    logging.info(f'Parsed url {url}')

    if not _should_download(url):
        return

    content, redirected_url = ProxiesManager().crawl(url)

    s3_key = _process_response(url, redirected_url, content)
    
    result = {
        "s3_key": s3_key
    }
    return result

def _parse_event(event) -> str:
    """
    Parse the event
    """
    if 'url' not in event:
        raise MalFormedMessageException(f'Message {event} is malformed')

    return event['url']

def _should_download(url: str) -> bool:
    existing = get_job_posting_by_origin_url(url)

    if existing:
        logging.info(f'The Job Posting of {url} already exist, skipping...')
        return False

    return True

def _process_response(origin_url: str, final_url: str, content: str) -> str:
    if bool(urlparse(final_url).netloc) and 'indeed' not in final_url:
        logging.warning(f'Redirected to unsupported URL {final_url}, discarding...')
        return

    source = _SOURCE
    external_id = _parse_external_id(final_url)

    if not external_id:
        logging.warning(f'Cannot determine external ID from the URL {final_url}, discarding...')
        return

    try:
        existing = get_job_posting_by_external_id(external_id)
        if existing:
            # TODO: consider updating existing record?
            logging.info(
                f'JobPosting record with source "{source}" external_id "{external_id}" already exists')

            if not existing.origin_url:
                logging.info(f'Updating JobPosting record [{existing.id}] with origin_url [{origin_url}]')
                update_job_posting_origin_url(job_posting_id=existing.id, origin_url=origin_url)

            return

        logging.info(f'Creating new JobPosting...')

        job_posting = create_job_posting(
            source=source,
            external_id=external_id,
            url=_prepend_netloc_to_relative_url(final_url),
            origin_url=origin_url,
        )

        file_key = job_posting.id
        logging.info(f'Uploading file to "{_UPLOAD_BUCKET}/{file_key}"...')
        S3.upload_file_obj(BytesIO(content.encode('utf-8')), _UPLOAD_BUCKET, file_key)
        logging.info(f'Uploaded file to "{_UPLOAD_BUCKET}/{file_key}"')

        logging.info(f'Created JobPosting record {job_posting.id}')
        return file_key

    except Exception as ex:
        logging.error('Error processing the downloaded content')
        logging.exception(ex)
        raise RetryableException(ex)


def _parse_external_id(url: str) -> str:
    parsed_url = urlparse(url)
    queries = parse_qs(parsed_url.query)
    if 'jk' in queries:
        return queries['jk'][0]
    return ''

def _prepend_netloc_to_relative_url(url: str) -> str:
    parsed_url = urlparse(url)
    if bool(parsed_url.netloc):
        return url

    return urlunparse(parsed_url._replace(netloc=_SOURCE, scheme='https'))
