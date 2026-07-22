from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PageStateDescriptor:
    page_name: str
    state_id: str = ""
    state_type: str = ""
    source_artifacts: list[str] = field(default_factory=list)
    signals: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
