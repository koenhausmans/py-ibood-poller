import requests
import json
import structlog
import dataclasses
import logging
import asyncio
import random
import os
import sys
from typing import Final
from ._logging import _setup_logging
from .ibood_api.api_client import IboodClient
from .ibood_api.models import IboodDeal

# Configure structlog
_setup_logging()
logger = structlog.get_logger()

FILTERED_EVENTS_FILE: Final[str] = "filtered_events.json"

class EventFileManager:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def _read_file(self) -> list:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _write_file(self, data: list) -> None:
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def has_id(self, event_id: str) -> bool:
        data = self._read_file()
        existing_ids = {item.get('id') for item in data if 'id' in item}
        return event_id in existing_ids

    def add_event(self, event: dict) -> None:
        data = self._read_file()
        data.append(event)
        self._write_file(data)

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Poller stopped by user")

async def async_main():
    client = IboodClient()
    file_manager = EventFileManager(FILTERED_EVENTS_FILE)
    
    while True:
        try:
            response = client.get_live_events()
            logger.info("API request", status_code=response.status_code)
            
            if response.status_code == 200:
                try:
                    data = response.json()  # Parse the JSON response
                    
                    # Navigate to the current item
                    try:
                        current_item = data["data"]["items"][0]["currentItem"]
                        # Navigate to the current item safely
                        items = data.get("data", {}).get("items", [])
                        if not items:
                            logger.warning("No items found in response")
                            continue
                        
                        current_item = items[0].get("currentItem")
                        if not current_item:
                            logger.warning("No currentItem found in first item")
                            continue
                    
                        # Extract the specific fields
                        deal: IboodDeal = IboodDeal.from_dict(current_item)
                        
                        logger.debug("Filtered current item", data=deal)
                        
                        # Check if current ID exists in the persistent file
                        if not file_manager.has_id(deal.id):
                            file_manager.add_event(deal.to_dict())
                            logger.info("New current item added", id=deal.id, name=deal.title)
                        else:
                            logger.info("Current item already exists", id=deal.id, name=deal.title)
                    
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
    main()
