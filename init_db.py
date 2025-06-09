from app.database import Base, engine
from app import models

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")

if __name__ == "__main__":
    init_db()
