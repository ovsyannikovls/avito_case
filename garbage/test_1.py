import json
from pipeline_first import first_step_pipeline
# with open('tests_data/inputs/inputs.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)

data = {
  "ads": {
    "singleComplexService": [
      {
        "itemId": 5001,
        "mcId": 201,
        "mcTitle": "Ремонт квартир и домов под ключ",
        "description": "Выполняем ремонт квартир под ключ с полным циклом работ. В стоимость входят демонтаж, электрика, сантехника, выравнивание стен, укладка плитки и чистовая отделка. Берем объект полностью и сдаем готовый результат."
      }
    ]
  }
}

for item in data['ads']['singleComplexService']:
    print('\n=====IZNACHALNY TEXT=======')
    print(item['description'])
    print('==========================')
    result = first_step_pipeline(item)
    print("\n=== NORMALIZED TEXT ===")
    print(result.normalizedText)
    print("\n=== SENTENCES ===")
    for s in result.sentences:
        print(s)
    print("\n=== SEGMENTS ===")
    for seg in result.segments:
        print(seg)

    result_dict = result.dict()
    
    # сериализуем в JSON строку с красивым отступом
    json_output = json.dumps(result_dict, ensure_ascii=False, indent=4)
    
    # выводим
    print(json_output)

# python pipelines/pipeline_first/test_1.py