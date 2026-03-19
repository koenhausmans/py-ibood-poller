from datetime import datetime, timedelta
from typing import TypedDict, Dict, Optional, List

from .ibood_api.models import IboodDeal
from .json_storage import JsonStorage


class DealData(TypedDict):
    id: str
    appearance_date: str
    last_seen_date: str
    disappeared_since: Optional[str]
    title: str
    price: str
    url: str


class DealHistory(JsonStorage):
    def __init__(self, cache_file: str):
        super().__init__(cache_file)
        self.deals: Dict[str, DealData] = self._read_json()

    def _save(self) -> None:
        """Saves the current state of the deals cache to the JSON file."""
        self._write_json(self.deals)

    def update(self, current_deals: List[IboodDeal]):
        today = datetime.now().strftime("%Y-%m-%d")
        current_deal_ids = {deal.id for deal in current_deals}

        # Identify new deals and update existing ones
        for deal in current_deals:
            if deal.id not in self.deals:
                self.deals[deal.id] = {
                    "id": deal.id,
                    "appearance_date": today,
                    "last_seen_date": today,
                    "disappeared_since": None,
                    "title": deal.title or "N/A",
                    "price": deal.price,
                    "url": deal.url or "",
                }
            else:
                self.deals[deal.id]["last_seen_date"] = today
                self.deals[deal.id]["disappeared_since"] = None
                # Optionally update price/title/url if they can change
                self.deals[deal.id]["price"] = deal.price
                self.deals[deal.id]["url"] = deal.url or ""
                self.deals[deal.id]["title"] = deal.title or "N/A"

        # Identify and handle disappeared deals
        for deal_id in list(self.deals.keys()):
            if deal_id not in current_deal_ids:
                if self.deals[deal_id].get("disappeared_since") is None:
                    self.deals[deal_id]["disappeared_since"] = today
            else:
                # This deal is active, ensure disappeared_since is None
                if deal_id in self.deals:
                    self.deals[deal_id]["disappeared_since"] = None

        self._save()

    def cleanup_old_deals(self, days_to_keep: int = 3):
        today = datetime.now()
        three_days_ago = today - timedelta(days=days_to_keep)

        deals_to_remove = []
        for deal_id, deal_data in self.deals.items():
            if deal_data.get("disappeared_since"):
                disappeared_date = datetime.strptime(
                    deal_data["disappeared_since"], "%Y-%m-%d"
                )
                if disappeared_date < three_days_ago:
                    deals_to_remove.append(deal_id)

        if deals_to_remove:
            for deal_id in deals_to_remove:
                del self.deals[deal_id]
            self._save()

    def is_new(self, deal_id: str) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        return (
            deal_id in self.deals
            and self.deals[deal_id].get("appearance_date") == today
        )
