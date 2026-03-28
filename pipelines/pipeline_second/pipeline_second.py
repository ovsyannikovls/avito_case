from __future__ import annotations

import json
import random
import re
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple, Literal
from pydantic import BaseModel


class NormalizenSentence(BaseModel):
    sentId: int
    text: str
    start: int
    end: int
    
    
class NormalizenSegment(BaseModel): # Минимальные смысловые куски, на которые разбивается предложение
    segmentId: int
    sentId: int
    text: str
    start: int
    end: int
    segmentType: Literal["sentence", "clause", "list_item"]


class FirstStep(BaseModel): # Информация в json для перехода на следующий этап пайплайна
    itemId: int
    sourceMcId: int
    sourceMcTitle: str
    text: str
    normalizedText: str
    sentences: List[NormalizenSentence]
    segments: List[NormalizenSegment]


class ServiceChunk(BaseModel): # Смысловые чанки, которые прошли первый этап - присваивание chunkType
    text: str
    start: int
    end: int
    sentId: int
    segmentId: int
    chunkType: Literal["atomic", "composite", "generic"]
    candidateMcIds: List[int]
    score: float | None = None
    evidence: dict | None = None


class SecondStepResult(BaseModel): # Формат для перехода к следующему этапу
    itemId: int
    sourceMcId: int
    chunks: List[ServiceChunk]


# ============================================================================
# 1. БАЗОВЫЕ КОНСТАНТЫ И КОНФИГ
# ============================================================================

DEFAULT_FIRST_STEP_JSON_PATH = "tests_data/first_step/first_step.json"

GROUP_MAP = {
    "basic": "basicExtraction",
    "lists": "listAndEnumeration",
    "mixed": "mixedContextCases",
}

COMPOSITE_MARKERS = {
    "под ключ",
    "комплексный",
    "комплексная",
    "комплексные",
    "полный цикл",
    "весь спектр работ",
    "все виды работ",
}

ACTION_WORDS = {
    "монтаж",
    "демонтаж",
    "установка",
    "замена",
    "укладка",
    "разводка",
    "перенос",
    "подключение",
    "сборка",
    "штукатурка",
    "шпаклевка",
    "покраска",
    "поклейка",
    "ремонт",
}

GENERIC_WORDS = {
    "электрика",
    "сантехника",
    "отделка",
    "демонтаж",
    "ремонт",
    "малярка",
    "плитка",
    "пол",
    "потолок",
    "электромонтаж",
    "плиточный",
    "отделочный",
    "сантехнический",
}

SYNONYMS = {
    "электромонтаж": "электрика",
    "электромонтажные работы": "электрика",
    "сантехнические работы": "сантехника",
    "плиточные работы": "укладка плитки",
}

ACTION_PATTERNS = [
    re.compile(
        r"\b((?:монтаж|демонтаж|установка|замена|укладка|разводка|перенос|подключение|"
        r"поклейка|покраска|штукатурка|шпаклевка|ремонт)\s+[а-яa-z0-9\- ]{1,50})\b"
    ),
]

WORK_PATTERNS = [
    re.compile(r"\b([а-яa-z\-]+(?:ские|ные|овый|овая|овые|ный|ная)\s+работы)\b"),
    re.compile(r"\b(работы\s+по\s+[а-яa-z\- ]{1,30})\b"),
]

LIST_SPLIT_RE = re.compile(r"\s*(?:,|;|/)\s*")


# ============================================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================


try:
    import pymorphy3
    _MORPH = pymorphy3.MorphAnalyzer()
except Exception:
    _MORPH = None


def lemmatize_word(word: str) -> str:
    word = normalize_text(word)
    if not word:
        return word

    if _MORPH is not None:
        try:
            return _MORPH.parse(word)[0].normal_form
        except Exception:
            return word

    # fallback без pymorphy3
    return word


def lemmatize_tokens(text: str) -> List[str]:
    return [lemmatize_word(token) for token in tokenize(text)]


def lemmatize_text(text: str) -> str:
    return " ".join(lemmatize_tokens(text))


def normalize_text(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    return re.findall(r"[а-яa-z0-9\-]+", normalize_text(text))


def canonicalize_text(text: str) -> str:
    text_n = normalize_text(text)
    for src, dst in SYNONYMS.items():
        text_n = text_n.replace(normalize_text(src), normalize_text(dst))
    return lemmatize_text(text_n)


def clamp_score(score: float) -> float:
    return max(0.0, min(1.0, score))


def overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def _ensure_first_step(item: Any) -> FirstStep:
    if isinstance(item, FirstStep):
        return item
    return FirstStep(**item)


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _mc_id(mc: Any) -> int:
    return _get_value(mc, "mcId")


def _mc_title(mc: Any) -> str:
    return _get_value(mc, "mcTitle")


def _mc_key_phrases(mc: Any) -> List[str]:
    return _get_value(mc, "keyPhrases", []) or []


# ============================================================================
# 3. ЗАГРУЗКА ДАННЫХ ПЕРВОГО ЭТАПА ИЗ first_step.json
# ============================================================================

def load_first_step_json(json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH) -> Dict[str, List[FirstStep]]:
    """
    Загружает first_step.json и приводит все кейсы к модели FirstStep.

    Ожидаемый формат файла:
    {
        "basicExtraction": [...],
        "listAndEnumeration": [...],
        "mixedContextCases": [...]
    }
    """
    path = Path(json_path)

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    result: Dict[str, List[FirstStep]] = {}

    for group_name, items in raw.items():
        result[group_name] = [_ensure_first_step(item) for item in items]

    return result


def get_first_steps(mode: str, json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH) -> List[FirstStep]:
    """
    Возвращает все кейсы одной группы:
    - basic
    - lists
    - mixed
    """
    if mode not in GROUP_MAP:
        raise ValueError("mode должен быть 'basic', 'lists' или 'mixed'")

    data = load_first_step_json(json_path)
    return data[GROUP_MAP[mode]]


def get_random_first_step(mode: str, json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH) -> FirstStep:
    """
    Возвращает случайный кейс из first_step.json.
    """
    cases = get_first_steps(mode, json_path)
    return random.choice(cases)


def get_first_step_by_item_id(item_id: int, json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH) -> Optional[FirstStep]:
    """
    Ищет кейс по itemId во всех группах first_step.json.
    """
    data = load_first_step_json(json_path)

    for items in data.values():
        for item in items:
            if item.itemId == item_id:
                return item

    return None


# ============================================================================
# 4. СЛОВАРНЫЙ РЕПОЗИТОРИЙ МИКРОКАТЕГОРИЙ
# ============================================================================

class MicrocategoryRepository:
    """
    Хранилище микрокатегорий + быстрые индексы:
    - phrase -> mcIds
    - token -> mcIds

    Принимает список dict или моделей, главное чтобы были поля:
    - mcId
    - mcTitle
    - keyPhrases
    """

    def __init__(self, microcategories: List[Any]):
        self.microcategories = microcategories

        self.mc_by_id: Dict[int, Any] = {}
        self.phrase_to_mcids: Dict[str, List[int]] = defaultdict(list)
        self.token_to_mcids: Dict[str, List[int]] = defaultdict(list)

        self._build()

    def _build(self) -> None:
        self.mc_by_id = {_mc_id(mc): mc for mc in self.microcategories}
        self.phrase_to_mcids.clear()
        self.token_to_mcids.clear()

        for mc in self.microcategories:
            mc_id = _mc_id(mc)

            for phrase in _mc_key_phrases(mc):
                norm_phrase = canonicalize_text(phrase)
                self.phrase_to_mcids[norm_phrase].append(mc_id)

                for token in self._extract_head_tokens(norm_phrase):
                    self.token_to_mcids[token].append(mc_id)

            norm_title = canonicalize_text(_mc_title(mc))
            for token in self._extract_head_tokens(norm_title):
                self.token_to_mcids[token].append(mc_id)

        for phrase, mc_ids in list(self.phrase_to_mcids.items()):
            self.phrase_to_mcids[phrase] = sorted(set(mc_ids))

        for token, mc_ids in list(self.token_to_mcids.items()):
            self.token_to_mcids[token] = sorted(set(mc_ids))

    def find_phrase_matches(self, text: str) -> List[Dict[str, Any]]:
        text_n = canonicalize_text(text)
        matches = []

        for phrase, mc_ids in self.phrase_to_mcids.items():
            if phrase in text_n:
                matches.append({
                    "phrase": phrase,
                    "mcIds": mc_ids,
                })

        return matches

    def find_token_matches(self, text: str) -> List[int]:
        mc_ids: List[int] = []
        for token in self._extract_head_tokens(text):
            mc_ids.extend(self.token_to_mcids.get(token, []))
        return sorted(set(mc_ids))

    @staticmethod
    def _extract_head_tokens(text: str) -> List[str]:
        return [t for t in tokenize(text) if len(t) >= 4]


# ============================================================================
# 5. EXTRACTORS
# ============================================================================

class DictionaryCandidateExtractor:
    """
    Ищет сервисные candidates по словарным keyPhrases.
    """

    def __init__(self, mc_repo: MicrocategoryRepository):
        self.mc_repo = mc_repo

    def extract(self, first_step: FirstStep) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []

        for segment in first_step.segments:
            seg_text = normalize_text(segment.text)
            matches = self.mc_repo.find_phrase_matches(seg_text)

            for match in matches:
                phrase = match["phrase"]
                local_idx = seg_text.find(phrase)
                if local_idx == -1:
                    continue

                candidates.append({
                    "text": phrase,
                    "start": segment.start + local_idx,
                    "end": segment.start + local_idx + len(phrase),
                    "sentId": segment.sentId,
                    "segmentId": segment.segmentId,
                    "extractor": self.__class__.__name__,
                    "evidence": {
                        "matchType": "dictionary_phrase",
                        "matchedPhrase": phrase,
                        "matchedMcIds": match["mcIds"],
                    },
                })

        return candidates


class PatternCandidateExtractor:
    """
    Ищет сервисные candidates по регулярным паттернам:
    - замена проводки
    - монтаж потолков
    - ремонт ванной
    - сантехнические работы
    """

    def extract(self, first_step: FirstStep) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []

        for segment in first_step.segments:
            seg_text = normalize_text(segment.text)

            for pattern in ACTION_PATTERNS:
                for match in pattern.finditer(seg_text):
                    span_text = match.group(1).strip(" ,.;:-")
                    candidates.append({
                        "text": span_text,
                        "start": segment.start + match.start(1),
                        "end": segment.start + match.end(1),
                        "sentId": segment.sentId,
                        "segmentId": segment.segmentId,
                        "extractor": self.__class__.__name__,
                        "evidence": {
                            "matchType": "action_pattern",
                            "regex": pattern.pattern,
                        },
                    })

            for pattern in WORK_PATTERNS:
                for match in pattern.finditer(seg_text):
                    span_text = match.group(1).strip(" ,.;:-")
                    candidates.append({
                        "text": span_text,
                        "start": segment.start + match.start(1),
                        "end": segment.start + match.end(1),
                        "sentId": segment.sentId,
                        "segmentId": segment.segmentId,
                        "extractor": self.__class__.__name__,
                        "evidence": {
                            "matchType": "work_pattern",
                            "regex": pattern.pattern,
                        },
                    })

        return candidates


class ListCandidateExtractor:
    """
    Разбирает перечисления и list_item сегменты.
    """

    def extract(self, first_step: FirstStep) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []

        for segment in first_step.segments:
            seg_text = normalize_text(segment.text)

            if segment.segmentType not in {"list_item", "sentence", "clause"}:
                continue

            parts = [p.strip(" ,.;:-") for p in LIST_SPLIT_RE.split(seg_text) if p.strip(" ,.;:-")]

            # Критичный фикс:
            # если сегмент уже list_item и сам похож на услугу,
            # возвращаем его как candidate даже без дальнейшего split
            if len(parts) < 2:
                if segment.segmentType == "list_item" and self._looks_like_service(seg_text):
                    candidates.append({
                        "text": seg_text,
                        "start": segment.start,
                        "end": segment.end,
                        "sentId": segment.sentId,
                        "segmentId": segment.segmentId,
                        "extractor": self.__class__.__name__,
                        "evidence": {
                            "matchType": "single_list_item_candidate",
                            "segmentType": segment.segmentType,
                        },
                    })
                continue

            search_cursor = 0
            for part in parts:
                if not self._looks_like_service(part):
                    continue

                local_idx = seg_text.find(part, search_cursor)
                if local_idx == -1:
                    local_idx = seg_text.find(part)
                if local_idx == -1:
                    continue

                search_cursor = local_idx + len(part)

                candidates.append({
                    "text": part,
                    "start": segment.start + local_idx,
                    "end": segment.start + local_idx + len(part),
                    "sentId": segment.sentId,
                    "segmentId": segment.segmentId,
                    "extractor": self.__class__.__name__,
                    "evidence": {
                        "matchType": "list_item_candidate",
                        "segmentType": segment.segmentType,
                    },
                })

        return candidates

    @staticmethod
    def _looks_like_service(text: str) -> bool:
        text_n = normalize_text(text)
        text_l = lemmatize_text(text_n)
        tokens = lemmatize_tokens(text_n)

        if not tokens:
            return False

        if any(marker in text_n for marker in COMPOSITE_MARKERS):
            return True

        if tokens[0] in ACTION_WORDS:
            return True

        if any(token in GENERIC_WORDS for token in tokens):
            return True

        if "работа" in tokens or "работы" in tokens:
            return True

        return False


class CandidateAggregator:
    """
    Собирает candidates от всех extractors.
    """

    def __init__(self, extractors: List[Any]):
        self.extractors = extractors

    def collect(self, first_step: FirstStep) -> List[Dict[str, Any]]:
        all_candidates: List[Dict[str, Any]] = []

        for extractor in self.extractors:
            all_candidates.extend(extractor.extract(first_step))

        return all_candidates


# ============================================================================
# 6. TYPER / MATCHER / SCORER
# ============================================================================

class SpanTyper:
    """
    Определяет тип найденного span:
    - composite
    - atomic
    - generic
    """

    def predict_type(self, candidate: Dict[str, Any], segment_text: str) -> Tuple[str, Dict[str, Any]]:
        text_n = normalize_text(candidate["text"])
        segment_n = normalize_text(segment_text)

        text_l = lemmatize_text(text_n)
        segment_l = lemmatize_text(segment_n)
        tokens = lemmatize_tokens(text_n)

        rules: List[str] = []

        if any(marker in text_n for marker in COMPOSITE_MARKERS):
            rules.append("has_composite_marker")
            return "composite", {"typeRules": rules}

        if text_l.startswith("ремонт") and any(marker in segment_n for marker in COMPOSITE_MARKERS):
            rules.append("repair_span_inside_composite_segment")
            return "composite", {"typeRules": rules}

        if tokens and tokens[0] in ACTION_WORDS and len(tokens) >= 2:
            rules.append("starts_with_action_word_and_has_object")
            return "atomic", {"typeRules": rules}

        if "работа" in tokens or "работы" in tokens:
            rules.append("contains_work_noun")
            return "generic", {"typeRules": rules}

        if any(token in GENERIC_WORDS for token in tokens):
            rules.append("contains_generic_service_word")
            return "generic", {"typeRules": rules}

        rules.append("fallback_generic")
        return "generic", {"typeRules": rules}


class MicrocategoryMatcher:
    """
    Матчит candidate к candidateMcIds.
    """

    def __init__(self, mc_repo: MicrocategoryRepository):
        self.mc_repo = mc_repo

    def match(self, candidate: Dict[str, Any]) -> Tuple[List[int], Dict[str, Any]]:
        text_n = canonicalize_text(candidate["text"])
        evidence: Dict[str, Any] = {"mcMatchRules": []}

        phrase_matches = self.mc_repo.find_phrase_matches(text_n)
        if phrase_matches:
            mc_ids: List[int] = []
            matched_phrases: List[str] = []

            for match in phrase_matches:
                mc_ids.extend(match["mcIds"])
                matched_phrases.append(match["phrase"])

            evidence["mcMatchRules"].append("dictionary_phrase_match")
            evidence["matchedPhrases"] = sorted(set(matched_phrases))
            evidence["matchedMcIds"] = sorted(set(mc_ids))
            return sorted(set(mc_ids)), evidence

        token_mc_ids = self.mc_repo.find_token_matches(text_n)
        if token_mc_ids:
            evidence["mcMatchRules"].append("token_head_match")
            evidence["matchedMcIds"] = token_mc_ids
            return token_mc_ids, evidence

        evidence["mcMatchRules"].append("no_match")
        evidence["matchedMcIds"] = []
        return [], evidence


class ServiceChunkScorer:
    """
    Считает rule-based score.
    """

    def score(
        self,
        candidate: Dict[str, Any],
        chunk_type: str,
        candidate_mc_ids: List[int],
        segment: Any,
        matcher_evidence: Dict[str, Any],
    ) -> float:
        score = 0.0

        extractor_base = {
            "DictionaryCandidateExtractor": 0.82,
            "PatternCandidateExtractor": 0.72,
            "ListCandidateExtractor": 0.68,
        }
        score += extractor_base.get(candidate["extractor"], 0.55)

        if chunk_type == "composite":
            score += 0.12
        elif chunk_type == "atomic":
            score += 0.10
        elif chunk_type == "generic":
            score += 0.05

        if "dictionary_phrase_match" in matcher_evidence.get("mcMatchRules", []):
            score += 0.10
        elif "token_head_match" in matcher_evidence.get("mcMatchRules", []):
            score += 0.05

        if getattr(segment, "segmentType", None) == "list_item":
            score += 0.04

        token_count = len(tokenize(candidate["text"]))
        if token_count == 1:
            score -= 0.05
        elif token_count >= 2:
            score += 0.03

        if not candidate_mc_ids:
            score -= 0.08

        return clamp_score(score)


# ============================================================================
# 7. CONSOLIDATION
# ============================================================================

class ChunkConsolidator:
    """
    Удаляет дубли и схлопывает пересечения.
    """

    TYPE_RANK = {
        "composite": 3,
        "atomic": 2,
        "generic": 1,
    }

    def consolidate(self, chunks: List[ServiceChunk]) -> List[ServiceChunk]:
        if not chunks:
            return []

        chunks = sorted(chunks, key=lambda c: (c.start, -(c.end - c.start), -c.score))
        kept: List[ServiceChunk] = []

        for chunk in chunks:
            merged = False

            for idx, existing in enumerate(kept):
                if self._is_same_span(chunk, existing):
                    kept[idx] = self._merge_same(existing, chunk)
                    merged = True
                    break

                if overlap(chunk.start, chunk.end, existing.start, existing.end):
                    kept[idx] = self._pick_better(existing, chunk)
                    merged = True
                    break

            if not merged:
                kept.append(chunk)

        return sorted(kept, key=lambda c: (c.start, c.end))

    @staticmethod
    def _is_same_span(a: ServiceChunk, b: ServiceChunk) -> bool:
        return (
            a.sentId == b.sentId
            and a.segmentId == b.segmentId
            and a.start == b.start
            and a.end == b.end
            and normalize_text(a.text) == normalize_text(b.text)
        )

    def _merge_same(self, a: ServiceChunk, b: ServiceChunk) -> ServiceChunk:
        merged_mc_ids = sorted(set(a.candidateMcIds + b.candidateMcIds))
        merged_evidence = {**a.evidence, **b.evidence}

        better = self._pick_better(a, b)
        better.candidateMcIds = merged_mc_ids
        better.evidence = merged_evidence
        better.score = max(a.score, b.score)
        return better

    def _pick_better(self, a: ServiceChunk, b: ServiceChunk) -> ServiceChunk:
        rank_a = self.TYPE_RANK[a.chunkType]
        rank_b = self.TYPE_RANK[b.chunkType]

        if rank_a != rank_b:
            return a if rank_a > rank_b else b

        len_a = a.end - a.start
        len_b = b.end - b.start
        if len_a != len_b:
            return a if len_a > len_b else b

        if a.score != b.score:
            return a if a.score >= b.score else b

        return a


# ============================================================================
# 8. MAIN PIPELINE
# ============================================================================

class ServiceSpanPipeline:
    """
    Главный оркестратор второго этапа.
    """

    def __init__(
        self,
        aggregator: CandidateAggregator,
        typer: SpanTyper,
        matcher: MicrocategoryMatcher,
        scorer: ServiceChunkScorer,
        consolidator: ChunkConsolidator,
    ):
        self.aggregator = aggregator
        self.typer = typer
        self.matcher = matcher
        self.scorer = scorer
        self.consolidator = consolidator

    def run(self, first_step: FirstStep) -> SecondStepResult:
        candidates = self.aggregator.collect(first_step)
        raw_chunks: List[ServiceChunk] = []

        for candidate in candidates:
            segment = self._get_segment(first_step, candidate["segmentId"])
            if segment is None:
                continue

            chunk_type, type_evidence = self.typer.predict_type(candidate, segment.text)
            mc_ids, matcher_evidence = self.matcher.match(candidate)
            score = self.scorer.score(
                candidate=candidate,
                chunk_type=chunk_type,
                candidate_mc_ids=mc_ids,
                segment=segment,
                matcher_evidence=matcher_evidence,
            )

            evidence = {
                **candidate.get("evidence", {}),
                **type_evidence,
                **matcher_evidence,
                "extractor": candidate["extractor"],
            }

            raw_chunks.append(
                ServiceChunk(
                    text=candidate["text"],
                    start=candidate["start"],
                    end=candidate["end"],
                    sentId=candidate["sentId"],
                    segmentId=candidate["segmentId"],
                    chunkType=chunk_type,
                    candidateMcIds=mc_ids,
                    score=score,
                    evidence=evidence,
                )
            )

        final_chunks = self.consolidator.consolidate(raw_chunks)

        return SecondStepResult(
            itemId=first_step.itemId,
            sourceMcId=first_step.sourceMcId,
            chunks=final_chunks,
        )

    @staticmethod
    def _get_segment(first_step: FirstStep, segment_id: int) -> Optional[Any]:
        for segment in first_step.segments:
            if segment.segmentId == segment_id:
                return segment
        return None


# ============================================================================
# 9. FACTORY
# ============================================================================

def build_second_step_pipeline(microcategories: List[Any]) -> ServiceSpanPipeline:
    """
    Собирает baseline pipeline второго этапа.
    """
    mc_repo = MicrocategoryRepository(microcategories)

    extractors = [
        DictionaryCandidateExtractor(mc_repo),
        PatternCandidateExtractor(),
        ListCandidateExtractor(),
    ]

    return ServiceSpanPipeline(
        aggregator=CandidateAggregator(extractors),
        typer=SpanTyper(),
        matcher=MicrocategoryMatcher(mc_repo),
        scorer=ServiceChunkScorer(),
        consolidator=ChunkConsolidator(),
    )


# ============================================================================
# 10. HIGH-LEVEL FUNCTIONS ДЛЯ ВЫЗОВА СНАРУЖИ
# ============================================================================

def run_second_step(
    first_step: FirstStep | Dict[str, Any],
    microcategories: List[Any],
) -> SecondStepResult:
    """
    Прогон второго этапа по одному FirstStep.
    """
    pipeline = build_second_step_pipeline(microcategories)
    first_step_model = _ensure_first_step(first_step)
    return pipeline.run(first_step_model)


def run_second_step_for_mode(
    mode: str,
    microcategories: List[Any],
    json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH,
) -> List[SecondStepResult]:
    """
    Прогон второго этапа по всей группе из first_step.json:
    - basic
    - lists
    - mixed
    """
    pipeline = build_second_step_pipeline(microcategories)
    cases = get_first_steps(mode, json_path)
    return [pipeline.run(case) for case in cases]


def run_second_step_for_random_case(
    mode: str,
    microcategories: List[Any],
    json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH,
) -> SecondStepResult:
    """
    Прогон второго этапа по случайному кейсу группы.
    """
    pipeline = build_second_step_pipeline(microcategories)
    case = get_random_first_step(mode, json_path)
    return pipeline.run(case)


def run_second_step_for_item_id(
    item_id: int,
    microcategories: List[Any],
    json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH,
) -> SecondStepResult:
    """
    Прогон второго этапа по itemId из first_step.json.
    """
    pipeline = build_second_step_pipeline(microcategories)
    case = get_first_step_by_item_id(item_id, json_path)

    if case is None:
        raise ValueError(f"itemId={item_id} не найден в first_step.json")

    return pipeline.run(case)


def iter_second_step_results(
    microcategories: List[Any],
    json_path: str | Path = DEFAULT_FIRST_STEP_JSON_PATH,
    modes: Optional[Iterable[str]] = None,
) -> Iterable[SecondStepResult]:
    """
    Генератор результатов второго этапа.
    Если modes=None, пройдет по всем группам.
    """
    pipeline = build_second_step_pipeline(microcategories)
    data = load_first_step_json(json_path)

    if modes is None:
        group_names = list(data.keys())
    else:
        group_names = [GROUP_MAP[m] for m in modes]

    for group_name in group_names:
        for case in data[group_name]:
            yield pipeline.run(case)


# ============================================================================
# 11. EXTENSION POINTS
# ============================================================================
# Если потом захочешь расширять файл, то обычно делается так:
#
# 1) новый extractor:
#       class SynonymCandidateExtractor: ...
#       и добавить его в build_second_step_pipeline()
#
# 2) новый typer:
#       class MLSpanTyper(SpanTyper): ...
#
# 3) новый matcher:
#       class EmbeddingMicrocategoryMatcher(MicrocategoryMatcher): ...
#
# 4) новый scorer:
#       class LearnedScorer(ServiceChunkScorer): ...
#
# 5) новый postprocessor:
#       например фильтр по score или merge по semantic similarity
# ============================================================================