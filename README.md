
# FinTrack AI – Personal Finance Dashboard

FinTrack AI is a personal finance dashboard that helps users track income, expenses, month-wise summaries, CSV reports, and AI-powered budgeting tips. The project uses a Streamlit frontend, Flask backend, SQLite database, and OpenRouter API for AI-generated financial suggestions.

## Live Demo

**Live App:** https://fintrack-ai.streamlit.app/  
**Backend API:** https://fintrack-ai-80no.onrender.com  
**GitHub Repository:** https://github.com/ruhani11/Fintrack-ai

## Features

- Add income and expense transactions
- Store transaction amount, category, date, month, and year
- View complete transaction history
- View monthly financial overview
- Calculate total income, total expenses, and estimated savings
- Generate category-wise monthly breakdown
- Generate AI-powered budgeting tips
- Download all transactions as CSV
- Download selected month/year transactions as CSV
- Download month-wise summary as CSV
- Backend health check API
- Deployed frontend and backend separately

## Tech Stack

### Frontend
- Streamlit
- Pandas
- Requests
- Python-dotenv

### Backend
- Flask
- Flask-CORS
- SQLite
- OpenAI Python SDK
- OpenRouter API
- Gunicorn

### Deployment
- Frontend: Streamlit Community Cloud
- Backend: Render
- Version Control: Git and GitHub

## Project Structure

```text
Fintrack-ai/
│
├── frontend/
│   ├── app.py
│   └── requirements.txt
│
├── server/
│   ├── app.py
│   ├── utils.py
│   ├── reset_db.py
│   └── requirements.txt
│
├── .gitignore
├── runtime.txt
└── README.md
````

## How It Works

1. User enters transaction details from the Streamlit frontend.
2. Frontend sends transaction data to the Flask backend using REST APIs.
3. Backend stores the transaction in SQLite database.
4. User can view transaction history and month-wise summary.
5. For AI tips, frontend sends selected month expense summary and income to backend.
6. Backend sends financial data to OpenRouter API.
7. AI-generated budgeting tips are returned and displayed on the dashboard.

## API Endpoints

### Health Check

```http
GET /
```

Returns backend running status.

### Get Transactions

```http
GET /api/transactions
```

Returns all saved transactions.

### Add Transaction

```http
POST /api/transactions
```

Request body:

```json
{
  "amount": 5000,
  "category": "Food",
  "date": "2026-05-25",
  "month": "May",
  "year": 2026
}
```

### Monthly Summary

```http
POST /api/summary
```

Request body:

```json
{
  "month": "May",
  "year": 2026
}
```

### AI Budget Tip

```http
POST /api/tip
```

Request body:

```json
{
  "summary": {
    "Food": 5000,
    "Shopping": 3000
  },
  "income": 50000
}
```

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ruhani11/Fintrack-ai.git
cd Fintrack-ai
```

## Backend Setup

### 2. Go to Backend Folder

```bash
cd server
```

### 3. Create Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Create `.env` File in `server` Folder

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
FLASK_DEBUG=1
DATABASE_PATH=database.db
```

### 7. Run Backend

```bash
python app.py
```

Backend will run on:

```text
http://localhost:5000
```

## Frontend Setup

### 8. Open New Terminal and Go to Frontend Folder

```bash
cd frontend
```

### 9. Create Virtual Environment

```bash
python -m venv venv
```

### 10. Activate Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

### 11. Install Dependencies

```bash
pip install -r requirements.txt
```

### 12. Create `.env` File in `frontend` Folder

```env
PROJECT_URL=http://localhost:5000
```

### 13. Run Frontend

```bash
streamlit run app.py
```

Frontend will open in browser.

## Deployment Details

### Backend Deployment on Render

Backend is deployed on Render using the following configuration:

```text
Root Directory: server
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

Required Render environment variables:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
FLASK_DEBUG=0
DATABASE_PATH=database.db
```

### Frontend Deployment on Streamlit Community Cloud

Frontend is deployed on Streamlit Community Cloud using:

```text
Repository: ruhani11/Fintrack-ai
Branch: main
Main file path: frontend/app.py
```

Required Streamlit secret:

```toml
PROJECT_URL = "https://fintrack-ai-80no.onrender.com"
```

## Important Notes

* `.env` files are not pushed to GitHub for security reasons.
* `database.db` is ignored and should not be committed.
* SQLite is used for demo purposes.
* For production-level usage, PostgreSQL or another cloud database is recommended.
* OpenRouter free models may sometimes be rate-limited.
* Backend and frontend are deployed separately.

## Sample AI Tip Output

```text
1. Reduce Shopping by ₹3,200.00 and set a fixed monthly limit for this category.
2. Increase savings/investments by ₹10,000.00 this month.
3. Keep total expenses near ₹22,500.00 and review spending weekly.
```

## Future Enhancements

* User login and authentication
* Cloud database integration
* Expense category editing
* Monthly budget limits
* PDF report generation
* Graphical dashboard improvements
* Recurring transaction support
* Multiple user accounts
* Better AI-based spending insights

## Author

**Ruhani Bhatia**

* GitHub: [https://github.com/ruhani11](https://github.com/ruhani11)
* Project: FinTrack AI

## License

This project is created for learning, portfolio, and demonstration purposes.

