from sqlalchemy import Column,Integer,VARCHAR

from database import Base

class Student(Base):
    __tablename__="students"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(VARCHAR(255))
    address=Column(VARCHAR(2555))



