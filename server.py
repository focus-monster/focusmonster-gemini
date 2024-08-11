from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from PIL import Image
import io

import requests

import google.generativeai as genai
from google.api_core.exceptions import *

app = FastAPI()

genai.configure(api_key='Internal Value')
model = genai.GenerativeModel('gemini-1.5-flash')

class SendChatRequest(BaseModel):
    chatToken: str
    newMessage: str
    history: list = []

class EvaluateRequest(BaseModel):
    history: str

image_prompt_kr = """Internal Script""" 

image_prompt_en = """Internal Script""" 

safety_settings=[
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

async def addHistory(foucsId, history):
    data = {
        "focusId": foucsId,
        "history": history
    }

    requests.post("https://focusmonster.me:8080/focus/history", json=data)
    return "Success"

async def validFocus(foucsId, socialId):
    data = {
        "focusId": foucsId,
        "socialId": socialId
    }

    response = requests.post("https://focusmonster.me:8080/gemini/focus", json=data)
    return {'code': response.status_code, 'reason': response.reason}

# 이미지 업로드 엔드포인트
@app.post("/image")
async def upload_image(socialId: str, focusId: str, file: UploadFile):
    result = validFocus(focusId, socialId)

    if (result['code'] != 200):
        return result['reason']

    contents = await file.read()
    
    image = Image.open(io.BytesIO(contents))
    history = model.generate_content(contents=[image_prompt_en, image], safety_settings=safety_settings).text
    return await addHistory(focusId, history)

# 이미지 업로드 엔드포인트
@app.post("/evaluate")
async def evaluate(request: EvaluateRequest):
    print(request.history)

    result = model.generate_content(contents=[request.history], safety_settings=safety_settings)
    for candidate in result.candidates:
        print(candidate.safety_ratings)
    
    return result.text