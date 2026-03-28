import json
from pydantic import BaseModel
from typing import List, Literal


from pipeline_second import(
    get_random_first_step,
    run_second_step,
    run_second_step_for_mode,
    run_second_step_for_item_id
)


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


with open("tests_data/mc/mc.json", "r", encoding="utf-8") as f:
    microcategories = json.load(f)["microcategories"]


case = get_random_first_step("basic")
result = run_second_step(case, microcategories)

results = run_second_step_for_mode("lists", microcategories)
one_result = run_second_step_for_item_id(5001, microcategories)

    
print(results[0].model_dump_json(indent=2))

# print(f"Result 1:\n\n", result.model_dump_json(indent=2), 
#     "\n\n\nResult 2:\n\n", one_result.model_dump_json(indent=2))