from typing import List

from schemas import (
    ChunkFeatures,
    Draft,
    SecondStepResult,
    ThirdStageResult
)


INDEPENDENT_MARKERS = [
    "отдельно",
    "отдельно выполняем",
    "можно заказать",
    "можно отдельно",
    "без полного ремонта",
    "только",
]

DEPENDENT_MARKERS = [
    "в составе",
    "в рамках",
    "включая",
    "в том числе",
    "входит в",
    "комплекс",
]


# ============================================================================
# 1. FEATURE EXTRACTION
# ============================================================================

def build_chunk_features(chunk, segment_text) -> ChunkFeatures:
    text = segment_text.lower()

    has_independent = any(m in text for m in INDEPENDENT_MARKERS)
    has_dependent = any(m in text for m in DEPENDENT_MARKERS)

    is_atomic = chunk.chunkType == "atomic"
    is_composite = chunk.chunkType == "composite"
    is_generic = chunk.chunkType == "generic"

    return ChunkFeatures(
        chunkText=chunk.text,
        segmentText=segment_text,
        segmentId=chunk.segmentId,
        chunkType=chunk.chunkType,
        candidateMcIds=chunk.candidateMcIds,
        secondStageScore=chunk.score,

        hasIndependentMarker=has_independent,
        hasDependentMarker=has_dependent,

        isAtomic=is_atomic,
        isComposite=is_composite,
        isGeneric=is_generic,

        thirdStageScore=0.0,
        label="dependent",
        selectedMcId=None,
    )


# ============================================================================
# 2. SCORING
# ============================================================================

def score_chunk(features: ChunkFeatures) -> float:
    score = 0.0

    if features.hasIndependentMarker:
        score += 3.0

    if features.hasDependentMarker:
        score -= 3.0

    if features.isComposite:
        score += 2.0

    if features.isAtomic:
        score += 1.5

    if features.isGeneric:
        score += 0.5

    if features.secondStageScore >= 0.85:
        score += 1.0

    if features.secondStageScore < 0.6:
        score -= 1.0

    return score


# ============================================================================
# 3. CLASSIFICATION
# ============================================================================

def classify(score: float) -> str:
    return "independent" if score >= 1.5 else "dependent"


# ============================================================================
# 4. MC SELECTION
# ============================================================================

def select_mc_id(features: ChunkFeatures) -> int | None:
    if not features.candidateMcIds:
        return None

    # baseline: просто берём первый
    return features.candidateMcIds[0]


# ============================================================================
# 5. DRAFT GENERATION (минимальный)
# ============================================================================

def generate_draft(mcId: int, mcTitle: str, chunk_text: str) -> Draft:
    return Draft(
        mcId=mcId,
        mcTitle=mcTitle,
        text=f"Выполняем {chunk_text} отдельно."
    )


# ============================================================================
# 6. MAIN PIPELINE
# ============================================================================

def run_third_stage(
    second_result: SecondStepResult,
    first_step
) -> ThirdStageResult:

    # map segmentId → text
    segment_map = {
        seg.segmentId: seg.text
        for seg in first_step.segments
    }

    features_list: List[ChunkFeatures] = []

    # 1. build features + classify
    for chunk in second_result.chunks:
        segment_text = segment_map.get(chunk.segmentId, "")

        features = build_chunk_features(chunk, segment_text)

        # score
        score = score_chunk(features)
        features.thirdStageScore = score

        # classify
        features.label = classify(score)

        # select mcId
        if features.label == "independent":
            features.selectedMcId = select_mc_id(features)

        features_list.append(features)

    # =========================================================================
    # 2. AGGREGATION
    # =========================================================================

    detected_mc_ids = set()

    for f in features_list:
        if f.label == "independent" and f.selectedMcId is not None:
            if f.selectedMcId != second_result.sourceMcId:
                detected_mc_ids.add(f.selectedMcId)

    detected_mc_ids = list(detected_mc_ids)

    should_split = len(detected_mc_ids) > 0

    # =========================================================================
    # 3. DRAFTS
    # =========================================================================

    drafts = []

    if should_split:
        for f in features_list:
            if f.label == "independent" and f.selectedMcId in detected_mc_ids:
                drafts.append(
                    generate_draft(
                        mcId=f.selectedMcId,
                        mcTitle=str(f.selectedMcId),  # можно заменить на lookup
                        chunk_text=f.chunkText
                    )
                )

    # =========================================================================
    # 4. RESULT
    # =========================================================================

    return ThirdStageResult(
        itemId=second_result.itemId,
        detectedMcIds=detected_mc_ids,
        shouldSplit=should_split,
        drafts=drafts,
    )