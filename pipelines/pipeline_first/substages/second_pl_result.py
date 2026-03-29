import json
from typing import Literal
from pipelines.pipeline_first.pipeline_first import first_step_pipeline
from services import get_random_ad

from schemas import SecondStepResult

from pipelines.pipeline_second.pipeline_second import(
    run_second_step
) # Прикольный импорт


with open("tests_data/mc/mc.json", "r", encoding="utf-8") as f:
    microcategories = json.load(f)["microcategories"]


def get_second_pipeline_result(chapter: Literal["single", "multiple"]) -> SecondStepResult:
    
    first_step = first_step_pipeline(get_random_ad(chapter))
    
    return run_second_step(first_step, microcategories), first_step
