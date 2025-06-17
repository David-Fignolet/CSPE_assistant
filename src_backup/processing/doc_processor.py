# doc_processor.py
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class CSPEEntity:
    value: Any
    entity_type: str

class DocumentProcessor:
    def test(self):
        return "DocumentProcessor is working"
