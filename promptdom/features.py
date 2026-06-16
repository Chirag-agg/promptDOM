from typing import Optional

FEATURES = {
    "youtube_shorts": {
        "selector": "ytd-reel-shelf-renderer"
    },
    "comments": {
        "selector": "#comments"
    },
    "sidebar": {
        "selector": "#secondary"
    }
}


def get_selector(target: str) -> Optional[str]:
    """Get CSS selector for a target feature"""
    return FEATURES.get(target, {}).get("selector")