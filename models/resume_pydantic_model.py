from utils.logger import logger

logger.info("[+] resume_pydantic_model File Started...")

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
import re

class ResumeModel(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    education: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    @field_validator("skills", "languages", "education", "experience", mode="before")
    def normalize_list_fields(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [item.strip() for item in re.split(r",|\n", v) if item.strip()]
        return v
    
logger.info("[+] resume_pydantic_model File Excecuted!")

