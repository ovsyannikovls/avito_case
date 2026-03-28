import re
from typing import List

from schemas import FirstStep, NormalizenSentence, NormalizenSegment
    
    

def normalize_text(text: str) -> str:
    text = text.lower()
    
    # убираем мусорные слова
    noise_words = [
        "недорого", "качественно", "быстро",
        "опыт", "гарантия", "звоните"
    ]
    
    for word in noise_words:
        text = re.sub(rf"\b{word}\b", "", text)
    
    # заменяем нестандартные разделители
    text = text.replace("•", ",")
    text = text.replace("\n", ". ")
    
    # чистка символов
    text = re.sub(r"[^\w\s,.;:-]", " ", text)
    
    # нормализация пробелов
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def split_sentences(text: str) -> List[NormalizenSentence]:
    sentences = []
    
    parts = re.split(r"[.!?]", text)
    
    cursor = 0
    sent_id = 0
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        start = text.find(part, cursor)
        end = start + len(part)
        
        sentences.append(
            NormalizenSentence(
                sentId=sent_id,
                text=part,
                start=start,
                end=end
            )
        )
        
        cursor = end
        sent_id += 1
    
    return sentences

def split_segments(sentences: List[NormalizenSentence]) -> List[NormalizenSegment]:
    segments = []
    segment_id = 0

    for sent in sentences:
        # Разделяем только если есть список/перечисление
        if re.search(r"[,;:-]", sent.text):
            parts = [p.strip() for p in re.split(r"[,;:-]", sent.text) if p.strip()]
            segment_type = "list_item"
        else:
            parts = [sent.text.strip()]
            segment_type = "clause"

        cursor = sent.start
        for part in parts:
            start = sent.text.find(part)
            end = start + len(part)
            # корректируем до глобальных позиций в тексте
            start += sent.start
            end += sent.start

            segments.append(
                NormalizenSegment(
                    segmentId=segment_id,
                    sentId=sent.sentId,
                    text=part,
                    start=start,
                    end=end,
                    segmentType=segment_type
                )
            )
            segment_id += 1

    return segments


# def add_sentence_segments(sentences: List[NormalizenSentence],
#                           segments: List[NormalizenSegment],
#                           start_id: int) -> List[NormalizenSegment]:

#     segment_id = start_id
#     new_segments = []

#     for sent in sentences:
#         # добавляем sentence сегмент только если нет уже полного покрытия
#         is_covered = any(seg.start <= sent.start and seg.end >= sent.end for seg in segments)
#         if not is_covered:
#             new_segments.append(
#                 NormalizenSegment(
#                     segmentId=segment_id,
#                     sentId=sent.sentId,
#                     text=sent.text,
#                     start=sent.start,
#                     end=sent.end,
#                     segmentType="sentence"
#                 )
#             )
#             segment_id += 1

#     return segments + new_segments

# def add_sentence_segments(
#     sentences: List[NormalizenSentence],
#     segments: List[NormalizenSegment],
#     start_id: int
# ) -> List[NormalizenSegment]:
    
#     segment_id = start_id
#     new_segments = []

#     for sent in sentences:
#         # проверяем, есть ли уже сегмент, полностью покрывающий предложение
#         overlap = False
#         for seg in segments:
#             if seg.start <= sent.start and seg.end >= sent.end:
#                 overlap = True
#                 break
        
#         if not overlap:
#             new_segments.append(
#                 NormalizenSegment(
#                     segmentId=segment_id,
#                     sentId=sent.sentId,
#                     text=sent.text,
#                     start=sent.start,
#                     end=sent.end,
#                     segmentType="sentence"
#                 )
#             )
#             segment_id += 1

#     return segments + new_segments

def first_step_pipeline(item: dict) -> FirstStep:
    
    normalized = normalize_text(item["description"])
    
    sentences = split_sentences(normalized)
    
    segments = split_segments(sentences)
    
    # (опционально) добавить sentence-сегменты
    # segments = add_sentence_segments(sentences, segments, len(segments))
    
    return FirstStep(
        itemId=item["itemId"],
        sourceMcId=item["mcId"],
        sourceMcTitle=item["mcTitle"],
        text=item["description"],
        normalizedText=normalized,
        sentences=sentences,
        segments=segments
    )


if __name__ == "__main__":
    
    item = {
        "itemId": 1,
        "mcId": 201,
        "mcTitle": "Ремонт под ключ",
        "description": "Ремонт под ключ: сантехника, электрика, укладка плитки. Быстро и качественно!"
    }
    
    result = first_step_pipeline(item)
    
    print("\n=== NORMALIZED TEXT ===")
    print(result.normalizedText)
    
    print("\n=== SENTENCES ===")
    for s in result.sentences:
        print(s)
    
    print("\n=== SEGMENTS ===")
    for seg in result.segments:
        print(seg)