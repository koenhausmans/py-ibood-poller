import json
import os
from enum import Enum

from .ibood_api.models import IboodDeal


class UpsertStatus(Enum):
    UNCHANGED = "unchanged"
    UPDATED = "updated"
    NEW = "new"


class EventFileManager:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def _read_events(self) -> dict[str, IboodDeal]:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r") as f:
                # Stored as {"id1": {...}, "id2": {...}}
                raw_events = json.load(f)

            events = {}
            for event_id, event_data in raw_events.items():
                events[event_id] = IboodDeal.from_dict(event_data)
            return events
        except (json.JSONDecodeError, IOError):
            return {}

    def _write_events(self, events: dict[str, IboodDeal]) -> None:
        raw_events = {}
        for event_id, deal in events.items():
            raw_events[event_id] = deal.to_dict()
        with open(self.filepath, "w") as f:
            json.dump(raw_events, f, indent=4)

    def upsert_event(self, deal_from_api: IboodDeal) -> UpsertStatus:
        events = self._read_events()
        status = UpsertStatus.UNCHANGED

        # The new deal from API will have exactly one time range
        new_time_range = deal_from_api.hunt_times[0]

        if deal_from_api.id in events:
            existing_deal = events[deal_from_api.id]

            # Update fields
            existing_deal.price = deal_from_api.price
            existing_deal.title = deal_from_api.title
            existing_deal.shortDescription = deal_from_api.shortDescription
            existing_deal.shortSpecs = deal_from_api.shortSpecs
            existing_deal.image = deal_from_api.image

            if new_time_range not in existing_deal.hunt_times:
                existing_deal.hunt_times.append(new_time_range)
                status = UpsertStatus.UPDATED
        else:
            events[deal_from_api.id] = deal_from_api
            status = UpsertStatus.NEW

        if status != UpsertStatus.UNCHANGED:
            self._write_events(events)

        return status
