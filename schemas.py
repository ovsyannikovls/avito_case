from pydantic import BaseModel
from typing import List


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