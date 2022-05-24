import logging
import os
from datetime import datetime, timedelta

from aws.s3 import S3
from bs4 import BeautifulSoup
from config import BUCKET_INDEED_JOB_POSTING_ENV_KEY
from models.job_posting import update_job_posting_from_parsed_info

_DOWNLOAD_BUCKET = os.environ[BUCKET_INDEED_JOB_POSTING_ENV_KEY]

logging.getLogger().setLevel(logging.INFO)

def lambda_handler(event, context):
    # Input example: {"s3_key":"00007cb1-ff0e-467e-9e5e-ee59433ee89f"}

    logging.info('Entering Indeed Parser lambda_handler')

    object_key = event['s3_key']

    if not object_key:
        logging.warning('Received null or empty s3_key, skipping')
        return {}

    logging.info(f'Downloading file from bucket "{_DOWNLOAD_BUCKET}", object key "{object_key}"...')
    file_str = S3.download_file_str(_DOWNLOAD_BUCKET, object_key)

    parsed_job_info = _parse_job_posting(file=file_str, file_name=object_key)

    logging.info(f'Updating JobPosting data with {parsed_job_info}')

    update_job_posting_from_parsed_info(job_posting_id=object_key, **parsed_job_info)

    return {}

def _parse_job_posting(file: str, file_name: str) -> dict:
    if not file:
        logging.error(f'Received an empty file [{file_name}]')
        return

    soup = BeautifulSoup(file, 'html.parser')

    title_h1 = soup.find("h1", class_="jobsearch-JobInfoHeader-title")
    if title_h1:
        job_title = title_h1.string
    else:
        job_title = ''

    jd_div = soup.find("div", class_="jobsearch-jobDescriptionText")
    if jd_div:
        job_description = '\n'.join([x for x in jd_div.strings])
    else:
        job_description = ''

    company_div = soup.find("div", class_="jobsearch-InlineCompanyRating")
    if company_div and company_div.contents:
        company_name = next(x.string for x in company_div.contents if x.string)
    else:
        company_name = ''

    subtitle_div = soup.find("div", class_="jobsearch-JobInfoHeader-subtitle")
    if subtitle_div and subtitle_div.contents:
        location_contents = [subtitle_div.contents[-2].string]
        if subtitle_div.contents[-1].string:
            location_contents.append(subtitle_div.contents[-1].string)
        location = '/'.join(location_contents)
    else:
        location = ''

    posted_datetime = _parse_posted_datetime(soup)

    logging.info(f'Parsed data: {job_title}, {company_name}, {location}')

    return {
        'title': job_title, 
        'company_name': company_name,
        'location': location,
        'job_description': job_description,
        'posted_datetime': posted_datetime
    }

def _parse_posted_datetime(soup: BeautifulSoup) -> datetime:
    if not soup.find("div", class_="jobsearch-JobMetadataFooter"):
        return datetime.now()

    footers = soup.find("div", class_="jobsearch-JobMetadataFooter").stripped_strings
    for s in footers:
        if s.endswith(" days ago"):
            if s.replace(" days ago", "") == "30+":
                n = 30
            else:
                n = int(s.replace(" days ago", ""))
            dt = datetime.now() - timedelta(days=n)
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        if s == "1 day ago":
            dt = datetime.now() - timedelta(days=1)
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        if s == "Today":
            dt = datetime.now()
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    return datetime.now()
