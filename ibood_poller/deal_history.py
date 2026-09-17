from datetime import datetime, timedelta
from typing import TypedDict, Dict, Optional, List

from .ibood_api.models import IboodDeal
from .json_storage import JsonStorage


class DealData(TypedDict):
    id: str
    product_id: str
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

    @staticmethod
    def _key_for(deal: IboodDeal) -> str:
        """Identity key for a deal: the stable product id iBOOD assigns to the
        underlying article, so the same article re-uploaded under a new deal
        `id` is recognized as the same entry. Falls back to the deal `id`
        itself if `product_id` is ever missing."""
        return deal.product_id or deal.id

    def update(self, current_deals: List[IboodDeal]):
        today = datetime.now().strftime("%Y-%m-%d")
        current_deal_keys = {self._key_for(deal) for deal in current_deals}

        # Identify new deals and update existing ones
        for deal in current_deals:
            key = self._key_for(deal)
            if key not in self.deals:
                self.deals[key] = {
                    "id": deal.id,
                    "product_id": key,
                    "appearance_date": today,
                    "last_seen_date": today,
                    "disappeared_since": None,
                    "title": deal.title or "N/A",
                    "price": deal.price,
                    "url": deal.url or "",
                }
            else:
                self.deals[key]["id"] = deal.id
                self.deals[key]["last_seen_date"] = today
                self.deals[key]["disappeared_since"] = None
                # Optionally update price/title/url if they can change
                self.deals[key]["price"] = deal.price
                self.deals[key]["url"] = deal.url or ""
                self.deals[key]["title"] = deal.title or "N/A"

        # Identify and handle disappeared deals
        for key in list(self.deals.keys()):
            if key not in current_deal_keys:
                if self.deals[key].get("disappeared_since") is None:
                    self.deals[key]["disappeared_since"] = today
            else:
                # This deal is active, ensure disappeared_since is None
                if key in self.deals:
                    self.deals[key]["disappeared_since"] = None

        self._save()

    def cleanup_old_deals(self, days_to_keep: int = 3):
        today = datetime.now()
        three_days_ago = today - timedelta(days=days_to_keep)

        deals_to_remove = []
        for key, deal_data in self.deals.items():
            if deal_data.get("disappeared_since"):
                disappeared_date = datetime.strptime(
                    deal_data["disappeared_since"], "%Y-%m-%d"
                )
                if disappeared_date < three_days_ago:
                    deals_to_remove.append(key)

        if deals_to_remove:
            for key in deals_to_remove:
                del self.deals[key]
            self._save()

    def is_new(self, deal: IboodDeal) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        key = self._key_for(deal)
        return (
            key in self.deals
            and self.deals[key].get("appearance_date") == today
        )
