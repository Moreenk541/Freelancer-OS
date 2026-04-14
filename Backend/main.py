from fastapi import FastAPI
from app.database.database import Base,engine
from app.models import user

Base.metadata.create_all(bind=engine)


app =FastAPI()

@app.get('/')

def home():
    return {"message": "Freelance OS API is ready"}