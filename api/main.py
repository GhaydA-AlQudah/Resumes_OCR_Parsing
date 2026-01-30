print('[+] Main File Started ...')

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse

from utils.logger import logger
logger.info("[+] loggers called from Main File ...")

logger.info("[+] Main File Started ...")

logger.info("[+] Importing config-allowed-upload From Main File ...")
from config import ALLOWED_EXT, UPLOAD_FOLDER
logger.info("[+] Importing config-allowed-upload From Main File Done!")

logger.info("[+] Importing resume_pydantic_model From Main File ...")
from models.resume_pydantic_model import ResumeModel
logger.info("[+] Importing resume_pydantic_model From Main File Done!")


logger.info("[+] Importing paddle_ocr File ...")
from ocr.paddle_ocr import OCR_engine_config, paddle_text_extractor, parse_with_openrouter, parse_and_validate_resume, visualize_paddle_detection_recognition
logger.info("[+] Importing paddle_ocr File Done!")

ocr_instance = OCR_engine_config()

logger.info("[+] Importing docling_ocr File ...")
from ocr.docling_ocr import DocLing_EasyOCR_TextExtractor

import shutil
import os


app = FastAPI()
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#####
# Libraries
#####


from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Optional
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Header

# ========================
# SECURITY
# ========================
SECRET_KEY = "MY_SUPER_SECRET_KEY_2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# passlib context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# ========================
# DATABASE (FAKE)
# ========================
fake_users_db = {
    "ghayda": {
        "username": 'ghayda',
        "full_name": None,
        "email": None,
        "disabled": False,
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$Wzqkp1Xp4VI41imxMPPpZg$eyw2pCVovjiGcJiAq9JCKdUPiTrlDlVbCZZDC1V0DV8"

    }
}

# ========================
# MODELS
# ========================
class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ========================
# HELPERS
# ========================
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def get_user(username: str):
    user = fake_users_db.get(username)
    if user:
        return UserInDB(**user)
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ========================
# REGISTER
# ========================
@app.post("/register")
def register(username: str, password: str):
    if username in fake_users_db:
        raise HTTPException(400, "User already exists")

    hashed_pass = get_password_hash(password)
    fake_users_db[username] = {
        "username": username,
        "full_name": None,
        "email": None,
        "disabled": False,
        "hashed_password": hashed_pass,
    }
    return {"msg": "User registered successfully"}

# ========================
# LOGIN → RETURNS TOKEN
# ========================


@app.post("/login", response_model=Token)
async def login(    
    user_name: str ,
    password: str ,
):
    user = authenticate_user(user_name, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ========================
# GET CURRENT USER
# ========================
# ========================
# GET CURRENT USER using  client_secret
# ========================
async def get_current_user(
    client_secret: str = Header(...),
):
    if not client_secret:
        raise HTTPException(status_code=401, detail="Missing client_secret")

    try:
        payload = jwt.decode(client_secret, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid client_secret")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid client_secret")

    user = get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user



# ========================
# PROTECTED ENDPOINT
# ========================
@app.post("/Protected-Resume-PaddleParser")
def protected_parser_funct(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...)
):
    


    logger.info(f"[+] PaddleOCR Used.")
    try:

        # Safe file checks
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")

        if "." not in file.filename:
            raise HTTPException(status_code=400, detail="Invalid file name")

        file_ext = file.filename.split(".")[-1].lower()
        logger.info(f"[+] {file.filename} Uploaded.")


        if file_ext not in ALLOWED_EXT:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_ext}' is not supported. Allowed: {', '.join(ALLOWED_EXT)}"
            )

        # Save file
        safe_file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(safe_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # OCR
        extracted_text, result = paddle_text_extractor(safe_file_path, ocr_instance, file.filename)

        # LLM Parsing
        raw_llm_output = parse_with_openrouter(extracted_text)

        parsed_json = parse_and_validate_resume(raw_llm_output)
        final_json = parsed_json.model_dump()

        visualize_paddle_detection_recognition(result)

        logger.info(f"[+] {file.filename} File Parsing Done!")

        return {
            "filename": file.filename,
            "parsed_data": final_json
        }

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    




@app.post("/Protected-Resume-DocLing")
def protected_parser_funct(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...)
):

    logger.info(f"[+] DocLing Orchestrator Used.")
    try:

        # Safe file checks
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")

        if "." not in file.filename:
            raise HTTPException(status_code=400, detail="Invalid file name")

        file_ext = file.filename.split(".")[-1].lower()



        # Save file
        safe_file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(safe_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)


        # Orchestrator
        extracted_text = DocLing_EasyOCR_TextExtractor(safe_file_path, file.filename)

        # LLM Parsing
        raw_llm_output = parse_with_openrouter(extracted_text,)

        parsed_json = parse_and_validate_resume(raw_llm_output)
        final_json = parsed_json.model_dump()

        

        logger.info(f"[+] {file.filename} File Parsing Done!")

        return JSONResponse({
            "filename": file.filename,
            "parsed_data": final_json
        })

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)




logger.info("[+] Main File Excecuted ! You Are Fine To Go...")

