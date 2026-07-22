from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class RunContext:
    workflow_id: str
    workflow_name: str
    source_type: str
    page_name: str = ""
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)
