from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "very-simple-secret-key"  # you can change this

# Path to your SQLite database
DATABASE = os.path.join(os.path.dirname(__file__), "cdms.db")


# ---------------------------
# DATABASE CONNECTION HELPER
# ---------------------------

def get_db_connection():
    """
    Open a connection to the SQLite database.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------
# FORM VALIDATION
# ---------------------------

def validate_school_form(form):
    """
    Check if the form data is valid.
    Returns:
      - is_valid (True/False)
      - errors (dict)
      - cleaned_data (dict)
    """
    errors = {}
    cleaned = {}

    # Required fields
    name = form.get("name", "").strip()
    address = form.get("address", "").strip()
    contact_person = form.get("contact_person", "").strip()

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
    cleaned["start_time"] = form.get("start_time", "").strip()
    cleaned["end_time"] = form.get("end_time", "").strip()
    cleaned["exam_dates"] = form.get("exam_dates", "").strip()
    cleaned["holidays"] = form.get("holidays", "").strip()

    # Capacity
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

    # Number of teachers
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

    # Simple email check
    email = cleaned["contact_email"]
    if email and "@" not in email:
        errors["contact_email"] = "Please enter a valid email address."

    is_valid = (len(errors) == 0)
    return is_valid, errors, cleaned


# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    # Redirect to the schools list
    return redirect(url_for("list_schools"))


@app.route("/schools")
def list_schools():
    """
    Show list of schools with optional search.
    """
    search_term = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_term:
        cursor.execute(
            """
            SELECT id, name, address, contact_person
            FROM schools
            WHERE name LIKE ?
            ORDER BY name ASC
            """,
            (f"%{search_term}%",),
        )
    else:
        cursor.execute(
            """
            SELECT id, name, address, contact_person
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
    View + update an existing school.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    if school is None:
        conn.close()
        flash("School not found.", "error")
        return redirect(url_for("list_schools"))

    if request.method == "POST":
        is_valid, errors, cleaned = validate_school_form(request.form)

        if not is_valid:
            flash("Please fix the errors below and try again.", "error")
            conn.close()
            return render_template(
                "edit_school.html",
                school=school,
                form_data=request.form,
                errors=errors,
            )

        # Update school record (location removed)
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

        flash("School information updated successfully.", "success")
        return redirect(url_for("edit_school", school_id=school_id))

    # GET request: show form with existing data
    conn.close()
    return render_template(
        "edit_school.html",
        school=school,
        form_data=school,
        errors={},
    )


# ---------------------------
# RUN APP
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)
    