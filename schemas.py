from pydantic import BaseModel

class Studentcreate(BaseModel):
    name:str
    address:str
    