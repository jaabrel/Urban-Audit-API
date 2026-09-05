from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    # Relação: Um utilizador tem várias ocorrências
    ocorrencias = relationship("Ocorrencia", back_populates="owner")
class Ocorrencia(Base):
    __tablename__ = "ocorrencias"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    descricao = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    fotoBase64 = Column(String)
    estado = Column(String, default="Aberto")
    
    # Relaciona cada ocorrência com um utilizador (Chave Estrangeira)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="ocorrencias")
