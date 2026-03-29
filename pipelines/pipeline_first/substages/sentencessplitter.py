
import re

from typing import List

from schemas import Sentence


class SentencesSplitter: # Разбиение текста на предложения

    _SENT_RE = re.compile(r"[^.!?\n]+")

    def run(self, text: str) -> List[Sentence]:
        sentences = []

        for idx, match in enumerate(self._SENT_RE.finditer(text)):
            raw = match.group()

            left_trim = len(raw) - len(raw.lstrip())
            right_trim = len(raw) - len(raw.rstrip())

            clean_text = raw.strip()
            if not clean_text:
                continue

            start = match.start() + left_trim
            end = match.end() - right_trim

            sentences.append(
                Sentence(
                    sentId=idx,
                    text=clean_text,
                    start=start,
                    end=end,
                )
            )

        return sentences