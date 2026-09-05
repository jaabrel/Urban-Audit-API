from pydantic import BaseModel, Field
from typing import Optional
# --- Utilizadores ---
class UserCreate(BaseModel):
    email: str
    password: str
class UserResponse(BaseModel):
    id: int
    email: str
    
    class Config:
        from_attributes = True
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    userId: int
# --- Ocorrências ---
class OcorrenciaBase(BaseModel):
    # Validações estritas de tamanho e valores (Requisito da Avaliação)
    titulo: str = Field(..., min_length=3, description="Título da ocorrência")
    descricao: str = Field(..., min_length=10, description="Descrição detalhada")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    fotoBase64: str
    estado: Optional[str] = "Aberto"
class OcorrenciaCreate(OcorrenciaBase):
    pass
class OcorrenciaUpdate(BaseModel):
    # Tudo é opcional na edição, pois podemos querer mudar só um campo
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    estado: Optional[str] = None
class OcorrenciaResponse(OcorrenciaBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True
