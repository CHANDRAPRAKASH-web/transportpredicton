
# create_db.py
from database import engine, Base
import models

print("Creating database (test.db) and tables...")
Base.metadata.create_all(bind=engine)
print("Done — test.db created/updated.")