---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import json
import time
import os
import requests
from bs4 import BeautifulSoup


@dataclass
class BountyProgram:
    platform: str
    name: str
    url: str
    scope: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)
    rewards: str = ""
    vulnerability_types: List[str] = field(default_factory=list)
    ai_ml_focus: bool = False
    status: str = "active"


class BaseScraper(ABC):
    """Abstract base interface for bounty target scrapers."""

    def __init__(self, rate_limit: int = 2):
        self.rate_limit = rate_limit
        self._last_request_time = 0

    def _respect_rate_limit(self) -> None:
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    @abstractmethod
    def fetch_programs(self) -> List[BountyProgram]:
        """Fetch bounty programs from target platform."""
        pass

    @abstractmethod
    def fetch_program_detail(self, program_url: str) -> Optional[BountyProgram]:
        """Fetch detail of a specific bounty program."""
        pass


def manage_index(index_file: str = "state/bounty_index.json") -> Dict[str, Any]:
    """Manage local index for deduplication and timestamps."""
    if not os.path.exists(index_file):
        os.makedirs(os.path.dirname(index_file) or ".", exist_ok=True)
        return {
            "index": [],
            "metadata": {
                "last_updated": int(time.time()),
                "total_programs": 0
            }
        }

    with open(index_file, "r") as f:
        index_data = json.load(f)

    return index_data


def save_index(index_data: Dict[str, Any], index_file: str = "state/bounty_index.json") -> None:
    """Save index to local storage."""
    os.makedirs(os.path.dirname(index_file) or ".", exist_ok=True)
    with open(index_file, "w") as f:
        json.dump(index_data, f, indent=2, default=str)


def get_ai_programs(programs: List[BountyProgram]) -> List[BountyProgram]:
    """Filter and return only AI/ML focused programs."""
    return [p for p in programs if p.ai_ml_focus]


class HuntrScraper(BaseScraper):
    """Concrete implementation for Huntr platform scraping."""

    HUNTR_BASE_URL = "https://www.huntr.com"

    def __init__(self, index_file: str = "state/bounty_index.json", rate_limit: int = 2):
        super().__init__(rate_limit)
        self.index_file = index_file
        self.session = requests.Session()
        self.index_data = manage_index(index_file)

    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request with graceful degradation."""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json() or {}
            elif response.status_code in (403, 404):
                return None
            else:
                print(f"Error {response.status_code} for {url}")
                return None
        except requests.RequestException as e:
            print(f"Request error for {url}: {e}")
            return None

    def fetch_programs(self) -> List[BountyProgram]:
        """Fetch bounty programs from Huntr platform."""
        programs = []

        try:
            url = f"{self.HUNTR_BASE_URL}/programs.json"
            self._respect_rate_limit()

            data = self._make_request(url)

            if not data or "data" not in data:
                return []

            for prog in data["data"]:
                program = BountyProgram(
                    platform="Huntr",
                    name=prog.get("name", ""),
                    url=f"{self.HUNTR_BASE_URL}{prog.get('url', '')}",
                    scope=prog.get("scope", {}).get("allowed", []),
                    out_of_scope=prog.get("out_of_scope", []),
                    rewards=str(prog.get("rewards", "")),
                    vulnerability_types=prog.get("vulnerability_types", []),
                    ai_ml_focus=bool(prog.get("ai_ml", False) or prog.get("ml_models", False)),
                    status="active" if prog.get("status") != "closed" else "closed"
                )

                # Deduplication check
                dedup_key = f"{program.platform}:{program.url}"
                is_duplicate = any(
                    idx.get("platform") == program.platform and
                    idx.get("url") == program.url
                    for idx in self.index_data["index"]
                )

                if not is_duplicate:
                    programs.append(program)

            # Save updated index with new programs
            save_index(self.index_data)

            return programs

        except Exception as e:
            print(f"Error fetching Huntr programs: {e}")
            return []

    def fetch_program_detail(self, program_url: str) -> Optional[BountyProgram]:
        """Fetch detail of a specific bounty program."""
        try:
            self._respect_rate_limit()

            url = f"{self.HUNTR_BASE_URL}{program_url}"
            data = self._make_request(url)

            if not data:
                return None

            program = BountyProgram(
                platform="Huntr",
                name=data.get("name", ""),
                url=program_url,
                scope=data.get("scope", {}).get("allowed", []),
                out_of_scope=data.get("out_of_scope", []),
                rewards=str(data.get("rewards", "")),
                vulnerability_types=data.get("vulnerability_types", []),
                ai_ml_focus=bool(data.get("ai_ml", False) or data.get("ml_models", False)),
                status="active" if data.get("status") != "closed" else "closed"
            )

            return program

        except Exception as e:
            print(f"Error fetching program detail {program_url}: {e}")
            return None

    def get_index(self) -> Dict[str, Any]:
        """Get current index data."""
        self.index_data = manage_index(self.index_file)
        return self.index_data
```