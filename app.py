from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

# -----------------------------------------
# BASIC APP SETUP
# -----------------------------------------

app = Flask(__name__)

# This is needed so we can use flash() messages
app.secret_key = "very-simple-secret-key"  # you can change this

# This is the name of your SQLite database file
DATABASE = os.path.join(os.path.dirname(__file__), "cdms.db")


# -----------------------------------------
# SIMPLE HELPER TO CONNECT TO THE DATABASE
# -----------------------------------------

def get_db_connection():
    """
    This function opens a connection to the SQLite database.
    We call it whenever we need to talk to the database.
    """
    conn = sqlite3.connect(DATABASE)
    # This lets us access rows like a dictionary, e.g. row["name"]
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------------------
# SIMPLE FORM VALIDATION FUNCTION
# -----------------------------------------

def validate_school_form(form):
    """
    This function checks if the form data is valid.
    It returns:
      - is_valid (True/False)
      - errors (dictionary with error messages)
      - cleaned_data (dictionary with cleaned/converted values)
    """
    errors = {}
    cleaned = {}

    # Get values from form (strip spaces)
    name = form.get("name", "").strip()
    address = form.get("address", "").strip()
    contact_person = form.get("contact_person", "").strip()

    # Required fields: they cannot be empty
    if not name:
        errors["name"] = "School name is required."
    if not address:
        errors["address"] = "Address is required."
    if not contact_person:
        errors["contact_person"] = "Contact person is required."

    cleaned["name"] = name
    cleaned["address"] = address
    cleaned["contact_person"] = contact_person

    # Optional fields
    cleaned["contact_phone"] = form.get("contact_phone", "").strip()
    cleaned["contact_email"] = form.get("contact_email", "").strip()
    cleaned["location"] = form.get("location", "").strip()
    cleaned["start_time"] = form.get("start_time", "").strip()
    cleaned["end_time"] = form.get("end_time", "").strip()
    cleaned["exam_dates"] = form.get("exam_dates", "").strip()
    cleaned["holidays"] = form.get("holidays", "").strip()

    # Numbers: capacity and num_teachers
    # These can be empty, but if the user types something it must be a valid number.
    capacity_value = form.get("capacity", "").strip()
    if capacity_value == "":
        cleaned["capacity"] = None
    else:
        try:
            cleaned["capacity"] = int(capacity_value)
            if cleaned["capacity"] < 0:
                errors["capacity"] = "Capacity cannot be negative."
        except ValueError:
            errors["capacity"] = "Capacity must be a whole number."

    num_teachers_value = form.get("num_teachers", "").strip()
    if num_teachers_value == "":
        cleaned["num_teachers"] = None
    else:
        try:
            cleaned["num_teachers"] = int(num_teachers_value)
            if cleaned["num_teachers"] < 0:
                errors["num_teachers"] = "Number of teachers cannot be negative."
        except ValueError:
            errors["num_teachers"] = "Number of teachers must be a whole number."

    # Very simple email check: if there is an email, it should contain "@"
    email = cleaned["contact_email"]
    if email and "@" not in email:
        errors["contact_email"] = "Please enter a valid email address."

    is_valid = (len(errors) == 0)
    return is_valid, errors, cleaned


# -----------------------------------------
# ROUTES
# -----------------------------------------

@app.route("/")
def home():
    """
    This is the homepage.
    For now, we just send the user to the schools list.
    """
    return redirect(url_for("list_schools"))


@app.route("/schools")
def list_schools():
    """
    This page shows a list of schools.
    It also supports searching by school name.
    This helps with the acceptance criteria:
      - staff can find and edit school info quickly (under 15 seconds).
    """
    search_term = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_term:
        # Search by name using LIKE
        cursor.execute(
            """
            SELECT id, name, address, contact_person, location
            FROM schools
            WHERE name LIKE ?
            ORDER BY name ASC
            """,
            (f"%{search_term}%",),
        )
    else:
        # No search: show all schools
        cursor.execute(
            """
            SELECT id, name, address, contact_person, location
            FROM schools
            ORDER BY name ASC
            """
        )

    schools = cursor.fetchall()
    conn.close()

    return render_template("schools_list.html", schools=schools, search=search_term)


@app.route("/schools/<int:school_id>/edit", methods=["GET", "POST"])
def edit_school(school_id):
    """
    This page allows the user to:
      - See the current details of a school
      - Edit any of the details
      - Save the changes

    It covers:
      System Requirement 2.2, 2.3, 2.4, 2.5
      and all acceptance criteria for Feature 2.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the existing school from the database
    cursor.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    # If no school found, show an error and go back to the list
    if school is None:
        conn.close()
        flash("School not found.", "error")
        return redirect(url_for("list_schools"))

    if request.method == "POST":
        # User submitted the form -> validate and update
        is_valid, errors, cleaned = validate_school_form(request.form)

        if not is_valid:
            # Something is wrong: show error messages and keep the form filled in
            flash("Please fix the errors below and try again.", "error")
            conn.close()
            return render_template(
                "edit_school.html",
                school=school,
                form_data=request.form,  # keep what user typed
                errors=errors,
            )

        # If we reach here, data is valid -> update the database
        cursor.execute(
            """
            UPDATE schools
            SET
                name = ?,
                address = ?,
                contact_person = ?,
                contact_phone = ?,
                contact_email = ?,
                capacity = ?,
                location = ?,
                start_time = ?,
                end_time = ?,
                exam_dates = ?,
                holidays = ?,
                num_teachers = ?
            WHERE id = ?
            """,
            (
                cleaned["name"],
                cleaned["address"],
                cleaned["contact_person"],
                cleaned["contact_phone"],
                cleaned["contact_email"],
                cleaned["capacity"],
                cleaned["location"],
                cleaned["start_time"],
                cleaned["end_time"],
                cleaned["exam_dates"],
                cleaned["holidays"],
                cleaned["num_teachers"],
                school_id,
            ),
        )
        conn.commit()
        conn.close()

        # Confirmation message (acceptance criteria)
        flash("School information updated successfully.", "success")

        # Redirect to the same page so refresh doesn't resubmit the form
        return redirect(url_for("edit_school", school_id=school_id))

    # If the request is GET: show the form with the current school data
    conn.close()
    return render_template(
        "edit_school.html",
        school=school,
        form_data=school,  # pre-fill form with existing data
        errors={},
    )


# -----------------------------------------
# RUN THE APP
# -----------------------------------------

if __name__ == "__main__":
    # debug=True helps while developing (shows errors in the browser)
    app.run(debug=True)
    