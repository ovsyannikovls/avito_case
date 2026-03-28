from pydantic import BaseModel
from typing import List, Literal


class MicroCategory(BaseModel):
    mcId: int
    mcTitle: str
    keyPhrases: List[str]


class InputAds(BaseModel):
    itemId: int
    mcId: int
    mcTitle: str
    description: str


class OutputAds(BaseModel):
    mcId: int
    mcTitle: str
    text: str


class Answer(BaseModel):
    shouldSplit: bool
    drafts: List[OutputAds]
    
    
#================ First step ==================

# Задача разбить описание на минимальны смысловые части при этом сохранив контекст


# Формальные предложения после нормализации текста.
# Это верхний уровень разбиения, обычно по . ! ? и переносам строки.
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
    
    
# Инварианты (константы) по завершении первого этапа:
#
# По sentences
#
# предложения не пересекаются;
# порядок соответствует тексту;
# sentId уникален внутри объявления;
# start < end;
# text == normalizedText[start:end] либо хотя бы соответствует этому с точностью до trim.
#
# По segments
#
# каждый сегмент принадлежит ровно одному sentId;
# сегменты лежат внутри соответствующего предложения;
# сегменты не должны пересекаться, если это один уровень сегментации;
# сегмент должен быть минимальной смысловой единицей.
#
# 1. Предобработка (Normalization)
# 2. Выделение сервисных фраз (Service Span Detection)
# 3. Первичный Split (Chunking)
# ...


#================ Second step==================


class SpanCandidate(BaseModel): # Сырое предположение (возможно для проверки уверенности?)
    text: str
    start: int
    end: int
    sentId: int
    segmentId: int
    extractor: str
    evidence: dict = {}


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


