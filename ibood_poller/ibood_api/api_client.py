import requests
from typing import Final

BASEURL: Final[str] = "https://api.ibood.io"

class IboodClient:
    def __init__(self):
        self.base_url = BASEURL
        self.headers = {
            'ibex-language': 'nl',
            'ibex-shop-id': 'b22a484d-fd20-570a-adf6-22edf2fdaf79',
            'ibex-tenant-id': 'eafb3ef2-e1ba-4f01-b67a-b0447bea74eb',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }
    
    def _get_session(self) -> requests.Session:
        session = requests.Session()
        try:
            session.get('https://www.ibood.com', headers=self.headers, timeout=10)
        except requests.RequestException:
            pass
        return session

    def get_live_events(self):
        session = self._get_session()
        url = f"{self.base_url}/event/events/live"
        return session.get(url, headers=self.headers, timeout=10)

    def get_all_deals(self):
        session = self._get_session()
        url = f"{self.base_url}/search/items/live?take=10000"
        return session.get(url, headers=self.headers, timeout=10)