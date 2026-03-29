from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field
from typing import List
from schemas import FinalResult, Inpution, InputAd, Draft  # Добавил Draft
from web.finder_csv import find_title_id
import random
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # это avito_case/web
TEMPLATES_DIR = BASE_DIR / "templates"

print("Templates path exists?", TEMPLATES_DIR.exists())
import os

print("Template exists?", os.path.exists(TEMPLATES_DIR / "index.html"))
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return FileResponse(TEMPLATES_DIR / "index.html")

router = APIRouter(prefix="/drafts", tags=["drafts"])

# --- POST для черновиков ---
@router.post('/', response_model=InputAd)
def input_desc(inp: Inpution) -> InputAd:
    mcTitle = inp.mcTitle
    description = inp.description
    id = find_title_id(mcTitle)
    
    return InputAd(
        itemId=random.randint(1, 99999),
        sourceMcId=id,
        sourceMcTitle=mcTitle,
        description=description
    )

# --- GET JSON example ---
# @app.get("/json-example", response_model=FinalResult)
# def get_jsons():
#     # Возвращаем пример объекта FinalResult
#     return FinalResult(
#         itemId=123,
#         detectedMcIds=[10, 20],
#         shouldSplit=True,
#         drafts=[
#             Draft(draftId=1, text="Первый черновик"),
#             Draft(draftId=2, text="Второй черновик")
#         ]
#     )

# Подключаем роутер
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("web.main:app", host="127.0.0.1", port=8000, reload=True)

