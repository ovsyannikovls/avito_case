from pipelines.pipeline_second.second_pl_result import get_second_pipeline_result
from pipelines.pipeline_third.pipeline_third import run_third_stage


second_result, first_step = get_second_pipeline_result("single")

third_result = run_third_stage(second_result, first_step)

print("First stage: \n\n\n\n\n", first_step.model_dump_json(indent=2),
      "\n\n\n\n\nSecond stage:\n\n\n\n\n", second_result.model_dump_json(indent=2),
      "\n\n\n\n\nThird stage:", third_result.model_dump_json(indent=2))