import datetime
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------
# 1. DATABASE CONFIGURATION (MySQL)
# ---------------------------------------------------------
MYSQL_URL = "mysql+pymysql://root:12345@localhost:3306/fastapi_db"

engine = create_engine(MYSQL_URL)
sessionlocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base = declarative_base()


# Hapa TRY na FINALLY ni muhimu ili kufunga connection siku zote
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# 2. DATABASE MODELS
# ---------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")


Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# 3. PYDANTIC SCHEMAS
# ---------------------------------------------------------
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ---------------------------------------------------------
# 4. SECURITY & AUTHENTICATION (Argon2 & JWT)
# ---------------------------------------------------------
SECRET_KEY = "7ab723eba8bcc3a5b161cbf9cb61c263807934a2700f91c6f560122e99853c9c"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


# Hapa TRY inazuia programu kucrash password ikiwa sio sahihi
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=30
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Hapa TRY inazuia programu kucrash token ikiwa imeisha muda au ni feki
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Token sio sahihi au imeisha muda")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Mtumiaji hajapatikana")
    return user


# ---------------------------------------------------------
# 5. FASTAPI APP & ENDPOINTS
# ---------------------------------------------------------
app = FastAPI(title="AUTHENTICATION SYSTEM")


@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    db_user = (
        db.query(User)
        .filter((User.username == user.username) | (User.email == user.email))
        .first()
    )
    if db_user:
        raise HTTPException(
            status_code=400, detail="Username au Email imeshasajiliwa"
        )

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role or "user",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Username au Password sio sahihi"
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/admin/dashboard")
def admin_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Huna ruhusa ya kufikia sehemu hii (Admin Pekee)",
        )
    return {
        "message": f"Karibu kwenye Dashboard ya Admin, {current_user.username}!",
        "status": "success",
    }