# School Project

A Flask-based web application with alert management and dashboard functionality.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. **Clone or navigate to the project directory:**

   ```bash
   cd //schoolproject
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Project

1. **Start the Flask application:**

   ```bash
   python3 run.py
   ```

2. **Access the application:**
   - Open your web browser and navigate to `http://localhost:5000`
   - The application will run in debug mode with automatic reload enabled

## Project Structure

- `run.py` - Entry point for the Flask application
- `config.py` - Configuration settings
- `requirements.txt` - Python dependencies
- `routes/` - Application routes and blueprints
  - `alert_routes.py` - Alert-related endpoints
- `services/` - Business logic and utilities
  - `database.py` - Database initialization and operations
- `templates/` - HTML templates
  - `dashboard.html` - Main dashboard interface
- `data/` - Data storage directory

## Features

- Alert management system
- Web-based dashboard interface
- Database integration

## Troubleshooting

- If port 5000 is already in use, modify the port in `run.py`
- Ensure all dependencies are installed with `pip install -r requirements.txt`
- Delete the virtual environment and start fresh if you encounter issues

## License

School project
