from .models import KnowledgePack
from .storage import KnowledgeStorage
from .builder import KnowledgeBuilder
from promptdom.capture.storage import CaptureStorage
from promptdom.intelligence.service import IntelligenceService
from promptdom.archetypes.service import ArchetypeService


class KnowledgeService:
    def __init__(
        self,
        capture_storage: CaptureStorage,
        intelligence_service: IntelligenceService,
        archetype_service: ArchetypeService
    ):
        self.storage = KnowledgeStorage()
        self.builder = KnowledgeBuilder(capture_storage, intelligence_service, archetype_service)

    def build_pack(self, hostname: str) -> KnowledgePack | None:
        pack = self.builder.build(hostname)
        if pack:
            self.storage.save(pack)
        return pack

    def get_pack(self, hostname: str) -> KnowledgePack | None:
        return self.storage.load(hostname)

    def list_packs(self) -> list[KnowledgePack]:
        return self.storage.list_packs()
