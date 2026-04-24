-- Active: 1752490614457@@127.0.0.1@5432
from sqlalchemy import create_engine
from sqlalchemy.orm import  sessionmaker, declarative_base

DATABASE_URL ="postgresql://moreenk:123456@localhost/freelance_os"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal =sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()