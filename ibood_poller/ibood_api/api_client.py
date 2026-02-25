import requests
from typing import Final

BASEURL: Final[str] = "https://api.ibood.io"

class IboodClient:
    def __init__(self):
        self.base_url = BASEURL
        self.headers = {
            # 'accept': 'application/json, text/plain, */*',
            # 'accept-language': 'en-NL,en;q=0.9',
            # 'dnt': '1',
            'ibex-language': 'nl',
            'ibex-shop-id': 'b22a484d-fd20-570a-adf6-22edf2fdaf79',
            'ibex-tenant-id': 'eafb3ef2-e1ba-4f01-b67a-b0447bea74eb',
            # 'origin': 'https://www.ibood.com',
            # 'priority': 'u=1, i',
            # 'referer': 'https://www.ibood.com/',
            # 'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            # 'sec-ch-ua-mobile': '?0',
            # 'sec-ch-ua-platform': '"Windows"',
            # 'sec-fetch-dest': 'empty',
            # 'sec-fetch-mode': 'cors',
            # 'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            # 'x-correlation-id': 'dd2cfed4-2cd5-4b56-adfe-e054f753192b'
        }

    def get_live_events(self):
        session = requests.Session()
        try:
            session.get('https://www.ibood.com', headers=self.headers, timeout=10)
        except requests.RequestException:
            pass
        
        url = f"{self.base_url}/event/events/live"
        return session.get(url, headers=self.headers, timeout=10)
