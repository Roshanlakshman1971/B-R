# B&R Events - Luxury Celebrations Bangalore

A responsive web application and inquiry management system for **B&R Events**, luxury event architects based in Bengaluru specializing in weddings, naming ceremonies, pre-wedding photography, milestone birthdays, and royal catering.

## Project Structure

- `test2.html` - Complete responsive frontend website featuring event showcases, interactive catering menus, photo galleries, testimonials, and consultation booking form.
- `backend` - Lightweight Python HTTP server handling inquiry submissions, SQLite database storage, email notifications, and administrative CSV data export.
- `test_website.py` - Automated test suite validating static HTML structure, DOM IDs, form elements, API endpoints, and database integration.
- `data/` - Storage directory for SQLite database (`inquiries.sqlite3`) and exported inquiries.

## Getting Started

### 1. Prerequisites
- Python 3.10+
- Modern web browser

### 2. Running the Backend Server
Start the inquiry backend API:
```bash
./backend
# Or: python3 backend
```
The server will run on `http://127.0.0.1:8000`.

### 3. Viewing the Website
Open `test2.html` in your browser or serve it using Python:
```bash
python3 -m http.server 3000
```
Then navigate to `http://localhost:3000/test2.html`.

### 4. Running Tests
Run the test suite to verify frontend and backend health:
```bash
python3 test_website.py
```
