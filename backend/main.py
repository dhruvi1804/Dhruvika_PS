import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Grab the live URL from Railway's environment variable.
# If running locally, it defaults to a standard local postgres URL.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")

def get_db():
    # Connect to PostgreSQL instead of SQLite
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            # Postgres uses SERIAL for auto-incrementing IDs and CURRENT_TIMESTAMP
            cur.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    payment TEXT DEFAULT 'Cash',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()

# Automatically generate tables when the file runs
init_db()

class ExpenseIn(BaseModel):
    description: str
    amount: float
    category: str
    date: str
    payment: str = "Cash"

@app.get("/expenses")
def list_expenses(category: str = None, month: str = None):
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    
    if category:
        # Postgres uses %s instead of ? for parameter binding
        query += " AND category = %s" 
        params.append(category)
    if month:
        query += " AND date LIKE %s"
        params.append(f"{month}%")
        
    query += " ORDER BY date DESC"
    
    with get_db() as conn:
        # RealDictCursor formats the rows as dictionaries, just like sqlite3.Row
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            
    return {"expenses": [dict(r) for r in rows]}

@app.post("/expenses", status_code=201)
def add_expense(exp: ExpenseIn):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Added RETURNING * to instantly fetch the new row without a second SELECT query
            cur.execute(
                "INSERT INTO expenses (description, amount, category, date, payment) VALUES (%s,%s,%s,%s,%s) RETURNING *",
                (exp.description, exp.amount, exp.category, exp.date, exp.payment)
            )
            row = cur.fetchone()
        conn.commit()
        
    return {"expense": dict(row)}

@app.delete("/expenses/{id}")
def delete_expense(id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id=%s", (id,))
        conn.commit()
        
    return {"message": "Deleted"}

@app.get("/summary")
def summary():
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT category, SUM(amount) as total FROM expenses GROUP BY category")
            rows = cur.fetchall()
            
            cur.execute("SELECT SUM(amount) as grand_total FROM expenses")
            total_row = cur.fetchone()
            
    grand_total = total_row["grand_total"] or 0
    
    categories = [
        {
            "name": r["category"],
            "total": round(r["total"], 2),
            "pct": round(r["total"] / grand_total * 100, 1) if grand_total else 0
        }
        for r in rows
    ]
    
    return {
        "grand_total": round(grand_total, 2),
        "categories": sorted(categories, key=lambda x: -x["total"])
    }
