from dataclasses import dataclass, asdict
from typing import Any, Optional

@dataclass
class IboodDeal:
    id: str
    price: Any
    title: Optional[str]
    shortdescription: Optional[str]
    shortspecs: Optional[str]
    image: Any
    start: Optional[str]
    end: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "IboodDeal":
        return cls(
            id=data.get("id"),
            price=data.get("price"),
            title=data.get("title"),
            shortdescription=data.get("shortDescription"),
            shortspecs=data.get("shortSpecs"),
            image=data.get("image"),
            start=data.get("start"),
            end=data.get("end"),
        )

    def to_dict(self) -> dict:
        return asdict(self)