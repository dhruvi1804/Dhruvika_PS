from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB = "expenses.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                payment TEXT DEFAULT 'Cash',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

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
        query += " AND category = ?"
        params.append(category)
    if month:
        query += " AND date LIKE ?"
        params.append(f"{month}%")
    query += " ORDER BY date DESC"
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return {"expenses": [dict(r) for r in rows]}

@app.post("/expenses", status_code=201)
def add_expense(exp: ExpenseIn):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (description, amount, category, date, payment) VALUES (?,?,?,?,?)",
            (exp.description, exp.amount, exp.category, exp.date, exp.payment)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM expenses WHERE id=?", (cur.lastrowid,)).fetchone()
    return {"expense": dict(row)}

@app.delete("/expenses/{id}")
def delete_expense(id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (id,))
        conn.commit()
    return {"message": "Deleted"}

@app.get("/summary")
def summary():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses GROUP BY category"
        ).fetchall()
        total_row = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()
    grand_total = total_row[0] or 0
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
