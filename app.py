from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
import os
from datetime import datetime

# --- CONFIG -----------------------------------------------------------------

DATABASE = os.path.join(os.path.dirname(__file__), "cdms.db")
SECRET_KEY = "change-this-in-production"  # needed for flash() messages

app = Flask(__name__)
app.config["DATABASE"] = DATABASE
app.config["SECRET_KEY"] = SECRET_KEY


# --- DATABASE HELPERS -------------------------------------------------------

def get_db():
    """Get a connection to the SQLite database for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # access columns by name
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# --- UTILITY: SIMPLE VALIDATION --------------------------------------------

def validate_school_form(form):
    """
    Validate update form input.
    Returns (is_valid, errors_dict, cleaned_data_dict)
    """
    errors = {}
    cleaned = {}

    # Required fields (simple non-empty check)
    required_fields = ["name", "address", "contact_person"]
    for field in required_fields:
        value = form.get(field, "").strip()
        if not value:
            errors[field] = "This field is required."
        cleaned[field] = value

    # Optional text fields
    for field in [
        "contact_phone",
        "contact_email",
        "capacity",
        "location",
        "start_time",
        "end_time",
        "exam_dates",
        "holidays",
        "num_teachers",
    ]:
        cleaned[field] = form.get(field, "").strip()

    # Basic numeric validation
    for numeric_field in ["capacity", "num_teachers"]:
        value = cleaned.get(numeric_field)
        if value:
            try:
                int_value = int(value)
                if int_value < 0:
                    raise ValueError
                cleaned[numeric_field] = int_value
            except ValueError:
                errors[numeric_field] = "Please enter a valid non-negative integer."

    # (Optional) very light email check
    email = cleaned.get("contact_email")
    if email and "@" not in email:
        errors["contact_email"] = "Please enter a valid email address."

    is_valid = len(errors) == 0
    return is_valid, errors, cleaned


# --- ROUTES FOR FEATURE 2 ---------------------------------------------------

@app.route("/")
def index():
    """Redirect to schools listing (so staff can quickly find a school)."""
    return redirect(url_for("list_schools"))


@app.route("/schools")
def list_schools():
    """
    System Requirement 2.1:
        Display a list of schools for the user to select.
    Extra: simple search by name to help meet the 15-second acceptance criteria.
    """
    db = get_db()
    search = request.args.get("search", "").strip()

    if search:
        schools = db.execute(
            """
            SELECT id, name, address, contact_person, location
            FROM schools
            WHERE name LIKE ?
            ORDER BY name ASC
            """,
            (f"%{search}%",),
        ).fetchall()
    else:
        schools = db.execute(
            """
            SELECT id, name, address, contact_person, location
            FROM schools
            ORDER BY name ASC
            """
        ).fetchall()

    return render_template("schools_list.html", schools=schools, search=search)


@app.route("/schools/<int:school_id>/edit", methods=["GET", "POST"])
def edit_school(school_id):
    """
    Implements:
        2.2 Show current school details
        2.3 Allow user to change details
        2.4 Save updated info
        2.5 Display confirmation / error messages
    """
    db = get_db()

    # Fetch existing school (for both GET and POST)
    school = db.execute(
        "SELECT * FROM schools WHERE id = ?",
        (school_id,),
    ).fetchone()

    if school is None:
        flash("School not found.", "error")
        return redirect(url_for("list_schools"))

    if request.method == "POST":
        is_valid, errors, cleaned = validate_school_form(request.form)

        if not is_valid:
            # Acceptance Criterion 2: show error message for invalid information
            flash("Please correct the errors below and try again.", "error")
            return render_template(
                "edit_school.html",
                school=school,
                form_data=request.form,
                errors=errors,
            )

        # Perform the update in the database
        db.execute(
            """
            UPDATE schools
            SET name = ?,
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
        db.commit()

        # Acceptance Criterion 3 & 4:
        #   - Data is saved in the database (commit above)
        #   - Confirmation message after saving (flash below)
        flash("School information updated successfully.", "success")

        # Redirect to avoid resubmitting form on refresh
        return redirect(url_for("edit_school", school_id=school_id))

    # GET request: show form with existing values
    return render_template(
        "edit_school.html",
        school=school,
        form_data=school,   # prefill form
        errors={},
    )


# --- MAIN ENTRYPOINT --------------------------------------------------------

if __name__ == "__main__":
    # For local testing
    app.run(debug=True)
    