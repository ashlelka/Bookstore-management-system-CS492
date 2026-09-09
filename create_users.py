from user_management import create_employee_account


employees = [
    {
        "username": "admin1",
        "password": "Admin123!",
        "first_name": "Ashley",
        "last_name": "Lindamood",
        "role": "Admin"
    },
    {
        "username": "manager1",
        "password": "Manager123!",
        "first_name": "Jordan",
        "last_name": "Smith",
        "role": "Manager"
    },
    {
        "username": "cashier1",
        "password": "Cashier123!",
        "first_name": "Taylor",
        "last_name": "Brown",
        "role": "Cashier"
    }
]


for employee in employees:

    success, result = create_employee_account(
        employee["username"],
        employee["password"],
        employee["first_name"],
        employee["last_name"],
        employee["role"]
    )

    if success:
        print(
            f"Employee account created. "
            f"User ID: {result}"
        )
    else:
        print(f"Account creation failed: {result}")