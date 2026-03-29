from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


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
    segmentRole: Literal["main_service", "included_service", "separate_service", "context"]
    hasIndependentMarker: bool
    hasDependentMarker: bool
    markerType: Optional[Literal["separate", "including", "and"]]


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
    chunkType: Literal[
    "atomic_independent",
    "atomic_dependent",
    "composite_independent",
    "composite_dependent",
    "generic"]
    candidateMcIds: List[int]
    score: float | None = None
    evidence: dict | None = None
    spanStart: int
    spanEnd: int
    spanText: str


class SecondStepResult(BaseModel): # Формат для перехода к следующему этапу
    itemId: int
    sourceMcId: int
    chunks: List[ServiceChunk]


#================ Third step ==================


class ThirdStepInput(BaseModel): # Соединяем файлы из второго и первого шага для проверки каждого чанка внутри контекста
    secondStage: SecondStepResult
    segments: List[NormalizenSegment]
    
    
class ChunkFeatures(BaseModel): # Признаки одного чанка, по которым будет определяться его релевантность
    chunkText: str
    segmentText: str
    chunkType: str
    candidateMcIds: List[int]
    candidateMcScores: Dict[int, float]
    candidateMcScores: Dict[int, float]
    topKMcIds: List[int]
    secondStageScore: float
    segmentId: int

    hasIndependentMarker: bool
    hasDependentMarker: bool

    isAtomic: bool
    isComposite: bool
    isGeneric: bool

    thirdStageScore: float
    label: Literal["independent", "dependent"]
                   
    
class Draft(BaseModel): # Концептуально - новое объявление, которое система предлагает создать (возможно использовать для дальнейшего создания текста черновика)
    mcId: int
    mcTitle: str
    text: str


class ThirdStageResult(BaseModel): # Финальный результат третьего этапа
    itemId: int
    detectedMcIds: List[int]
    shouldSplit: bool # Решаем, делать ли сплит в принципе
    drafts: List[Draft] = Field(default_factory=list)