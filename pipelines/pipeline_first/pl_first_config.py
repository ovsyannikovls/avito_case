import re
import json

data = []




SPLIT_PATTERNS = [
    {"type": "strong", "pattern": r","},
    {"type": "strong", "pattern": r";"},
    {"type": "strong", "pattern": r":"},
    {"type": "strong", "pattern": r"\s+\+\s+"},
    {"type": "strong", "pattern": r"\s+/\s+"},
    {"type": "strong", "pattern": r"\s+\|\s+"},
    {"type": "strong", "pattern": r"\s+-\s+"},
    {"type": "strong", "pattern": r"\s+–\s+"},
    {"type": "strong", "pattern": r"\s+—\s+"},
    {"type": "strong", "pattern": r"\n- "},
    {"type": "strong", "pattern": r"^- "},
    {"type": "strong", "pattern": r"\s+можем\s+"},
    {"type": "strong", "pattern": r"\s+выполняем\s+"},
    {"type": "strong", "pattern": r"\s+делаю\s+"},
    {"type": "strong", "pattern": r"\s+делаем\s+"},

    {"type": "and", "pattern": r"\s+а\s+также\s+"},
    {"type": "and", "pattern": r"\s+также\s+"},
    {"type": "and", "pattern": r"\s+плюс\s+"},

    {"type": "including", "pattern": r"\s+включая\s+"},
    {"type": "including", "pattern": r"\s+в\s+том\s+числе\s+"},
    {"type": "including", "pattern": r"\s+с\s+учетом\s+"},
    {"type": "including", "pattern": r"\s+с\s+учётом\s+"},
    {"type": "including", "pattern": r"\s+при\s+необходимости\s+"},
    {"type": "including", "pattern": r"\s+можно\s+"},
    {"type": "including", "pattern": r"\s+как\s+часть\s+"},
    {"type": "including", "pattern": r"\s+в\s+составе\s+"},

    {"type": "separate", "pattern": r"\s+отдельно\s+"},
    {"type": "separate", "pattern": r"\s+раздельно\s+"},
    {"type": "separate", "pattern": r"\s+самостоятельно\s+"},
]


CONTEXT_REGEX = re.compile(
    r"\b("
    r"опыт\w*|стаж\w*|лет|год\w*|"
    r"цен\w*|стоим\w*|руб|₽|прайс\w*|смет\w*|бюджет\w*|"
    r"звон\w*|пиш\w*|лс|тел\w*|номер\w*|контакт\w*|"
    r"whatsapp|telegram|tg|viber|"
    r"выезд\w*|приед\w*|достав\w*|самовывоз\w*|"
    r"срок\w*|сегодня|завтра|сейчас|"
    r"ищу|заказ\w*|"
    r"по\s+отдельн\w*\s+видам\s+работ|"
    r"не\s*выезж\w*|не\s*дела\w*|не\s*работа\w*|"
    r"аккуратн\w*|"
    r"гарант\w*|"
    r"бесплатн\w*|"
    r"бригада\w*|"
    r"замер\w*|"
    r"посредник\w*|"
    r"отвеч\w*|вопрос\w*|"
    r"частн\w*\s+мастер\w*|"
    r"с\s+опыт\w*|"
    r"свободн\w*\s+дат\w*|"
    r"оперативн\w*\s+выезд\w*"
    r")\b"
)


with open("rnc_dataset.jsonl", "r", encoding="utf-8") as rnc_dataset:
    for num, line in enumerate(rnc_dataset, 1):
        if num >= 21:
            break
        data.append(json.loads(line))


