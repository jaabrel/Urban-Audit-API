from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
        title="Urban Audit API",
        description="API REST para gestão de ocorrências urbanas",
        version="1.0.0"
)

## MODELOS DE DADOS

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    userId: int

class Ocorrencia(BaseModel):
    idServidor: Optional[int] = None
    titulo: str
    descricao: str
    latitude: float
    longitude: float
    fotoBase64: str
    estado: str = "Aberto"

# BASE DE DADOS SIMULADA

bd_ocorrencias = [
        Ocorrencia(
            idServidor=1,
            titulo="Buraco perigoso na via",
            descricao="Abatimento do piso junto à passadeira.",
            latitude=39.6042,
            longitude=-8.4116,
            fotoBase64="simulacao_base_64",
            estado="Aberto"
            )
]

# ENDPOINTS REST

@app.post("/api/login", response_model=LoginResponse)
def login(request: LoginRequest):
    if request.email == "aluno@ipt.pt" and request.password == "12345":
        return LoginResponse(token="token_simulado_123", userId=1)

    raise HTTPException(status_code=401, detail="Credenciais inválidas")

@app.get("/api/ocorrencias", response_model=List[Ocorrencia])
def listar_ocorrencias(authorization: str = Header(None)):
    # Simulação de controlo de acesso[cite: 1]
    if not authorization:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return bd_ocorrencias

@app.post("/api/ocorrencias", response_model=Ocorrencia)
def criar_ocorrencia(nova_ocorrencia: Ocorrencia, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Gerar um ID simulado e guardar
    nova_ocorrencia.idServidor = len(bd_ocorrencias) + 1
    bd_ocorrencias.append(nova_ocorrencia)
    
    return nova_ocorrencia
