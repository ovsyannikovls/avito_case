import re

from typing import List

from schemas import Segment, Sentence
from pipelines.pipeline_first.substages.sentencessplitter import SentencesSplitter
from pipelines.pipeline_first.pl_first_config import SPLIT_PATTERNS, CONTEXT_REGEX




class Segmenter: # Разбиение предложений на сигменты


    def __init__(self):
        self.clause_splitter = ClauseSplitter()
        self.marker_detector = MarkerDetector()
        self.role_assigner = RoleAssigner()


    def run(self, sentences: List[Sentence]) -> List[Segment]:

        segments = []
        segment_id = 0

        for sent in sentences:

            clauses = self.clause_splitter.run(sent)

            for clause in clauses:

                marker = self.marker_detector.run(clause)

                role = self.role_assigner.run(clause, marker)

                segment_type = "sentence" if len(clauses) == 1 else "clause"

                segment = Segment(
                    segmentId=segment_id,
                    sentId=sent.sentId,

                    text=clause["text"],
                    start=clause["start"],
                    end=clause["end"],

                    segmentType=segment_type,
                    segmentRole=role,

                    hasIndependentMarker=marker["hasIndependentMarker"],
                    hasDependentMarker=marker["hasDependentMarker"],
                    markerType=marker["markerType"] if marker["markerType"] != "none" else None,
                )

                segments.append(segment)
                segment_id += 1

        return segments
    
    

class ClauseSplitter:


    def __init__(self):
        self.patterns = SPLIT_PATTERNS
        self.split_re = self._build_regex()


    def _build_regex(self):
        parts = []
        self.group_to_type = {}

        for i, p in enumerate(self.patterns):
            group_name = f"g{i}"
            parts.append(f"(?P<{group_name}>{p['pattern']})")
            self.group_to_type[group_name] = p["type"]

        return re.compile("|".join(parts))
    
    
    def run(self, sentence: Sentence) -> list:
        text = sentence.text
        base = sentence.start

        clauses = []
        last = 0
        clause_id = 0

        for match in self.split_re.finditer(text):
            start = match.start()
            end = match.end()

            raw = text[last:start]

            if raw.strip():
                left_trim = len(raw) - len(raw.lstrip())
                right_trim = len(raw) - len(raw.rstrip())

                clause_start = base + last + left_trim
                clause_end = base + start - right_trim

                clauses.append({
                    "clauseId": clause_id,
                    "text": raw.strip(),
                    "start": clause_start,
                    "end": clause_end,
                    "separatorType": None
                })

                clause_id += 1

            sep_type = None
            for gname, value in match.groupdict().items():
                if value is not None:
                    sep_type = self.group_to_type[gname]
                    break

            if clauses:
                clauses[-1]["separatorType"] = sep_type

            last = end

        raw = text[last:]
        if raw.strip():
            left_trim = len(raw) - len(raw.lstrip())
            right_trim = len(raw) - len(raw.rstrip())

            clause_start = base + last + left_trim
            clause_end = base + len(text) - right_trim

            clauses.append({
                "clauseId": clause_id,
                "text": raw.strip(),
                "start": clause_start,
                "end": clause_end,
                "separatorType": None
            })

        return clauses
    
    

class MarkerDetector:


    def __init__(self):
        self.SEPARATE_REGEX = re.compile(r"\bотдельн\w*\b")
        self.INCLUDING_REGEX = re.compile(
            r"\bвключа\w*\b|\bв\s+том\s+числе\b"
        )


    def run(self, clause):

        sep_signal = self.detect_from_separator(clause["separatorType"])
        text_signal = self.detect_from_text(clause["text"])

        return self.merge(sep_signal, text_signal)


    def detect_from_separator(self, sep_type):

        if sep_type == "separate":
            return {
                "hasIndependentMarker": True,
                "hasDependentMarker": False,
                "markerType": "separate"
            }

        if sep_type == "including":
            return {
                "hasIndependentMarker": False,
                "hasDependentMarker": True,
                "markerType": "including"
            }

        if sep_type == "and":
            return {
                "hasIndependentMarker": False,
                "hasDependentMarker": False,
                "markerType": "and"
            }

        return {
            "hasIndependentMarker": False,
            "hasDependentMarker": False,
            "markerType": "none"
        }


    def detect_from_text(self, text):

        if self.SEPARATE_REGEX.search(text):
            return {
                "hasIndependentMarker": True,
                "hasDependentMarker": False,
                "markerType": "separate"
            }

        if self.INCLUDING_REGEX.search(text):
            return {
                "hasIndependentMarker": False,
                "hasDependentMarker": True,
                "markerType": "including"
            }

        return {
            "hasIndependentMarker": False,
            "hasDependentMarker": False,
            "markerType": "none"
        }

    def merge(self, sep_signal, text_signal):
        if sep_signal["markerType"] != "none":
            return sep_signal
        return text_signal
    
    
TAIL_CONTEXT = re.compile(
        r"\b(звон\w*|пиш\w*|лс|тел\w*|выезд\w*|замер\w*|бригада\w*).*?$"
    )


def clean_tail(text: str) -> str:
        
    return TAIL_CONTEXT.sub("", text).strip()


SERVICE_VERBS = re.compile(r"\b(делаю|делаем|выполняем|оказываю)\b")
SERVICE_NOUNS = re.compile(r"\b(монтаж|укладка|ремонт|установка)\b")


class RoleAssigner:

    def run(self, clause, marker):

        raw_text = clause["text"]
        text = clean_tail(raw_text)

        words = text.split()
        word_count = len(words)

        if marker["markerType"] == "separate" and word_count > 1:
            return "separate_service"

        if marker["markerType"] == "including":
            return "included_service"

        if word_count == 1:
            return "context"

        if SERVICE_VERBS.search(text):
            return "main_service"

        if SERVICE_NOUNS.search(text) and word_count <= 4:
            return "main_service"

        if CONTEXT_REGEX.search(text) and word_count <= 5:
            return "context"

        return "main_service"