import requests
import uuid
from typing import Final

BASEURL: Final[str] = "https://api.ibood.io"

class IboodClient:
    def __init__(self):
        self.base_url = BASEURL
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-NL,en-US;q=0.9,en;q=0.8',
            'dnt': '1',
            'ibex-language': 'nl',
            'ibex-shop-id': 'b22a484d-fd20-570a-adf6-22edf2fdaf79',
            'ibex-tenant-id': 'eafb3ef2-e1ba-4f01-b67a-b0447bea74eb',
            'origin': 'https://www.ibood.com',
            'referer': 'https://www.ibood.com/',
            'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        }

    def _get_session(self) -> requests.Session:
        session = requests.Session()
        try:
            session.get('https://www.ibood.com', headers=self.headers, timeout=10)
        except requests.RequestException:
            pass
        return session

    def _request_headers(self) -> dict:
        headers = dict(self.headers)
        headers['x-correlation-id'] = str(uuid.uuid4())
        return headers

    def get_live_events(self):
        session = self._get_session()
        url = f"{self.base_url}/event/events/live"
        return session.get(url, headers=self._request_headers(), timeout=10)

    def get_all_deals(self):
        session = self._get_session()
        url = f"{self.base_url}/search/items/live?take=10000"
        return session.get(url, headers=self._request_headers(), timeout=10)
