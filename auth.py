from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
SECRET_KEY = "escreve-aqui-uma-frase-secreta-qualquer-para-o-projeto"
ALGORITHM = "HS256"
# Encriptação de passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Esquema de extração do Token do Header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")
def get_password_hash(password):
    return pwd_context.hash(password)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7) # Token válido por 7 dias
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
# Função para proteger endpoints - Devolve o Utilizador se o Token for válido
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
Ficheiro Principal: main.py
Objetivo: Ligar tudo, substituir o teu ficheiro antigo e criar as operações CRUD completas (Registar, Login, Listar, Criar, Editar, Apagar).

python


from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from database import engine, get_db
# Cria o ficheiro base de dados e as tabelas assim que a API arranca
models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Urban Audit API",
    description="API REST para gestão de ocorrências urbanas",
    version="2.0.0"
)
# ==========================================
# ENDPOINTS DE AUTENTICAÇÃO
# ==========================================
@app.post("/api/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def registar_utilizador(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Verifica se já existe email
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já registado")
    
    # 2. Guarda com password encriptada (Segurança)
    new_user = models.User(email=user.email, hashed_password=auth.get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
@app.post("/api/login", response_model=schemas.LoginResponse)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    # Valida login
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou password inválidos")
    
    # Devolve o Token
    access_token = auth.create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer", "userId": db_user.id}
# ==========================================
# ENDPOINTS DE OCORRÊNCIAS (CRUD)
# ==========================================
@app.post("/api/ocorrencias", response_model=schemas.OcorrenciaResponse, status_code=status.HTTP_201_CREATED)
def criar_ocorrencia(
    ocorrencia: schemas.OcorrenciaCreate, 
    db: Session = Depends(get_db),
    # O Depends obriga a que seja enviado um Token válido para criar
    current_user: models.User = Depends(auth.get_current_user) 
):
    nova_ocorrencia = models.Ocorrencia(**ocorrencia.model_dump(), owner_id=current_user.id)
    db.add(nova_ocorrencia)
    db.commit()
    db.refresh(nova_ocorrencia)
    return nova_ocorrencia
@app.get("/api/ocorrencias", response_model=List[schemas.OcorrenciaResponse])
def listar_ocorrencias(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Retorna todas as ocorrências
    return db.query(models.Ocorrencia).all()
# NOVO REQUISITO: Operação de Edição
@app.put("/api/ocorrencias/{ocorrencia_id}", response_model=schemas.OcorrenciaResponse)
def editar_ocorrencia(
    ocorrencia_id: int, 
    ocorrencia_update: schemas.OcorrenciaUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_ocorrencia = db.query(models.Ocorrencia).filter(models.Ocorrencia.id == ocorrencia_id).first()
    if not db_ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    
    # CONTROLO DE ACESSO: O utilizador atual é o dono desta ocorrência?
    if db_ocorrencia.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não tens permissão para editar esta ocorrência")
    
    # Atualiza apenas os campos enviados
    update_data = ocorrencia_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ocorrencia, key, value)
        
    db.commit()
    db.refresh(db_ocorrencia)
    return db_ocorrencia
# NOVO REQUISITO: Operação de Remoção
@app.delete("/api/ocorrencias/{ocorrencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_ocorrencia(
    ocorrencia_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_ocorrencia = db.query(models.Ocorrencia).filter(models.Ocorrencia.id == ocorrencia_id).first()
    if not db_ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
        
    # CONTROLO DE ACESSO: Apenas o dono pode apagar
    if db_ocorrencia.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não tens permissão para apagar esta ocorrência")
        
    db.delete(db_ocorrencia)
    db.commit()
