# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class CSPEEntity:
    value: Any
    entity_type: str

class CSPEDocumentProcessor:
    def test(self):
        return "CSPEDocumentProcessor is working"