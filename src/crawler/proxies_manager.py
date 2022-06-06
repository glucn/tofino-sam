import json
import logging
import random
from datetime import datetime, timedelta

from aws import Lambda
from exceptions import RetryableException
from models.crawler_proxy import CrawlerProxy, deactivate_crawler_proxy, list_active_crawler_proxy

DEACTIVATED_WAIT_TIME = timedelta(hours=12)


class ProxiesManager:
    """ The manager for proxy Lambda functions """

    @staticmethod
    def _get_random_proxy() -> CrawlerProxy:
        available_proxies = list_active_crawler_proxy(datetime.now() - DEACTIVATED_WAIT_TIME)
        logging.info(f'available_proxies: {available_proxies}')
        if len(available_proxies) == 0:
            logging.warning(f'There is no active proxy at the moment')
            raise RetryableException
        return available_proxies[random.randrange(len(available_proxies))]

    @staticmethod
    def _deactivate_proxy(proxy_id: str) -> None:
        try:
            deactivate_crawler_proxy(proxy_id)
            logging.info(f'Proxy {proxy_id} deactivated')
        except Exception as ex:
            raise RetryableException(ex)

    def crawl(self, url: str):
        crawler_proxy = self._get_random_proxy()
        r = Lambda.invoke(crawler_proxy.region, crawler_proxy.arn, json.dumps({'url': url}))
        response = json.loads(r)
        logging.info(f'ProxiesManager crawl response {response}')

        if 'statusCode' not in response:
            # TODO: change to logging.error
            logging.warning(f'Getting URL "{url}" error with response {response}')
            self._deactivate_proxy(crawler_proxy.id)
            raise RetryableException
        
        if response['statusCode'] != 200:
            logging.warning(f'Getting URL "{url}" resulted in status code {response["statusCode"]}')
            self._deactivate_proxy(crawler_proxy.id)
            raise RetryableException

        if 'content' not in response or not response['content']:
            logging.warning(f'Proxy in region [{crawler_proxy.region}] received empty content')
            self._deactivate_proxy(crawler_proxy.id)
            raise RetryableException

        if 'www.hcaptcha.com' in response['content']:
            logging.warning(f'Proxy in region [{crawler_proxy.region}] received hcaptcha check')
            self._deactivate_proxy(crawler_proxy.id)
            raise RetryableException

        return response['content'], response['url']
