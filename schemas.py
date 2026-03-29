from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal


# =========================
# INPUT / DICTIONARY
# =========================

class MicroCategory(BaseModel):
    mcId: int
    mcTitle: str
    keyPhrases: List[str]
    description: Optional[str] = None


class InputAd(BaseModel):
    itemId: int
    sourceMcId: int
    sourceMcTitle: str
    description: str


# =========================
# FIRST STAGE — SEGMENTATION
# =========================

class Sentence(BaseModel):
    sentId: int
    text: str
    start: int
    end: int


class Segment(BaseModel):
    segmentId: int
    sentId: int

    text: str
    start: int
    end: int

    segmentType: Literal["sentence", "clause", "list_item"]

    segmentRole: Literal[
        "main_service",
        "separate_service",
        "included_service",
        "context"
    ]

    hasIndependentMarker: bool
    hasDependentMarker: bool

    markerType: Optional[Literal[
        "separate",
        "including",
        "and",
        "none"
    ]]


class FirstStageResult(BaseModel):
    itemId: int
    sourceMcId: int
    sourceMcTitle: str

    rawText: str
    normalizedText: str

    sentences: List[Sentence]
    segments: List[Segment]


# =========================
# SECOND STAGE — SPAN EXTRACTION; Переписать полностью оставшиеся контракты с учетом того что может принять нейронка
# =========================


class CandidateSource(BaseModel):
    segmentId: int
    sentId: int

    role: Literal[
        "main_service",
        "separate_service",
        "included_service"
    ]

    markerType: Optional[Literal[
        "separate",
        "including",
        "and",
        "none"
    ]] = None

    hasIndependentMarker: bool = False
    hasDependentMarker: bool = False


class ServiceCandidate(BaseModel):
    candidateId: int

    rawText: str
    normalizedText: str
    canonicalText: Optional[str] = None

    sources: List[CandidateSource] = Field(default_factory=list)

    hasIndependentMarker: bool = False
    hasDependentMarker: bool = False

    markerTypes: List[Literal[
        "separate",
        "including",
        "and",
        "none"
    ]] = Field(default_factory=list)

    hasNegation: bool = False

    builderType: Literal[
        "segment",
        "split",
        "merge",
        "hybrid"
    ] = "segment"

    buildConfidence: float = 1.0


class CandidateCategoryScore(BaseModel):
    mcId: int
    score: float

    matchedPhrases: List[str] = Field(default_factory=list)

    matchType: Literal[
        "exact",
        "partial",
        "semantic"
    ]

    numMatches: int = 0


class ScoredCandidate(BaseModel):
    candidate: ServiceCandidate

    categoryScores: List[CandidateCategoryScore] = Field(default_factory=list)

    selectedMcId: Optional[int] = None
    selectedScore: Optional[float] = None

    secondMcId: Optional[int] = None
    secondScore: Optional[float] = None

    scoreGap: Optional[float] = None


class SecondStageResult(BaseModel):
    itemId: int
    sourceMcId: int

    candidates: List[ScoredCandidate] = Field(default_factory=list)


# =========================
# THIRD STAGE — CLASSIFICATION + ML
# =========================

class CategoryEvidence(BaseModel):
    mcId: int

    candidateIds: List[int] = Field(default_factory=list)

    bestCandidateId: Optional[int] = None
    bestScore: float = 0.0
    secondBestScore: float = 0.0

    totalCandidates: int = 0
    totalMatchedPhrases: int = 0

    hasIndependentMarker: bool = False
    hasDependentMarker: bool = False
    hasNegation: bool = False

    hasMainRole: bool = False
    hasSeparateRole: bool = False
    hasIncludedRole: bool = False

    hasExactMatch: bool = False
    hasPartialMatch: bool = False
    hasSemanticMatch: bool = False

    isSourceCategory: bool = False


class CategoryFeatures(BaseModel):
    mcId: int

    bestScore: float = 0.0
    secondBestScore: float = 0.0
    scoreGap: float = 0.0

    totalCandidates: int = 0
    totalMatchedPhrases: int = 0

    hasIndependentMarker: bool = False
    hasDependentMarker: bool = False
    hasNegation: bool = False

    hasMainRole: bool = False
    hasSeparateRole: bool = False
    hasIncludedRole: bool = False

    hasExactMatch: bool = False
    hasPartialMatch: bool = False
    hasSemanticMatch: bool = False

    isSourceCategory: bool = False


class CategoryDecision(BaseModel):
    mcId: int

    isDetected: bool
    isIndependent: bool

    detectionConfidence: float = 0.0
    splitConfidence: float = 0.0

    decisionType: Literal[
        "source_only",
        "dependent",
        "independent",
        "rejected"
    ]


class ThirdStageResult(BaseModel):
    itemId: int
    sourceMcId: int

    detectedMcIds: List[int] = Field(default_factory=list)

    independentMcIds: List[int] = Field(default_factory=list)
    dependentMcIds: List[int] = Field(default_factory=list)

    shouldSplit: bool = False

    categoryEvidences: List[CategoryEvidence] = Field(default_factory=list)
    categoryFeatures: List[CategoryFeatures] = Field(default_factory=list)
    categoryDecisions: List[CategoryDecision] = Field(default_factory=list)


# =========================
# FINAL — DRAFT GENERATION
# =========================

class Draft(BaseModel):
    mcId: int
    mcTitle: str
    text: str

    sourceCandidateIds: Optional[int]


class FinalResult(BaseModel):
    itemId: int

    detectedMcIds: List[int]
    shouldSplit: bool

    drafts: List[Draft] = Field(default_factory=list)

# =========================
# INPUT
# =========================

class Inpution(BaseModel):
    mcTitle: str
    description: str