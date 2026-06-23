import json
import os
from typing import Optional

class DomainResolver:
    def __init__(self, aliases_path: str = "data/site_aliases.json"):
        self.aliases_path = aliases_path
        self._aliases = {}
        self._load_aliases()
        
    def _load_aliases(self):
        if os.path.exists(self.aliases_path):
            try:
                with open(self.aliases_path, "r", encoding="utf-8") as f:
                    self._aliases = json.load(f)
            except Exception as e:
                print(f"Error loading site aliases: {e}")
                
    def resolve(self, target: str) -> str:
        """Resolves a target name like 'Netflix' to a hostname like 'www.netflix.com'."""
        target_lower = target.lower().strip()
        
        if target_lower in self._aliases:
            return self._aliases[target_lower]
            
        # Fallback heuristic if not in aliases
        if "." in target_lower:
            return target_lower
        return f"www.{target_lower}.com"
