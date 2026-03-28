import logging
import random
import json

# ========================= Открытие файлов с тестами ===========================


with open("tests_data/inputs/inputs.json", "r", encoding="utf-8") as f:
    ads = json.load(f)["ads"]


# with open("tests_data/mc/mc.json", "r", encoding="utf-8") as f:
#     microcategories = json.load(f)["microcategories"]


# with open("tests_data/first_step/first_step.json", "r", encoding="utf-8") as f:
#     first_step = json.load(f)["microcategories"]


# ========================= Рандомная выдача для тестов ===========================


def get_random_ad(mode):
    if mode == "single":
        return random.choice(ads["singleComplexService"])
    elif mode == "multiple":
        return random.choice(ads["multipleIndependentServices"])
    else:
        logging.error("Lack of an argument")
        raise ValueError("mode должен быть 'single' или 'multiple'")
    
    
# def get_random_first_step(mode):
#     if mode == "basic":
#         return random.choice(ads["basicExtraction"])
#     elif mode == "lists":
#         return random.choice(ads["listAndEnumeration"])
#     elif mode == "mixed":
#         return random.choice(ads["mixedContextCases"])
#     else:
#         logging.error("Lack of an argument")
#         raise ValueError("mode должен быть 'basic', 'lists' или 'mixed'")
    

# ========================= Прочее ===========================


def get_mc_by_id(mc_id):
    for mc in microcategories:
        if mc["mcId"] == mc_id:
            return mc
    return None