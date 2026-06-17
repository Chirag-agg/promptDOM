from enum import Enum
from pydantic import BaseModel

class ExecutorType(str, Enum):
    JAVASCRIPT = "JAVASCRIPT"
    BROWSER = "BROWSER"

class CapabilityID(str, Enum):
    DOM_MANIPULATION = "DOM_MANIPULATION"
    NOTIFICATIONS = "NOTIFICATIONS"
    OBSERVE = "OBSERVE"

class CapabilityRequirement(BaseModel):
    capability: CapabilityID
    permission_required: bool = False

class Capability(BaseModel):
    id: CapabilityID
    name: str
    supported: bool
    executor: ExecutorType
    requires_permission: bool = False
