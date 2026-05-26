# Expense Tracker

A full-stack expense tracking app with category-wise summary and analytics.

## Live URLs
- Frontend: [add your Vercel URL here]
- Backend API: [add your Render URL here]

## Features
- Add expenses with category, amount, date, payment method
- View all expenses filtered by category or month
- Category-wise summary with percentage breakdown
- Monthly trend chart

## Tech Stack
- **Backend:** Python, FastAPI, SQLite
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Deployment:** Render (backend), Vercel (frontend)

## Run Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
API runs at http://localhost:8000

### Frontend
Open `frontend/index.html` in your browser.
Make sure the `API` variable at the top of `index.html` points to `http://localhost:8000`

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /expenses | List all expenses |
| POST | /expenses | Add an expense |
| DELETE | /expenses/{id} | Delete an expense |
| GET | /summary | Category-wise totals |
