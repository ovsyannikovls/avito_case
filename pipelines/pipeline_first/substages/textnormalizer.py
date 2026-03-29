import re
import unicodedata


class TextNormalizer: # Нормализация текста (перевод в регистр, убираение лишних пробелов)
    
    
    _NBSP_RE = re.compile(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000\t\f\v]+")
    _MULTISPACE_RE = re.compile(r"[ ]{2,}")
    _MULTINEWLINE_RE = re.compile(r"\n{2,}")
    _BULLETS_RE = re.compile(r"[•●▪◦·∙◆◇▶►▸▹►]")
    _DASHES_RE = re.compile(r"[–—−]")
    _REPEATED_PUNCT_RE = re.compile(r"([.!?,;:+])\1+")
    _SENT_END_RE = re.compile(r"\s*([.!?])\s*")
    _SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,;:.!?])")
    _SPACE_AROUND_NEWLINE_RE = re.compile(r" *\n *")
    
    
    def run(self, text: str) -> str:
        if not text:
            return ""

        text = self._normalize_unicode(text)
        text = self._normalize_case(text)
        text = self._normalize_spaces(text)

        text = self._normalize_symbols(text)
        text = self._normalize_punctuation(text)

        text = self._normalize_brackets(text)
        text = self._normalize_phone(text)

        text = self._final_cleanup(text)

        return text


    def _normalize_unicode(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text


    def _normalize_case(self, text: str) -> str:
        text = text.lower()
        text = text.replace("ё", "е")
        return text


    def _normalize_spaces(self, text: str) -> str:
        text = self._NBSP_RE.sub(" ", text)
        text = self._SPACE_AROUND_NEWLINE_RE.sub("\n", text)
        return text


    def _normalize_symbols(self, text: str) -> str:
        text = self._BULLETS_RE.sub(" ; ", text)
        text = self._DASHES_RE.sub("-", text)
        text = re.sub(r"-{2,}", "-", text)
        text = re.sub(r";{2,}", ";", text)

        return text


    def _normalize_punctuation(self, text: str) -> str:
        text = self._REPEATED_PUNCT_RE.sub(r"\1", text)
        text = re.sub(r"\s*([,;:+|/])\s*", r" \1 ", text)
        text = re.sub(r"\s*([.!?])\s*", r"\1 ", text)
        text = self._SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)

        return text


    def _final_cleanup(self, text: str) -> str:
        text = self._MULTISPACE_RE.sub(" ", text)
        text = self._MULTINEWLINE_RE.sub("\n", text)
        text = text.strip()
        return text
    
    
    def _normalize_brackets(self, text: str) -> str:
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)

        return text
    
    
    def _normalize_phone(self, text: str) -> str:
        text = re.sub(r"\+\s+(\d)", r"+\1", text)

        return text