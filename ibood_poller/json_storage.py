import json
import os
from typing import Dict, Any

class JsonStorage:
    def __init__(self, filepath: str):
        self.filepath = filepath
        # Ensure the cache directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def _read_json(self) -> Dict[str, Any]:
        """Reads and returns the content of the JSON file."""
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _write_json(self, data: Dict[str, Any]) -> None:
        """Writes the given dictionary to the JSON file."""
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=4)
