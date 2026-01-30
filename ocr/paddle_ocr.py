import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


from paddleocr import PaddleOCR
import os
from typing import List
import json
import re
from utils.logger import logger
logger.info("[+] logger Imported from paddle_ocr.")

logger.info("[+] Importing resume_pydantic_model from paddle_ocr...")
from models.resume_pydantic_model import ResumeModel
logger.info("[+] Importing resume_pydantic_model from paddle_ocr Done!")

from config import UPLOAD_FOLDER

logger.info("[+] Paddle File Started...")
# =========================
# OCR Engine Configuration
# =========================
def OCR_engine_config():
    logger.info("[+] Loading PaddleOCR models...")

    ocr = PaddleOCR(
        lang="ar",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False
    )

    logger.info("[+] PaddleOCR Models Loaded Successfully!")
    return ocr

# =========================
# OCR Extraction
# =========================
def paddle_text_extractor(file_path: str, ocr_instance, file_name: str):
    logger.info(f"[+] Running PaddleOCR on {file_name}...")
    result = ocr_instance.predict(file_path)

    full_text = []
    for page in result:
        rec_texts = page["rec_texts"]
        full_text.extend(rec_texts)

    final_text = "\n".join(full_text)
    logger.info("[+] Text Extraction Done!")
    return final_text, result

# =========================
# LLM Parsing
# =========================
import requests

def parse_with_openrouter(extracted_text: str):
    logger.info("[+] Sending text to OpenRouter LLM...")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer YOUR KEY", 
        "HTTP-Referer": "http://localhost",
        "X-Title": "Resume Parser Script"
    }

    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {
                "role": "system",
                "content": (
                        "You are a resume parser.\n"
                        "Return ONLY valid JSON.\n"
                        "NO markdown. NO explanations.\n"
                        "ALL fields must be STRINGS or LIST OF STRINGS.\n"
                        "NO objects, NO nested JSON.\n\n"
                        "Schema:\n"
                        "{\n"
                        "  name: string|null,\n"
                        "  phone: string|null,\n"
                        "  email: string|null,\n"
                        "  education: string[],\n"
                        "  experience: string[],\n"
                        "  skills: string[],\n"
                        "  languages: string[]\n"
                        "}"
                )
            },
            {"role": "user", "content": extracted_text}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    


    if "choices" not in data:
        logger.error(f"[LLM ERROR] OpenRouter response: {data}")
        raise ValueError("LLM response missing 'choices'")

    content = data["choices"][0]["message"]["content"]
    logger.info("[+] LLM Parsing Done!")

    return content

# =========================
# JSON Validation
# =========================
from pydantic import ValidationError

def parse_and_validate_resume(raw_llm_output: str) -> ResumeModel:
    logger.info("[+] Cleaning & validating LLM output")
    cleaned = re.sub(r"```", "", raw_llm_output).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("No JSON found in LLM output")
    json_data = json.loads(match.group(0))

    try:
        resume = ResumeModel(**json_data)
        logger.info("[+] Resume validated successfully with Pydantic")
        return resume
    except ValidationError as e:
        logger.error("[!] Pydantic validation failed")
        raise e

# =========================
# Visualization 
# =========================
def visualize_paddle_detection_recognition(result, output_folder=UPLOAD_FOLDER):
    os.makedirs(output_folder, exist_ok=True)
    logger.info("[+] Saving PaddleOCR visualizations...")
    for res in result:
        res.save_to_img(output_folder)
        res.save_to_json(output_folder)
    logger.info(f"[DEBUG] Upload folder absolute path: {os.path.abspath(output_folder)}")



logger.info("[+] Paddle File Excecuted!")

