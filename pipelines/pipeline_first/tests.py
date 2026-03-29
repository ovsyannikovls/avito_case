import random

from pipelines.pipeline_first.pl_first_config import data
from pipelines.pipeline_first.substages.textnormalizer import TextNormalizer
from pipelines.pipeline_first.substages.sentencessplitter import SentencesSplitter
from pipelines.pipeline_first.substages.segmenter import Segmenter
from pipelines.pipeline_first.substages.segmentpostprocessor import SegmentPostProcessor
from pipelines.pipeline_first.pl_first import FirstStage

from schemas import InputAd


# ====================== Tests ==========================


for _ in range(5):
    test_ad = InputAd.model_validate(data[random.randint(1, 19)])

    test_fpl = FirstStage()
    print(test_ad.model_dump_json(indent=2), "\n\n\n\n\n\n", test_fpl.run(test_ad).model_dump_json(indent=2))