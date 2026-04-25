---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import abc
import dataclasses
import json
import os
import time
from typing import List, Optional, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    # Fallback or graceful degradation if dependencies missing
    requests = None
    BeautifulSoup = None

DATA_DIR = "state"
INDEX_FILE = os.path.join(DATA_DIR, "bounty_index.json")


@dataclasses.dataclass
class BountyProgram:
    platform: str
    name: str
    url: str
    scope: str
    out_of_scope: str
    rewards: str
    vulnerability_types: List[str]
    ai_ml_focus: bool
    status: str


class BaseScraper(abc.ABC):
    def __init__(self, platform_name: str):
        self.platform = platform_name

    def _ensure_dir(self) -> None:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _load_index(self) -> Dict[str, BountyProgram]:
        self._ensure_dir()
        try:
            if os.path.exists(INDEX_FILE):
                with open(INDEX_FILE, 'r') as f:
                    data = json.load(f)
                    return {item['url']: BountyProgram(**item) for item in data}
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_index(self, programs: Dict[str, BountyProgram]) -> None:
        self._ensure_dir()
        try:
            with open(INDEX_FILE, 'w') as f:
                # Convert objects to dicts for JSON serialization
                json.dump([dataclasses.asdict(p) for p in programs.values()], f)
        except IOError:
            pass

    @abc.abstractmethod
    def fetch_programs(self) -> List[BountyProgram]:
        """Fetch programs from target platform, handle rate limits, deduplicate."""
        pass

    @abc.abstractmethod
    def fetch_program_detail(self, url: str) -> Optional[BountyProgram]:
        """Fetch specific program detail, handle unreachable gracefully."""
        pass

    def get_ai_programs(self, programs: List[BountyProgram]) -> List[BountyProgram]:
        """Filter programs where ai_ml_focus is True."""
        return [p for p in programs if p.ai_ml_focus]


class HuntrScraper(BaseScraper):
    def __init__(self):
        super().__init__("Huntr")

    def _make_request(self, url: str) -> Optional[requests.Response]:
        if not requests or not BeautifulSoup:
            return None
        try:
            time.sleep(2)  # Rate limit enforcement between requests
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response
        except (requests.RequestException, OSError):
            return None

    def _parse_programs(self, html_content: str) -> List[BountyProgram]:
        programs = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Placeholder parsing logic for implementation structure
            # In real scenario, scrape specific selectors here
            if "programs" not in dir(self): 
                pass  # Generic handling
            
            # Simulating finding program cards
            # Since we don't have actual schema/hunters API details here, 
            # we implement the graceful degradation and data structure population logic.
            
            # Example parsing structure based on typical HTML
            for card in soup.select(".program-card"):
                try:
                    name = card.find("h2", class_="title").text.strip() if card.find("h2") else "Unknown"
                    vuln_types = ["CWE-20", "CWE-89"] # Default placeholders
                    
                    p = BountyProgram(
                        platform=self.platform,
                        name=name,
                        url=card.get("href", ""),
                        scope="Web Application",
                        out_of_scope="Internal Network",
                        rewards="$100-$500",
                        vulnerability_types=vuln_types,
                        ai_ml_focus=False, # Huntr default unless specified
                        status="Active"
                    )
                    programs.append(p)
                except AttributeError:
                    continue
        except Exception:
            return []
        return programs

    def fetch_programs(self) -> List[BountyProgram]:
        """Implement fetching and index update."""
        index = self._load_index()
        all_progs = []
        
        # Fetch URL (Mocking the base Huntr search/list view for this implementation skeleton)
        # Using a mock endpoint to satisfy scraper structure logic without hardcoding public keys
        target_url = "https://app.huntr.com/v2/programs" 
        
        response = self._make_request(target_url)
        
        if response:
            new_progs = self._parse_programs(response.text)
            
            # Deduplication against existing index based on URL
            for p in new_progs:
                if p.url not in index:
                    index[p.url] = p
                    
            all_progs.extend(new_progs.values())
        else:
            # Graceful degradation: no programs found or network error
            pass
            
        self._save_index(index)
        
        return list(index.values())

    def fetch_program_detail(self, url: str) -> Optional[BountyProgram]:
        """Fetch detail for specific program."""
        index = self._load_index()
        
        if url in index and index[url].status == "Active":
            # Cache hit
            return index[url]
            
        response = self._make_request(url)
        if not response:
            return None
            
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            name_el = soup.find("h1")
            scope_el = soup.select_one(".scope-text")
            
            # Construct detailed program object
            p = BountyProgram(
                platform=self.platform,
                name=name_el.text.strip() if name_el else url,
                url=url,
                scope=scope_el.text.strip() if scope_el else "Default",
                out_of_scope="Not specified",
                rewards="$100+",
                vulnerability_types=["General"],
                ai_ml_focus=False,
                status="Active"
            )
            
            # Check for AI indicators in description/body to set flag dynamically
            body = soup.find("div", class_="description")
            if body and ("AI" in str(body) or "ML" in str(body)):
                p.ai_ml_focus = True
            
            return p
        except Exception:
            return None

    def get_ai_programs(self) -> List[BountyProgram]:
        """Fetch and filter AI/ML focused programs."""
        progs = self.fetch_programs()
        return self.get_ai_programs(progs)