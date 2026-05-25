from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from utils import generate_budget_tip

app = Flask(__name__)

CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.getenv(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "database.db")
)


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            month TEXT NOT NULL,
            year INTEGER
        )
        """
    )

    # Add year column automatically if old database already exists
    cur.execute("PRAGMA table_info(transactions)")
    columns = [column[1] for column in cur.fetchall()]

    if "year" not in columns:
        cur.execute("ALTER TABLE transactions ADD COLUMN year INTEGER")

    # Fill year for old transactions from date like YYYY-MM-DD
    cur.execute(
        """
        UPDATE transactions
        SET year = CAST(substr(date, 1, 4) AS INTEGER)
        WHERE year IS NULL
        """
    )

    conn.commit()
    conn.close()


init_db()


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "success": True,
        "message": "FinTrack AI backend running"
    })


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
        rows = cur.fetchall()

        conn.close()

        transactions = [dict(row) for row in rows]

        return jsonify({
            "success": True,
            "transactions": transactions
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        amount = data.get("amount")
        category = data.get("category")
        date = data.get("date")
        month = data.get("month")
        year = data.get("year")

        # If frontend does not send year, derive it from date
        if not year and date:
            year = date[:4]

        if amount is None or not category or not date or not month or not year:
            return jsonify({
                "success": False,
                "error": "Amount, category, date, month and year are required"
            }), 400

        amount = float(amount)
        year = int(year)

        if amount <= 0:
            return jsonify({
                "success": False,
                "error": "Amount must be greater than 0"
            }), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO transactions (amount, category, date, month, year)
            VALUES (?, ?, ?, ?, ?)
            """,
            (amount, category.strip(), date, month, year)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Transaction added successfully"
        }), 201

    except ValueError:
        return jsonify({
            "success": False,
            "error": "Amount and year must be valid numbers"
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/summary", methods=["POST"])
def get_summary():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        month = data.get("month")
        year = data.get("year")

        if not month or not year:
            return jsonify({
                "success": False,
                "error": "Month and year are required"
            }), 400

        year = int(year)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE month = ? AND year = ?
            GROUP BY category
            """,
            (month, year)
        )

        rows = cur.fetchall()
        conn.close()

        summary = {row["category"]: row["total"] for row in rows}

        return jsonify({
            "success": True,
            "summary": summary
        })

    except ValueError:
        return jsonify({
            "success": False,
            "error": "Year must be a valid number"
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/tip", methods=["POST"])
def get_tip():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "tip": "Please provide expense summary and monthly income."
            }), 400

        summary = data.get("summary")
        income = data.get("income")

        if not summary or income is None:
            return jsonify({
                "success": False,
                "tip": "Please provide both expense summary and monthly income."
            }), 400

        tip = generate_budget_tip(summary, income)

        return jsonify({
            "success": True,
            "tip": tip
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "tip": f"AI tip could not be generated: {str(e)}"
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG") == "1"

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )