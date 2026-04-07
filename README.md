
Project structure

SmartExpenseTracker/
│
├── README.md
├── requirements.txt
├── main.py
├── data/               # Empty folder, DB auto-creates
├── exports/            # Empty folder, CSV exports go here
├── src/
│   ├── expense.py
│   └── tracker.py
└── tests/
    └── test_tracker.py
src/expense.py
Python
# src/expense.py
# Smart Expense Tracker 2026
# Python Standard Library only

class Expense:
    def __init__(self, name: str, amount: float, date: str, category: str):
        self.name = name.strip()
        self.amount = float(amount)
        self.date = date.strip()
        self.category = category.strip()
src/tracker.py
Python
# src/tracker.py
import sqlite3
from pathlib import Path
import csv
from .expense import Expense

DATA_DIR = Path.home() / "SmartExpenseTracker"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "expenses.db"
CSV_EXPORT = DATA_DIR / "exports/expenses_export.csv"
CSV_EXPORT.parent.mkdir(exist_ok=True)

class Database:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL
        )""")
        self.conn.commit()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()


class ExpenseTracker:
    def __init__(self):
        self.db = Database()
        self.budget_alert = None

    def add_expense(self, expense: Expense):
        self.db.execute(
            "INSERT INTO expenses (name, amount, date, category) VALUES (?, ?, ?, ?)",
            (expense.name, expense.amount, expense.date, expense.category)
        )

    def view_expenses(self, filter_category=None, filter_date=None):
        query = "SELECT * FROM expenses"
        params = ()
        if filter_category and filter_date:
            query += " WHERE category=? AND date=?"
            params = (filter_category, filter_date)
        elif filter_category:
            query += " WHERE category=?"
            params = (filter_category,)
        elif filter_date:
            query += " WHERE date=?"
            params = (filter_date,)
        query += " ORDER BY date DESC"
        return self.db.fetchall(query, params)

    def total_spending(self):
        result = self.db.fetchone("SELECT SUM(amount) FROM expenses")
        return result[0] if result and result[0] else 0.0

    def category_summary(self):
        return self.db.fetchall("""
        SELECT category, SUM(amount) 
        FROM expenses 
        GROUP BY category 
        ORDER BY SUM(amount) DESC
        """)

    def monthly_summary(self, month: int, year: int):
        return self.db.fetchall("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE strftime('%Y', date)=? AND strftime('%m', date)=?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """, (str(year), f"{month:02d}"))

    def top_expenses(self, limit=5):
        return self.db.fetchall("SELECT * FROM expenses ORDER BY amount DESC LIMIT ?", (limit,))

    def export_csv(self, path=CSV_EXPORT):
        expenses = self.view_expenses()
        if not expenses:
            print("No expenses to export.")
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Amount", "Date", "Category"])
            writer.writerows(expenses)
        print(f" Expenses exported to {path}")

    def set_budget_alert(self, amount):
        self.budget_alert = amount

    def check_budget_alert(self):
        total = self.total_spending()
        if self.budget_alert and total > self.budget_alert:
            print(f" Alert! You exceeded your budget of ${self.budget_alert:.2f} by ${total - self.budget_alert:.2f}")

    def close(self):
        self.db.close()
tests/test_tracker.py
Python
import unittest
from pathlib import Path
from src.expense import Expense
from src.tracker import ExpenseTracker

TEST_DB = Path("data/test_expenses.db")
TEST_DB.parent.mkdir(exist_ok=True)

class TestExpenseTracker(unittest.TestCase):
    def setUp(self):
        if TEST_DB.exists():
            TEST_DB.unlink()
        self.tracker = ExpenseTracker()

    def tearDown(self):
        self.tracker.close()
        if TEST_DB.exists():
            TEST_DB.unlink()

    def test_add_and_total(self):
        e1 = Expense("Lunch", 10.5, "2026-04-07", "Food")
        e2 = Expense("Bus", 2.5, "2026-04-07", "Transport")
        self.tracker.add_expense(e1)
        self.tracker.add_expense(e2)
        self.assertEqual(self.tracker.total_spending(), 13.0)

    def test_category_summary(self):
        e1 = Expense("Lunch", 10.0, "2026-04-07", "Food")
        e2 = Expense("Dinner", 15.0, "2026-04-07", "Food")
        e3 = Expense("Bus", 5.0, "2026-04-07", "Transport")
        for e in [e1, e2, e3]:
            self.tracker.add_expense(e)
        summary = dict(self.tracker.category_summary())
        self.assertEqual(summary["Food"], 25.0)
        self.assertEqual(summary["Transport"], 5.0)

    def test_budget_alert(self):
        self.tracker.set_budget_alert(20.0)
        e1 = Expense("Shopping", 25.0, "2026-04-07", "Misc")
        self.tracker.add_expense(e1)
        self.assertTrue(self.tracker.total_spending() > self.tracker.budget_alert)

if __name__ == "__main__":
    unittest.main()

