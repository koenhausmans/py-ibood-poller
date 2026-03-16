import requests
import json
import structlog
import asyncio
import random
from typing import Final
from ._logging import _setup_logging
from .ibood_api.api_client import IboodClient
from .ibood_api.models import IboodDeal
from .event_saver import EventFileManager, UpsertStatus

# Configure structlog
_setup_logging()
logger = structlog.get_logger()

FILTERED_EVENTS_FILE: Final[str] = "filtered_events.json"

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
            response.raise_for_status()
            logger.info("API request", status_code=response.status_code)

            data = response.json()

            items = data.get("data", {}).get("items", [])
            if not items:
                logger.warning("No items found in response")
            else:
                current_item = items[0].get("currentItem")
                if not current_item:
                    logger.warning("No currentItem found in the first item")
                else:
                    deal = IboodDeal.from_dict(current_item)
                    logger.debug("Filtered current item", data=deal)

                    status = file_manager.upsert_event(deal)

                    if status == UpsertStatus.NEW:
                        logger.info("New deal added", id=deal.id, name=deal.title)
                    elif status == UpsertStatus.UPDATED:
                        logger.info(
                            "Deal updated with new hunt time",
                            id=deal.id,
                            name=deal.title,
                        )
                    else:  # unchanged
                        logger.info(
                            "Deal already exists and is up to date",
                            id=deal.id,
                            name=deal.title,
                        )
        except requests.RequestException as e:
            # This handles connection errors, timeouts, etc., and HTTP error status codes via raise_for_status()
            logger.error("HTTP request failed", error=str(e))
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from response.")
        except (KeyError, IndexError) as e:
            logger.error("Unexpected data structure in response", error=str(e))

        # Wait randomly between 28 and 47 seconds before next poll
        sleep_time = random.randint(28, 47)
        logger.debug("Sleeping before next poll", seconds=sleep_time)
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    main()
