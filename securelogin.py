from flask import Blueprint, render_template, request, redirect, session, url_for
from datetime import datetime, timezone

# Ashley's employee account system
from user_management import (
    authenticate_user,
    create_employee_account
)

# Alexis's roles, permissions, and account locks
from users import (
    assign_role,
    get_user,
    load_users
)


# ---------------------------------------------------------
# AUTHENTICATION BLUEPRINT
# Greg's secure login/register routes
# ---------------------------------------------------------

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates"
)


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = authenticate_user(username, password)

        load_users()
        merged_user = get_user(username)

        # Prevent locked employees from logging in.
        if merged_user and merged_user.get("locked"):
            return render_template(
                "index.html",
                error="This employee account is locked."
            )

        # Successful authentication
        if user:
             # Create authenticated employee session.
            session.permanent = True
            session["username"] = user["username"]

         # Record the employee's initial activity time.
            session["last_activity"] = datetime.now(
                timezone.utc
             ).isoformat()

         # Start each login with a clean shopping cart.
            session.pop("cart", None)

            return redirect(url_for("index"))

        # Authentication failed.
        return render_template(
            "index.html",
            error="Invalid login credentials. Please try again."
        )

    # Normal GET request displays login page.
    return render_template("index.html")

# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Get employee name from Greg's registration form
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()

        # New employees start as Cashier.
        # Alexis's user-management screen can change the role later.
        role = "Cashier"

        if not first_name or not last_name:
            return render_template(
                "index.html",
                error="First name and last name are required."
            )

        # Ashley's employee-account creation function
        success, message = create_employee_account(
            username,
            password,
            first_name,
            last_name,
            role
        )

        if not success:
            return render_template(
                "index.html",
                error=message
            )

        # Load the new employee into Alexis's permissions system
        load_users()

        # Give the new employee the default permissions
        # associated with the Cashier role.
        assign_role(username, role)

        load_users()

        return redirect(url_for("auth.login"))

    return render_template("index.html")


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@auth_bp.route("/dashboard")
def dashboard():

    if "username" in session:
        return render_template(
            "dashboard.html",
            username=session["username"]
        )

    return redirect(url_for("auth.login"))


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@auth_bp.route("/logout")
def logout():
    """
    Log out the current employee.

    Clearing the session removes the authenticated username,
    shopping cart, and other session-based information.
    """

    session.clear()

    return redirect(url_for("auth.login"))