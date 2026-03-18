
import sqlite3
from crypto_util import encrypt, decrypt

DB="users.db"

def init_db():
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
        uid TEXT PRIMARY KEY,
        userid TEXT,
        password TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_user(uid,userid,password):
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    enc=encrypt(password)
    cur.execute("INSERT OR REPLACE INTO users VALUES(?,?,?)",(uid,userid,enc))
    conn.commit()
    conn.close()

def get_user(uid):
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute("SELECT userid,password FROM users WHERE uid=?",(uid,))
    row=cur.fetchone()
    conn.close()
    if not row:
        return None,None
    return row[0],decrypt(row[1])
