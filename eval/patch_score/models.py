import json
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any

@dataclass
class DiffLine:
    old_line_num: int
    new_line_num: int
    content: str
    type: str  # 'added', 'removed', or 'context'

@dataclass
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine] = field(default_factory=list)

@dataclass
class FileDiff:
    old_path: str
    new_path: str
    is_new: bool = False
    is_deleted: bool = False
    hunks: List[DiffHunk] = field(default_factory=list)
    added_lines: int = 0
    removed_lines: int = 0
    changed_old_line_numbers: List[int] = field(default_factory=list)
    changed_new_line_numbers: List[int] = field(default_factory=list)

@dataclass
class FunctionRange:
    name: str
    start_line: int
    end_line: int

@dataclass
class PatchFootprint:
    files: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    line_ranges: List[str] = field(default_factory=list)
    lines_touched: int = 0
    added_lines: int = 0
    removed_lines: int = 0

@dataclass
class Verdict:
    label: str
    confidence: float
    explanation: str
    failure_taxonomy: List[str] = field(default_factory=list)

@dataclass
class PatchScore:
    locality: Dict[str, Any] = field(default_factory=dict)
    minimality: Dict[str, Any] = field(default_factory=dict)
    overlap: Dict[str, Any] = field(default_factory=dict)
    verdict: Verdict = field(default_factory=lambda: Verdict("", 0.0, ""))

    def to_json(self) -> str:
        def _sort_lists(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _sort_lists(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                # Only sort if elements are comparable (e.g. strings or numbers)
                if all(isinstance(x, (str, int, float, bool)) for x in obj):
                    return sorted(obj)
                return [_sort_lists(x) for x in obj]
            elif isinstance(obj, set):
                return sorted(list(obj))
            elif hasattr(obj, "__dict__"):
                return _sort_lists(obj.__dict__)
            return obj
        
        serializable = _sort_lists(self)
        return json.dumps(serializable, sort_keys=True, indent=2)
