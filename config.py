import os
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat

from utils.logger import logger

logger.info("[+] Config File Started ...")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg", "webp"}

# DocLing default converter
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options = EasyOcrOptions(
    lang=["ar", "en"],    
    confidence_threshold=0.1, 
    suppress_mps_warnings=True,
    force_full_page_ocr=False      
)

converter = DocumentConverter(
    format_options={InputFormat.IMAGE: PdfFormatOption(pipeline_options=pipeline_options)}
)

logger.info("[+] Config Excecuted !")
