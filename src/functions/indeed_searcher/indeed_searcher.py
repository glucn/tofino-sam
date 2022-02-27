import logging
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup

from exceptions.exceptions import MalFormedMessageException
from crawler.proxies_manager import ProxiesManager


logging.getLogger().setLevel(logging.INFO)

def lambda_handler(event, context):
    logging.info("Entering Indeex Searcher lambda_handler")

    url = _parse_event(event)
    logging.info(f'Parsed url {url}')

    content, _ = ProxiesManager().crawl(url)

    soup = BeautifulSoup(content, 'html.parser')
    urls = [_parse_url(x['href']) for x in soup.find_all('a', class_='result')]

    # TODO: check if the URL already exists

    result = {
        "job_postings": [{"url": url} for url in urls]
    }
    return result

def _parse_event(event) -> str:
    """
    Parse the event
    """
    if 'url' not in event:
        raise MalFormedMessageException(f'Message {event} is malformed')

    return event['url']

def _parse_url(url: str):
    uu = list(urlparse(url))
    uu[0] = 'https'  # scheme
    uu[1] = 'ca.indeed.com'  # netloc, the link in the search results page are all relative
    return urlunparse(uu)
