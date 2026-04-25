---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

# Constants for local state storage relative to this script's location
STATE_DIR = Path(__file__).parent / "state"
INDEX_FILE = STATE_DIR / "bounty_index.json"


@dataclass
class BountyProgram:
    """Data model for a bounty program."""
    platform: str
    name: str
    url: str
    scope: str
    out_of_scope: str
    rewards: str
    vulnerability_types: List[str] = field(default_factory=list)
    ai_ml_focus: bool = False
    status: str = "new"

    def to_dict(self):
        """Convert instance to dictionary (useful for saving or JSON)."""
        return {
            "platform": self.platform,
            "name": self.name,
            "url": self.url,
            "scope": self.scope,
            "out_of_scope": self.out_of_scope,
            "rewards": self.rewards,
            "vulnerability_types": list(self.vulnerability_types),
            "ai_ml_focus": self.ai_ml_focus,
            "status": self.status,
            "timestamp": datetime.now().isoformat()
        }


class BaseScraper(ABC):
    """Abstract base class for bounty scrapers that handles state management."""

    def __init__(self):
        # Ensure state directory exists (create if missing)
        try:
            self.state_dir = STATE_DIR
            self.state_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize index file if not exists
            self.index_file = INDEX_FILE
            if not self.index_file.exists():
                with open(INDEX_FILE, 'w') as f:
                    json.dump([], f)
        except OSError as e:
            print(f"Failed to create state directory or file (likely permission issue): {e}")

    @staticmethod
    def _load_index() -> List[dict]:
        """Load the index of seen URLs."""
        try:
            with open(INDEX_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def _save_index(data: List[dict]):
        """Persist the updated index."""
        try:
            with open(INDEX_FILE, 'w') as f:
                json.dump(data, f)
        except OSError:
            pass  # Silently handle write errors for robustness

    @abstractmethod
    def fetch_programs(self) -> List[BountyProgram]:
        """Fetch a list of programs. Should respect rate limits."""
        pass
    
    @abstractmethod
    def fetch_program_detail(self, url: str) -> Optional[BountyProgram]:
        """Fetch details for a single program."""
        pass


class HuntrScraper(BaseScraper):
    """Specific scraper implementation for huntr.dev."""
    
    def __init__(self, base_url: str = "https://huntr.dev"):
        super().__init__()
        self.base_url = base_url

    def fetch_programs(self) -> List[BountyProgram]:
        programs: List[BountyProgram] = []
        seen_urls_set = set()  # Using a set for faster O(1) duplicate checks in memory
        
        try:
            # Huntr typically lists bounties here. Adjust selector based on actual DOM if dynamic.
            response = requests.get(f"{self.base_url}/bounties", timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Iterate over found program elements 
                for item in soup.select('a.program-item'): # Adjust selector 'a.program-item' based on DOM inspection
                    link = item.get('href', '')
                    
                    if not link: continue
                    
                    name = item.get_text(strip=True)
                    
                    # Skip known bots/maintenance links if present or empty names
                    if name == "": continue

                    # Prevent duplicates using global state AND local set logic
                    is_seen_globally = any(p.url == link for p in programs)
                    if is_seen_globally: continue
                    
                    # Add to current list and global memory set
                    new_prog = BountyProgram(
                        platform="huntr",
                        name=name,
                        url=link,
                        scope="", 
                        out_of_scope="", 
                        rewards="", 
                        vulnerability_types=[], 
                        ai_ml_focus=False, 
                        status="new"
                    )

                    # Deduplicate strictly here to avoid adding same URL twice in run
                    is_dup = any(p.url == link for p in programs)
                    if not is_dup:
                         seen_urls_set.add(link) # Add to set for this batch if needed, but list check handles it
                         programs.append(new_prog)
                else:
                    # Optional: Pause between fetching batches or pages if pagination exists. 
                    # If single page scrape, this sleep acts as a rate limiter per request cycle.
                    time.sleep(2) # Rate limit enforcement per main request
            return programs
        
        except requests.exceptions.RequestException as e:
            print(f"Network error scraping Huntr: {e}")
        
        return programs
    
    def fetch_program_detail(self, url: str) -> Optional[BountyProgram]:
        try:
            resp = requests.get(f"{self.base_url}{url}", timeout=5)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Try to get title from meta or <title> tag
                title_tag = soup.find('title')
                title = title_tag.string if title_tag and title_tag.string else "Unknown"
                
                # If Huntr uses dynamic JS content, standard requests might need Selenium. 
                # This code assumes static HTML fetches work (or uses a headless browser logic elsewhere).
                
                return BountyProgram(
                    platform="huntr",
                    name=title,
                    url=url,
                    scope="", out_of_scope="", rewards="", 
                    vulnerability_types=[], ai_ml_focus=False, status="active"
                )
        except requests.exceptions.RequestException:
            pass
        
        return None


# Example usage or testing block (uncomment to run directly)
if __name__ == "__main__":
    try:
        scraper = HuntrScraper()
        programs = scraper.fetch_programs()
        print(f"Scraped {len(programs)} programs.")
        if programs:
            print("Sample program:", programs[0].name)
        
        # Uncomment for detail fetch demo (replace URL)
        # detailed = scraper.fetch_program_detail("/example") 
        # print(detailed)
    except Exception as e:
        print(f"Error running script: {e}")
```<|endoftext|><|im_start|>user
You pass