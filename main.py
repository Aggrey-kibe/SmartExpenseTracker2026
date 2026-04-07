import sqlite3
from pathlib import Path
from datetime import datetime
import csv
import os

# ---------------- Paths ----------------
DATA_DIR = Path.home() / "SmartExpenseTracker"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "expenses.db"
CSV_EXPORT = DATA_DIR / "expenses_export.csv"

# ---------------- Database Layer ----------------
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

# ---------------- Models ----------------
class Expense:
    def __init__(self, name: str, amount: float, date: str, category: str):
        self.name = name.strip()
        self.amount = float(amount)
        self.date = date.strip()
        self.category = category.strip()

# ---------------- Expense Tracker ----------------
class ExpenseTracker:
    def __init__(self):
        self.db = Database()
        self.budget_alert = None  # Optional budget threshold

    # Core operations
    def add_expense(self, expense: Expense):
        self.db.execute(
            "INSERT INTO expenses (name, amount, date, category) VALUES (?, ?, ?, ?)",
            (expense.name, expense.amount, expense.date, expense.category)
        )

    def view_expenses(self, filter_category=None, filter_date=None):
        query = "SELECT * FROM expenses"
        params = ()
        if filter_category and filter_date:
            query += " WHERE category = ? AND date = ?"
            params = (filter_category, filter_date)
        elif filter_category:
            query += " WHERE category = ?"
            params = (filter_category,)
        elif filter_date:
            query += " WHERE date = ?"
            params = (filter_date,)
        query += " ORDER BY date DESC"
        return self.db.fetchall(query, params)

    def total_spending(self):
        result = self.db.fetchone("SELECT SUM(amount) FROM expenses")
        return result[0] if result and result[0] else 0.0

    def category_summary(self):
        query = """
        SELECT category, SUM(amount) 
        FROM expenses 
        GROUP BY category 
        ORDER BY SUM(amount) DESC
        """
        return self.db.fetchall(query)

    def monthly_summary(self, month: int, year: int):
        query = """
        SELECT category, SUM(amount) 
        FROM expenses 
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ? 
        GROUP BY category 
        ORDER BY SUM(amount) DESC
        """
        return self.db.fetchall(query, (str(year), f"{month:02d}"))

    def top_expenses(self, limit=5):
        query = "SELECT * FROM expenses ORDER BY amount DESC LIMIT ?"
        return self.db.fetchall(query, (limit,))

    def export_csv(self, path=CSV_EXPORT):
        expenses = self.view_expenses()
        if not expenses:
            print("No expenses to export.")
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Amount", "Date", "Category"])
            writer.writerows(expenses)
        print(f"Expenses exported to {path}")

    def set_budget_alert(self, amount):
        self.budget_alert = amount

    def check_budget_alert(self):
        total = self.total_spending()
        if self.budget_alert and total > self.budget_alert:
            print(f" Alert! You exceeded your budget of ${self.budget_alert:.2f} by ${total - self.budget_alert:.2f}")

    def close(self):
        self.db.close()

# ---------------- Validation ----------------
def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_amount(amount):
    try:
        return float(amount) >= 0
    except (ValueError, TypeError):
        return False

def validate_integer(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False

# ---------------- Display Helpers ----------------
def print_table(rows, headers):
    print("─" * 80)
    print(" | ".join(f"{h:<15}" for h in headers))
    print("─" * 80)
    for row in rows:
        print(" | ".join(f"{str(r):<15}" for r in row))
    print("─" * 80)

def print_chart(data, title):
    print(f"\n {title}")
    total = sum(amount for _, amount in data)
    for category, amount in data:
        bar = "" * int((amount / total) * 40) if total else ""
        print(f"{category:<15} | {bar} {amount:.2f}")
    print()

# ---------------- CLI Dashboard ----------------
def main():
    tracker = ExpenseTracker()
    print(" Smart Expense Tracker 2026 - Recruiter-Ready Dashboard ")

    while True:
        tracker.check_budget_alert()
        print("\n--- Menu ---")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Total Spending")
        print("4. Category Summary")
        print("5. Monthly Summary")
        print("6. Top 5 Expenses")
        print("7. Export CSV")
        print("8. Set Budget Alert")
        print("9. Exit")
        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            name = input("Name: ").strip()
            amount = input("Amount: ").strip()
            date = input("Date YYYY-MM-DD: ").strip()
            category = input("Category: ").strip()

            if not name or not category:
                print(" Name and category cannot be empty.")
                continue
            if not validate_amount(amount):
                print("Amount must be >= 0.")
                continue
            if not validate_date(date):
                print(" Invalid date format (YYYY-MM-DD).")
                continue

            tracker.add_expense(Expense(name, amount, date, category))
            print("Expense added successfully!")

        elif choice == "2":
            filter_cat = input("Filter by category (optional): ").strip() or None
            filter_date = input("Filter by date YYYY-MM-DD (optional): ").strip() or None
            expenses = tracker.view_expenses(filter_cat, filter_date)
            if expenses:
                print_table(expenses, ["ID", "Name", "Amount", "Date", "Category"])
            else:
                print("No expenses found.")

        elif choice == "3":
            total = tracker.total_spending()
            print(f"Total Spending: ${total:.2f}")

        elif choice == "4":
            summary = tracker.category_summary()
            if summary:
                print_table(summary, ["Category", "Total Spending"])
                print_chart(summary, "Category Spending Chart")
            else:
                print("No expenses found.")

        elif choice == "5":
            month = input("Month (1-12): ").strip()
            year = input("Year (YYYY): ").strip()
            if not validate_integer(month) or not (1 <= int(month) <= 12):
                print("Invalid month.")
                continue
            if not validate_integer(year) or len(year) != 4:
                print("Invalid year.")
                continue
            summary = tracker.monthly_summary(int(month), int(year))
            if summary:
                print_table(summary, ["Category", "Total Spending"])
                print_chart(summary, f"Monthly Spending Chart {month}/{year}")
            else:
                print("No expenses for this period.")

        elif choice == "6":
            top = tracker.top_expenses()
            if top:
                print_table(top, ["ID", "Name", "Amount", "Date", "Category"])
            else:
                print("No expenses found.")

        elif choice == "7":
            tracker.export_csv()

        elif choice == "8":
            budget = input("Set budget alert amount: ").strip()
            if not validate_amount(budget):
                print(" Invalid budget amount.")
                continue
            tracker.set_budget_alert(float(budget))
            print(f"Budget alert set at ${budget}")

        elif choice == "9":
            tracker.close()
            print(" Goodbye!")
            break

        else:
            print(" Invalid choice! Enter 1-9.")

if __name__ == "__main__":
    main()
