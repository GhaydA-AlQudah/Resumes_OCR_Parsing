import base64
import os
import tempfile
from utils.logger import logger
logger.info("[+] DocLing File Started...")

logger.info("[+] Importing DocLing Config-converter From DocLing...")
from config import converter
logger.info("[+] Importing DocLing Config-converter From DocLing Done!")



# =========================
# OCR Extraction with DocLing
# =========================
def DocLing_EasyOCR_TextExtractor(file_path: str, file_name: str):
    logger.info(f"[+] Running DocLing on {file_name}...")
    result = converter.convert(file_path)
    text = result.document.export_to_markdown()
    logger.info("[+] Text Extraction Done")
    return text

def DocLing_EasyOCR_TextExtractor_from_base64(file_base64: str, file_name: str):
    logger.info(f"[+] Running DocLing on {file_name} from Base64...")
    file_bytes = base64.b64decode(file_base64)
    suffix = os.path.splitext(file_name)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        result = converter.convert(tmp_path)
        return result.document.export_to_markdown()
    finally:
        os.remove(tmp_path)

# =========================
# LLM Parsing (reuse Paddle function)
# =========================
from ocr.paddle_ocr import parse_with_openrouter, parse_and_validate_resume

logger.info("[+] DocLing File Excecuted!")
