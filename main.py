from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
import model
from database import sessionlocal
from schemas import Studentcreate

app=FastAPI(title="DATABASE CONNECTION SYSTEM")

def get_db():

    db=sessionlocal()  
    try:
        yield db
    finally:
        db.close()

@app.post("/students")

def create_student(student:Studentcreate,db:Session=Depends(get_db)):
    new_student=model.Student(
        name=student.name,
        address=student.address
    )


    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


        
    