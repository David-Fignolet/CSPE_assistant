# test_import.py
from dataclasses import dataclass
from typing import Any

@dataclass
class TestEntity:
    value: Any
    type: str

def test_import():
    return "Import successful!"

if __name__ == "__main__":
    print(test_import())
