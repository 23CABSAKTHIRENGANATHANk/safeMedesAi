"""HTTP utilities with retry and timeouts."""
from typing import Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
import logging

log = logging.getLogger('scraper.http')

DEFAULT_TIMEOUT = 30

def _is_transient_error(exception: Exception) -> bool:
    if isinstance(exception, requests.exceptions.HTTPError):
        status_code = exception.response.status_code if exception.response is not None else 0
        return status_code >= 500
    return isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(_is_transient_error)
)
def fetch(url: str, method: str = 'GET', headers: Optional[dict] = None, params: Optional[dict] = None, stream: bool = False, timeout: int = DEFAULT_TIMEOUT):
    headers = headers or {"User-Agent": "MedVerify Scraper (+https://example.org)"}
    log.debug('Fetching %s', url)
    resp = requests.request(method, url, headers=headers, params=params, timeout=timeout, stream=stream)
    resp.raise_for_status()
    return resp

