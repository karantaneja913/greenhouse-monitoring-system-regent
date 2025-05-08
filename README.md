# GreenTech Greenhouse Monitoring System

This is a Flask-based web application for monitoring greenhouse conditions, managing issues, and assigning employees.

## Features

*   User Authentication (Login/Logout)
*   Dashboard with overview statistics and greenhouse status
*   Detailed view for each greenhouse with historical data charts
*   Issue tracking and assignment to employees
*   Employee management (view list)
*   Reporting section with various statistics
*   Notification system
*   User profile and settings pages (basic structure)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

4.  **Initialize the Database:**
    *   Run the Flask application once to create the necessary folders:
        ```bash
        python3 app.py
        ```
    *   Stop the application (Ctrl+C).
    *   Access the initialization URL in your browser (while the app *is not* running, this command just sets up the DB file):
        Visit `http://127.0.0.1:5000/init-db`
        *You should see a message "Database initialized with sample data".*

5.  **Run the application:**
    ```bash
    python3 app.py
    ```

6.  **Access the application:**
    Open your web browser and go to `http://127.0.0.1:5000/`

## Default Login Credentials

*   **Email:** `karan.taneja@greentech.com`
*   **Password:** `password123`

## Project Structure

```
/
|-- app.py                  # Main Flask application file
|-- requirements.txt        # Python dependencies
|-- .gitignore              # Files/folders ignored by Git
|-- README.md               # This file
|-- instance/
|   |-- greenhouse.db       # SQLite database file (created after init)
|-- templates/              # HTML templates
|   |-- base.html           # Base template for all pages
|   |-- login.html          # Login page
|   |-- dashboard.html      # Main dashboard page
|   |-- greenhouses.html    # List of all greenhouses
|   |-- greenhouse_detail.html # Details for a single greenhouse
|   |-- reports.html        # Reports page
|   |-- employees.html      # Employee list page
|   |-- settings.html       # Settings page
|   |-- profile.html        # User profile page
|   `-- index.html          # (Currently unused, login is at root)
`-- test_greenhouse_system.py # Unit/Integration tests (basic structure)
```

## Notes

*   The `SECRET_KEY` in `app.py` should be changed to a strong, unique value for production environments.
*   The `/init-db` route should ideally be removed or protected in a production environment as it drops and recreates the database.
*   Error handling and further input validation can be improved.
*   API endpoints for adding/editing employees and users in the settings page are not fully implemented in the provided `app.py`.
