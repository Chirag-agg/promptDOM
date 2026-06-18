import os
import uuid
from datetime import datetime, timezone
from .models import VisualContext

class ScreenshotStorage:
    def __init__(self, storage_dir: str = "data/screenshots"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def save(self, image_bytes: bytes, page_url: str, width: int = 1920, height: int = 1080) -> VisualContext:
        screenshot_id = str(uuid.uuid4())
        filename = f"{screenshot_id}.png"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
            
        return VisualContext(
            screenshot_id=screenshot_id,
            screenshot_path=filepath,
            page_url=page_url,
            width=width,
            height=height,
            created_at=datetime.now(timezone.utc).isoformat() + "Z"
        )
