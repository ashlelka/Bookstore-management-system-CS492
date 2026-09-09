
 college course final project 
# Bookstore Management System

## CS492 Team Project

The Bookstore Management System (BMS) is a team-developed application designed to replace paper-based bookstore processes with a computerized system. The application supports bookstore operations such as inventory management, employee accounts, sales processing, and related bookstore functions.

## Development Environment

The project is developed using:

- Python
- Flask
- JSON data storage
- HTML/CSS
- Visual Studio Code
- Git and GitHub
- Python virtual environment

## Project Structure

- `main.py` - Inventory application entry point
- `book.py` - Book model
- `inventory.py` - Inventory management functions
- `sales_app.py` - Flask point-of-sale application
- `user_management.py` - Employee account management
- `books.json` - Inventory data
- `users.json` - Employee account data
- `templates/` - Flask HTML templates
- `static/` - CSS and static web resources
- `test_inventory.py` - Inventory tests
- `test_users.py` - Employee account tests

## Setup

Clone or download the project repository.

Create a Python virtual environment:

    uv venv

Install the project dependencies:

    uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt

## Running the Inventory System

    .\.venv\Scripts\python.exe main.py

## Running the Point-of-Sale System

    .\.venv\Scripts\python.exe sales_app.py

After Flask starts, open the local address displayed in the terminal.

## Testing

Run the inventory tests:

    .\.venv\Scripts\python.exe test_inventory.py

Run the employee account tests:

    .\.venv\Scripts\python.exe test_users.py

## Security

Employee passwords are not stored as plain text. Passwords are securely hashed before being written to the employee account data file.

Employee roles currently include:

- Admin
- Manager
- Cashier

## Sprint 1

Sprint 1 development includes inventory management, sales functionality, employee account management, security, and supporting development-environment configuration.
## Repository and Deployment

The development team uses GitHub as the shared code repository for
version control and team collaboration.

Render is used as the live demonstration deployment platform for the
Bookstore Management System.

Developers should test changes locally before committing and pushing
changes to the shared GitHub repository.