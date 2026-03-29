from schemas import InputAd, FirstStageResult
from pipelines.pipeline_first.substages.textnormalizer import TextNormalizer
from pipelines.pipeline_first.substages.sentencessplitter import SentencesSplitter
from pipelines.pipeline_first.substages.segmenter import Segmenter
from pipelines.pipeline_first.substages.segmentpostprocessor import SegmentPostProcessor


class FirstStage: # Первый этап пайплайна
    
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.sentences = SentencesSplitter()
        self.segmenter = Segmenter()
        self.postprocessor = SegmentPostProcessor()
        
        
    def run(self, ad: InputAd) -> FirstStageResult:
        
        normalized_text = self.normalizer.run(ad.description)
        
        sentences = self.sentences.run(normalized_text)
        
        segments = self.segmenter.run(sentences)
        
        segments = self.postprocessor.run(segments)
        
        return FirstStageResult(
            itemId = ad.itemId,
            sourceMcId = ad.sourceMcId,
            sourceMcTitle = ad.sourceMcTitle,
            rawText = ad.description,
            normalizedText = normalized_text,
            sentences = sentences,
            segments = segments,
        )