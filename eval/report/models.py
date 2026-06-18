from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class BehavioralResult:
    crash_resolved: Optional[bool]
    detail: str
    source: str

@dataclass
class TestSuiteResult:
    __test__ = False
    passed: Optional[bool]
    total: int
    failed: int
    warnings: int
    detail: str
    source: str

@dataclass
class StructuralResult:
    verdict_label: str
    confidence: float
    locality: Dict[str, Any]
    minimality: Dict[str, Any]
    overlap: Dict[str, Any]

@dataclass
class CombinedVerdict:
    label: str
    confidence: float
    explanation: str
    reasons: List[str]
    required_human_actions: List[str]

@dataclass
class RemediationReport:
    case_id: str
    combined_verdict: CombinedVerdict
    structural: Optional[StructuralResult]
    behavioral: Optional[BehavioralResult]
    test_suite: Optional[TestSuiteResult]
    proof_excerpt: str
    evidence_inputs: Dict[str, Any]
    limitations: List[str]
