# Contributing

1. Create a focused branch and keep commits small.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `pytest -q` before each commit.
4. Keep business logic in `core/`; Streamlit presentation belongs in `app.py` or `pages/`.
5. Never commit `.env`, uploaded data, database files, or credentials.
