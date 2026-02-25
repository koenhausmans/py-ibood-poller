import requests
import json
import structlog
import logging
import asyncio
import random

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
logging.getLogger().setLevel(logging.INFO)
# Add a stream handler to output to console
handler = logging.StreamHandler()
logging.getLogger().addHandler(handler)

async def main():
    url = "https://api.ibood.io/event/events/live"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-NL,en;q=0.9',
        'dnt': '1',
        'ibex-language': 'nl',
        'ibex-shop-id': 'b22a484d-fd20-570a-adf6-22edf2fdaf79',
        'ibex-tenant-id': 'eafb3ef2-e1ba-4f01-b67a-b0447bea74eb',
        'origin': 'https://www.ibood.com',
        'priority': 'u=1, i',
        'referer': 'https://www.ibood.com/',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        'x-correlation-id': 'dd2cfed4-2cd5-4b56-adfe-e054f753192b'
    }
    
    while True:
        # Use a session to maintain cookies
        session = requests.Session()
        
        # First, visit the main site to get cookies
        try:
            session.get('https://www.ibood.com', headers=headers)
        except requests.RequestException:
            pass  # Ignore if this fails
        
        try:
            response = session.get(url, headers=headers)
            logger.info("API request", status_code=response.status_code, content_type=response.headers.get('Content-Type', 'N/A'))
            
            if response.status_code == 200:
                try:
                    data = response.json()  # Parse the JSON response
                    
                    # Navigate to the current item
                    try:
                        current_item = data["data"]["items"][0]["currentItem"]
                    
                        # Extract the specific fields
                        filtered_current = {
                            'id': current_item.get('id'),
                            'price': current_item.get('price'),
                            'title': current_item.get('title'),
                            'shortdescription': current_item.get('shortDescription'),
                            'shortspecs': current_item.get('shortSpecs'),
                            'image': current_item.get('image'),
                            'start': current_item.get('start'),
                            'end': current_item.get('end')
                        }
                        
                        logger.debug("Filtered current item", data=filtered_current)
                        
                        
                        # Check if current ID exists in the persistent file
                        import os
                        if os.path.exists('filtered_events.json'):
                            try:
                                with open('filtered_events.json', 'r') as f:
                                    existing_data = json.load(f)
                            except (json.JSONDecodeError, IOError):
                                existing_data = []
                        else:
                            existing_data = []
                        
                        existing_ids = {item['id'] for item in existing_data if 'id' in item}
                        
                        if filtered_current['id'] not in existing_ids:
                            # Append new item to existing
                            updated_data = existing_data + [filtered_current]
                            with open('filtered_events.json', 'w') as f:
                                json.dump(updated_data, f, indent=4)
                            logger.info("New current item added", id=filtered_current['id'], name=filtered_current['title'])
                        else:
                            logger.info("Current item already exists", id=filtered_current['id'], name=filtered_current['title'])
                    
                    except (KeyError, IndexError) as e:
                        logger.error("Error accessing current item", error=str(e), data=data)
                except json.JSONDecodeError:
                    logger.error("Response is not JSON", raw_content=response.text[:1000])
            else:
                logger.error("HTTP error", status_code=response.status_code, response_text=response.text[:1000])
    
        except requests.RequestException as e:
            logger.error("Error fetching data", error=str(e))
        
        # Wait randomly between 28 and 47 seconds before next poll
        sleep_time = random.randint(28, 47)
        logger.debug("Sleeping before next poll", seconds=sleep_time)
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(main())
