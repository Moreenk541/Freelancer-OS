from sqlalchemy import Column,Integer,String
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id =Column(Integer, priimary_key = True)
    name= Column(String)
    email=Column(String, unique = True)
    password=Column(String)
    role =Column(String)