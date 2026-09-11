from sqlalchemy  import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

MYSQL_USER="root"
MYSQL_PASSWORD="12345"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_DATABASE="fastapi_db"

MYSQL_URL=f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine=create_engine(MYSQL_URL)

sessionlocal=sessionmaker(autoflush=False,autocommit=False,bind=engine)
Base=declarative_base()


