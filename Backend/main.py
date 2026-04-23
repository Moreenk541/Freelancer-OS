import app.models
from fastapi import FastAPI
from app.database.database import Base,engine
 

Base.metadata.create_all(bind=engine)


app =FastAPI()

@app.get('/')

def home():
    return {"message": "Freelance OS API is ready"}