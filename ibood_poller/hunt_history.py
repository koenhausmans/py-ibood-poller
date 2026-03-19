from enum import Enum
from typing import Dict

from .ibood_api.models import IboodDeal
from .json_storage import JsonStorage


class UpsertStatus(Enum):
    UNCHANGED = "unchanged"
    UPDATED = "updated"
    NEW = "new"


class HuntHistory(JsonStorage):
    def __init__(self, filepath: str):
        super().__init__(filepath)
        self.events: Dict[str, IboodDeal] = self._load_events()

    def _load_events(self) -> Dict[str, IboodDeal]:
        """Reads the raw JSON and deserializes it into IboodDeal objects."""
        raw_events = self._read_json()
        
        events = {}
        for event_id, event_data in raw_events.items():
            events[event_id] = IboodDeal.from_dict(event_data)
        return events

    def _save_events(self) -> None:
        """Serializes the IboodDeal objects and writes them to the JSON file."""
        raw_events = {}
        for event_id, deal in self.events.items():
            raw_events[event_id] = deal.to_dict()
        self._write_json(raw_events)

    def upsert_event(self, deal_from_api: IboodDeal) -> UpsertStatus:
        status = UpsertStatus.UNCHANGED

        # The new deal from API will have exactly one time range
        if not deal_from_api.hunt_times:
            # Should not happen with hunt deals, but good to be safe
            return status
            
        new_time_range = deal_from_api.hunt_times[0]

        if deal_from_api.id in self.events:
            existing_deal = self.events[deal_from_api.id]

            # Update fields that can change
            existing_deal.raw_price = deal_from_api.raw_price
            existing_deal.title = deal_from_api.title
            existing_deal.soldOut = deal_from_api.soldOut
            
            # A hunt deal might get a new image/slug/etc., but it's the same "deal"
            # so we update the core info.

            if new_time_range not in existing_deal.hunt_times:
                existing_deal.hunt_times.append(new_time_range)
                status = UpsertStatus.UPDATED
        else:
            self.events[deal_from_api.id] = deal_from_api
            status = UpsertStatus.NEW

        if status != UpsertStatus.UNCHANGED:
            self._save_events()

        return status
