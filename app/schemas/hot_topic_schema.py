from pydantic import BaseModel
from typing import List, Dict

class SummaryItem(BaseModel):
    publisher: str
    summary: str
    article_id: int

class HotTopicGroup(BaseModel):
    진보: List[SummaryItem]
    중립: List[SummaryItem]
    보수: List[SummaryItem]

class HotTopicOut(BaseModel):
    id: int
    name: str
    groups: HotTopicGroup
