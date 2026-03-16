from dataclasses import dataclass, asdict, field
from typing import Optional, List, Final
import re
import base64
import fnmatch


@dataclass
class TimeRange:
    start: Optional[str]
    end: Optional[str]

@dataclass
class DealImage:
    imageId: Optional[str]
    extension: Optional[str]

    _IMAGE_URL_TEMPLATE: Final[str] = "https://image.ibood.io/image/w256/{base64}"
    _BASE64_TEMPLATE_MIME: Final[str] = "gs://ibex-prd-api-30f0-documents-public/{tenantId}/{imageId}/image.{extension}"
    _BASE64_TEMPLATE_GO: Final[str] = "gs://ibood-go-production-gcs-storage/images/source/{imageId}.{extension}"

    tenantId: str = "eafb3ef2-e1ba-4f01-b67a-b0447bea74eb"

    def to_url(self) -> Optional[str]:
        if not self.imageId:
            return None

        base64_string = None
        if self.extension in ("image/png", "image/jpg", "image/jpeg"):
            extension = self.extension.split("/")[-1]
            base64_string = self._BASE64_TEMPLATE_MIME.format(
                tenantId=self.tenantId, imageId=self.imageId, extension=extension
            )
        elif self.extension in ("png", "jpg", "jpeg", "gif"):
            base64_string = self._BASE64_TEMPLATE_GO.format(imageId=self.imageId, extension=self.extension)

        if base64_string:
            base64_encoded = base64.b64encode(base64_string.encode()).decode()
            return self._IMAGE_URL_TEMPLATE.format(base64=base64_encoded.replace("=", ""))
        return None

    @classmethod
    def from_dict(cls, data: dict) -> "DealImage":
        return cls(
            imageId=data.get("id"),
            extension=data.get("extension")
        )


@dataclass
class Price:
    currency: str
    value: int
    cents: int

    def to_human_readable(self) -> str:
        symbols = {
            "EUR": "€"
        }
        symbol = symbols.get(self.currency, self.currency)
        return f"{symbol}{self.value}"


@dataclass
class IboodDeal:
    id: str
    raw_price: Optional[Price]
    title: Optional[str]
    brand: Optional[str]
    shortDescription: Optional[str]
    shortSpecs: Optional[str]
    raw_image: Optional[DealImage]
    hunt_times: List[TimeRange]
    classicId: Optional[str]
    slug: Optional[str]
    soldOut: bool
    matched_keywords: List[str] = field(default_factory=list, init=False, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "IboodDeal":
        hunt_times = []
        if "start" in data and "end" in data:
            hunt_times.append(TimeRange(start=data.get("start"), end=data.get("end")))
        elif "hunt_times" in data:
            hunt_times = [TimeRange(**t) for t in data.get("hunt_times", [])]
        
        image_data = data.get("image")
        raw_image = DealImage.from_dict(image_data) if image_data else None

        price_data = data.get("price")
        raw_price = Price(**price_data) if price_data else None

        return cls(
            id=data.get("id"),
            raw_price=raw_price,
            title=data.get("title"),
            brand=data.get("brand"),
            shortDescription=data.get("shortDescription"),
            shortSpecs=data.get("shortSpecs"),
            raw_image=raw_image,
            hunt_times=hunt_times,
            classicId=data.get("classicId"),
            slug=data.get("slug"),
            soldOut=data.get("soldOut", False),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def price(self) -> str:
        if self.raw_price:
            return self.raw_price.to_human_readable()
        return "N/A"

    def find_and_store_matches(self, keywords: List[str]) -> None:
        found_keywords = []
        
        search_fields = [
            self.id,
            self.title,
            self.brand,
            self.shortDescription,
            self.shortSpecs,
            self.price,
            self.classicId,
            self.slug,
        ]
        
        # Create a single searchable string, converting all fields to lowercase strings
        searchable_text = " ".join(str(field).lower() for field in search_fields if field)

        for keyword_line in keywords:
            # Regex to find exclusion terms (quoted or single-word)
            exclude_pattern = r'-\"([^\"]*)\"|-(\S+)'
            
            # Find all exclusion terms
            exclusions = re.findall(exclude_pattern, keyword_line.lower())
            exclude_keywords = [group[0] or group[1] for group in exclusions]

            # Get the inclusion keyword by removing the exclusion terms
            include_keyword = re.sub(exclude_pattern, '', keyword_line).strip()

            if not include_keyword:
                continue

            # Check for inclusion using fnmatch for wildcard support
            if fnmatch.fnmatch(searchable_text, f"*{include_keyword.lower()}*"):
                # Check for exclusion
                is_excluded = False
                for exclude_word in exclude_keywords:
                    if fnmatch.fnmatch(searchable_text, f"*{exclude_word}*"):
                        is_excluded = True
                        break
                
                if not is_excluded:
                    # Store the original keyword line
                    found_keywords.append(keyword_line)

        self.matched_keywords = list(set(found_keywords))

    @property
    def image(self) -> Optional[str]:
        if self.raw_image:
            return self.raw_image.to_url()
        return None

    @property
    def url(self) -> Optional[str]:
        if self.slug and self.classicId:
            return f"https://www.ibood.com/nl/s-nl/o/{self.slug}/{self.classicId}"
        return None