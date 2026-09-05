from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./urbanaudit.db"

# check_same_thread=False é necessário no SQLite com o FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Dependência para abrir e fechar a BD em cada pedido
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
