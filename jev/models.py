from dataclasses import dataclass, asdict
from typing import Any
@dataclass
class Finding:
    check_name: str
    status: str
    severity: str
    summary: str
    evidence: list[str]
    facts: dict[str, Any]
    def to_dict(self): return asdict(self)
