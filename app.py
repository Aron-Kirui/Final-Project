import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import sqlite3

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# decorator to enforce user authentication
def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return func(*args, **kwargs)
    return decorated_view


db = "voting.db"


def get_db_connection():
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# error-handling function
def handle_error(message):
    return render_template("error.html", error_message=message)

# Home page route
@app.route("/")
def home():
    user_id = session.get("user_id")
    username = None
    projects = []
    # checks if user is logged in
    if user_id:
        # establish a connection to the database
        conn = get_db_connection()
        # execute an SQL query to get the username of the user logged in and fetch the first result
        user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()

         # Find the highest vote count
        max_votes = conn.execute("SELECT MAX(votes) as max_votes FROM projects_table").fetchone()["max_votes"]

       # Select all projects with the highest vote count
        projects = conn.execute("SELECT title, youtube_link, description, CAST(votes AS INTEGER) as votes FROM projects_table WHERE votes = ?", (max_votes,)).fetchall()
        # close the database connection to free resources
        conn.close()
        # checks if the user was found in the database
        if user:
            username = user["username"]
    return render_template("index.html", username=username, projects=projects)


# Admin page route
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    # checks if the logged-in user is not the admin and redirects them to homepage
    if session["user_id"] != 1 and session["user_id"] != 5:
        flash("This page can only be accessed by the admin!")
        return redirect("/")

    # checks if request method used is POST
    if request.method == "POST":
        # retrieves the system status from form submitted and checks if it is "on"
        posting_status = request.form.get("posting_status") == "on"
        voting_status = request.form.get("voting_status") == "on"

        conn = get_db_connection()
        # update the posting_status and voting_status in system_status table
        conn.execute("UPDATE system_status SET posting_status = ?, voting_status = ? WHERE id = 1",
                     (posting_status, voting_status))
        # commits the transaction to the database
        conn.commit()
        conn.close()

        flash("System status updated successfully!")
        return redirect("/admin")

    conn = get_db_connection()
    # retrieves the current posting_status and voting_status from the database.
    status = conn.execute(
        "SELECT posting_status, voting_status FROM system_status WHERE id = 1").fetchone()
    conn.close()

    return render_template("admin.html", status=status)

# Handles the sign up process of users
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Get the form data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate the form data
        if not username:
            return handle_error("Must provide username")
        elif not password:
            return handle_error("Must provide password")
        elif not confirmation:
            return handle_error("Must provide the password again")
        elif password != confirmation:
            return handle_error("Passwords do not match")

        try:
            # Insert the new user into the database
            conn = get_db_connection()
            conn.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                         (username, generate_password_hash(password)))
            conn.commit()

            # Retrieve the new user's ID and store it in the session
            user_id = conn.execute("SELECT id FROM users WHERE username = ?",
                                   (username,)).fetchone()["id"]
            conn.close()
            session["user_id"] = user_id

            # Redirect to the home page
            return redirect("/")
        except sqlite3.IntegrityError:
            # Handle the case where the username is already taken
            return handle_error("Username taken")

    # Render the signup form
    else:
        return render_template("signup.html")

# Handles the login process of users
@app.route("/login", methods=["GET", "POST"])
def login():
    # Clear any existing user session
    session.clear()

    if request.method == "POST":
        # Get the form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate the form data
        if not username:
            return handle_error("Must provide username")
        elif not password:
            return handle_error("Must provide password")
        else:
            # Query the database for the user
            conn = get_db_connection()
            rows = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()

            # Check if the username exists and if the password matches the hashed password in the database
            if rows is None or not check_password_hash(rows["hashed_password"], password):
                return handle_error("Invalid username and/or password")
            else:
                # Store the user's ID in the session and redirect to the home page
                session["user_id"] = rows["id"]
                return redirect("/")
    else:
        # Render the login form
        return render_template("login.html")

# Handles the logout process of users
@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out successfully!")
    return redirect("/")

@app.route("/post_project", methods=["GET", "POST"])
@login_required
def post_project():
    if request.method == "POST":
        # Get the form data
        title = request.form.get("title")
        description = request.form.get("description")
        youtube_link = request.form.get("youtube_link")

        # Check if any field is left empty
        if not title or not description or not youtube_link:
            return handle_error("All fields are required.")

        # Convert YouTube watch link to embed link
        def embed_link(youtube_link):
            if "watch?v=" in youtube_link:
                return youtube_link.replace("watch?v=", "embed/")
            else:
                return youtube_link

        youtube_link = embed_link(youtube_link)

        # Connect to the database
        conn = get_db_connection()

        # Check if posting is open
        system_status = conn.execute(
            "SELECT posting_status FROM system_status WHERE id = 1").fetchone()
        if not system_status["posting_status"]:
            conn.close()
            return handle_error("Posting is not open yet.")

        # Insert the new project into the database
        conn.execute("INSERT INTO projects_table (title, description, youtube_link) VALUES (?, ?, ?)",
                     (title, description, youtube_link))
        conn.commit()
        conn.close()

        # Flash a success message
        flash("You have posted your project successfully!")

        # Redirect to the view projects page
        return redirect("/view_projects")

    else:
        # Render the post project form
        return render_template("post_project.html")

@app.route("/view_projects")
@login_required
def view_projects():
    # Connect to the database
    conn = get_db_connection()

    # Fetch all projects from the database
    projects = conn.execute("SELECT * FROM projects_table").fetchall()

    # Close the database connection
    conn.close()

    # Handle the case where no projects are found
    if not projects:
        return handle_error("No projects have been posted yet.")

    # Render the view_projects template with the projects and embed_link function
    return render_template("view_projects.html", projects=projects)


@app.route("/vote", methods=["POST"])
@login_required
def vote():
    user_id = session["user_id"]
    project_id = request.form.get("project_id")

    conn = get_db_connection()

    # Check if voting is open
    system_status = conn.execute("SELECT voting_status FROM system_status WHERE id = 1").fetchone()
    if not system_status["voting_status"]:
        conn.close()
        return handle_error("Voting is not open yet.")

    # Check if the user has already voted
    user_status = conn.execute("SELECT voted FROM users WHERE id = ?", (user_id,)).fetchone()
    if user_status["voted"]:
        conn.close()
        return handle_error("You have already voted.")

    # Allow the vote
    conn.execute("UPDATE projects_table SET votes = votes + 1 WHERE id = ?", (project_id,))
    conn.execute("UPDATE users SET voted = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("You have voted successfully!")

    # Redirect to the view projects page
    return redirect("/view_projects")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Get the form data
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # Check if any field is left empty
        if not name:
            return handle_error("Name is required.")
        elif not email:
            return handle_error("Email is required.")
        elif "@" not in email or "." not in email:
            return handle_error("Invalid email address.")
        elif not message:
            return handle_error("Message is required.")

        # ackowledge successful submission of the message
        else:
            flash("Form submitted successfully!")
            return redirect("/")

    else:
        return render_template("contact.html")


if __name__ == '__main__':
    app.run(debug=True)
