import logging
import random
import json


with open("tests/inputs/inputs.json", "r", encoding="utf-8") as f:
    ads = json.load(f)["ads"]


with open("tests/mc/mc.json", "r", encoding="utf-8") as f:
    microcategories = json.load(f)["microcategories"]


def get_random_ad(mode):
    if mode == "single":
        return random.choice(ads["singleComplexService"])
    elif mode == "multiple":
        return random.choice(ads["multipleIndependentServices"])
    else:
        logging.error("Lack of an argument")
        raise ValueError("mode должен быть 'single' или 'multiple'")
    

def get_mc_by_id(mc_id):
    for mc in microcategories:
        if mc["mcId"] == mc_id:
            return mc
    return None

print(get_mc_by_id(get_random_ad("single")["mcId"]))