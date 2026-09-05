from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models, schemas, auth
from database import engine, get_db, SessionLocal
# Cria o ficheiro base de dados e as tabelas assim que a API arranca
models.Base.metadata.create_all(bind=engine)

def fazer_seed_da_base_de_dados():
    db = SessionLocal()

    try:
        if db.query(models.User).count() == 0:
            print("A base de dados está vazia. Seed inicial...")

            admin = models.User(
                    email="admin@ipt.pt",
                    hashed_password=auth.get_password_hash("admin123"),
                    role="admin"
                    )
            
            # 2. Criar Utilizador Normal
            aluno = models.User(
                email="aluno@ipt.pt",
                hashed_password=auth.get_password_hash("aluno123"),
                role="user"
            )
            
            # Guarda os utilizadores na base de dados
            db.add(admin)
            db.add(aluno)
            db.commit()
            
            # O refresh serve para obtermos os IDs reais (1 e 2) que a base de dados lhes atribuiu
            db.refresh(admin)
            db.refresh(aluno)
            # 3. Criar Ocorrências que pareçam reais (usando coordenadas de Tomar)
            ocorrencia1 = models.Ocorrencia(
                titulo="Buraco profundo na estrada",
                descricao="Abatimento acentuado do piso junto à passadeira. Muito perigoso para pneus de motociclos.",
                latitude=39.6042,
                longitude=-8.4116,
                fotoBase64="simulacao_base_64_imagem_estrada",
                estado="Aberto",
                owner_id=aluno.id # Esta foi reportada pelo aluno
            )
            
            ocorrencia2 = models.Ocorrencia(
                titulo="Sinal de Stop caído",
                descricao="O vento derrubou o sinal de stop no cruzamento. Requer intervenção urgente.",
                latitude=39.6055,
                longitude=-8.4100,
                fotoBase64="simulacao_base_64_imagem_sinal", 
                estado="Aberto",
                owner_id=aluno.id # Também reportada pelo aluno
            )
            ocorrencia3 = models.Ocorrencia(
                titulo="Papeleira a transbordar",
                descricao="Lixo espalhado pelo passeio na rua principal. Já foi limpo pelos serviços camarários.",
                latitude=39.6065,
                longitude=-8.4120,
                fotoBase64="simulacao_base_64_imagem_lixo", 
                estado="Resolvido",
                owner_id=admin.id # Esta foi reportada/editada pelo admin e está Resolvida
            )
            
            # Guardar todas as ocorrências de uma vez
            db.add_all([ocorrencia1, ocorrencia2, ocorrencia3])
            db.commit()
            print("Seed concluído com sucesso!")
        else:
            print("A base de dados já tem dados. Seed ignorado.")
    finally:
        db.close()

fazer_seed_da_base_de_dados()

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
    return {"access_token": access_token, "token_type": "bearer", "userId": db_user.id, "role": db_user.role}
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
    if db_ocorrencia.owner_id != current_user.id and current_user.role != "admin":
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
    if db_ocorrencia.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Não tens permissão para apagar esta ocorrência")
        
    db.delete(db_ocorrencia)
    db.commit()
