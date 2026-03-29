from typing import List

from schemas import Segment


    
class SegmentPostProcessor: # Постобработка сегментов


    def run(self, segments: List[Segment]) -> List[Segment]:
        segments = self.merge_short_segments(segments)
        segments = self.merge_context_segments(segments)
        segments = self.drop_trash(segments)
        segments = [s for s in segments if s.text.strip()]
        segments = self.deduplicate(segments)
        segments = self.remove_subsegments(segments)
        segments = self.reindex(segments)
        return segments
    
    
    def merge_short_segments(self, segments):
        result = []
        i = 0

        while i < len(segments):
            current = segments[i]

            if (
                i < len(segments) - 1
                and current.sentId == segments[i + 1].sentId
                and current.segmentRole == "main_service"
                and segments[i + 1].segmentRole == "main_service"
                and current.markerType in ("none", "and")
            ):
                nxt = segments[i + 1]

                if nxt.segmentRole == "main_service":
                    merged = Segment(
                        segmentId=current.segmentId,
                        sentId=current.sentId,
                        text=current.text + " " + nxt.text,
                        start=current.start,
                        end=nxt.end,
                        segmentType=current.segmentType,
                        segmentRole=current.segmentRole,
                        hasIndependentMarker=current.hasIndependentMarker,
                        hasDependentMarker=current.hasDependentMarker,
                        markerType=current.markerType,
                    )

                    result.append(merged)
                    i += 2
                    continue

            result.append(current)
            i += 1

        return result
    
    
    def merge_context_segments(self, segments):
        result = []
        buffer = None

        for seg in segments:
            if seg.segmentRole == "context":
                if buffer is None:
                    buffer = Segment(**seg.model_dump())
                else:
                    buffer = Segment(
                        segmentId=buffer.segmentId,
                        sentId=buffer.sentId,
                        text=buffer.text + " " + seg.text,
                        start=buffer.start,
                        end=seg.end,
                        segmentType=buffer.segmentType,
                        segmentRole="context",
                        hasIndependentMarker=False,
                        hasDependentMarker=False,
                        markerType="none",
                    )
            else:
                if buffer:
                    result.append(buffer)
                    buffer = None
                result.append(seg)

        if buffer:
            result.append(buffer)

        return result
    
    
    def drop_trash(self, segments):
        result = []

        for seg in segments:

            text = seg.text.strip()

            if text.endswith(":"):
                continue

            if len(text.split()) <= 1 and seg.segmentRole == "context":
                continue

            result.append(seg)

        return result
    
    
    def reindex(self, segments: List[Segment]) -> List[Segment]:
        for i, seg in enumerate(segments):
            seg.segmentId = i
        return segments
    
    
    def deduplicate(self, segments):
        result = []
        seen = set()

        for seg in segments:
            key = seg.text.strip()
            if key in seen:
                continue
            seen.add(key)
            result.append(seg)

        return result
    
    
    def remove_subsegments(self, segments):
        result = []

        for i, seg in enumerate(segments):
            is_sub = False

            for j, other in enumerate(segments):
                if i == j:
                    continue

                if seg.text != other.text and seg.text in other.text:
                    is_sub = True
                    break

            if not is_sub:
                result.append(seg)

        return result