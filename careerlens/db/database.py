from careerlens.config import DB_PATH
import sqlite3
from contextlib import contextmanager
@contextmanager
def connect():
 DB_PATH.parent.mkdir(parents=True,exist_ok=True);conn=sqlite3.connect(DB_PATH);conn.row_factory=sqlite3.Row;conn.execute("PRAGMA foreign_keys=ON")
 try:
  yield conn
  conn.commit()
 except Exception:
  conn.rollback();raise
 finally:conn.close()
def initialize_database():
 schema=DB_PATH.parent.parent/"careerlens"/"db"/"schema.sql"
 with connect() as conn:conn.executescript(schema.read_text(encoding="utf-8"))
