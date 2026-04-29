import app.models
from fastapi import FastAPI
from app.database.database import Base,engine
 
from app.routes.users import router as users_router


Base.metadata.create_all(bind=engine)



app =FastAPI()

app.include_router(users_router)

@app.get('/')

def home():
    return {"message": "Freelance OS API is ready"}