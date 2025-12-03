from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "very-simple-secret-key"  # used for flash messages

# The SQLite database file
DATABASE = os.path.join(os.path.dirname(__file__), "cdms.db")


# ---------------------------
# Connect to the database
# ---------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # allows column names
    return conn


# ---------------------------
# Check if form data is valid
# ---------------------------
def validate_school_form(form):
    errors = {}

    # Get values from the form and remove extra spaces
    name = form.get("name", "").strip()
    address = form.get("address", "").strip()
    contact_person = form.get("contact_person", "").strip()

    contact_phone = form.get("contact_phone", "").strip()
    contact_email = form.get("contact_email", "").strip()
    start_time = form.get("start_time", "").strip()
    end_time = form.get("end_time", "").strip()
    exam_dates = form.get("exam_dates", "").strip()
    holidays = form.get("holidays", "").strip()

    # Required fields must not be empty
    if not name:
        errors["name"] = "School name is required."
    if not address:
        errors["address"] = "Address is required."
    if not contact_person:
        errors["contact_person"] = "Contact person is required."

    # Capacity validation
    capacity_value = form.get("capacity", "").strip()
    if capacity_value == "":
        capacity = None
    else:
        try:
            capacity = int(capacity_value)
            if capacity < 0:
                errors["capacity"] = "Capacity cannot be negative."
        except ValueError:
            errors["capacity"] = "Capacity must be a whole number."

    # Number of teachers validation
    teachers_value = form.get("num_teachers", "").strip()
    if teachers_value == "":
        num_teachers = None
    else:
        try:
            num_teachers = int(teachers_value)
            if num_teachers < 0:
                errors["num_teachers"] = "Number of teachers cannot be negative."
        except ValueError:
            errors["num_teachers"] = "Number of teachers must be a whole number."

    # Email check (basic)
    if contact_email and "@" not in contact_email:
        errors["contact_email"] = "Please enter a valid email address."

    # Return everything so we can use these values later
    is_valid = (len(errors) == 0)

    return (
        is_valid,
        errors,
        name,
        address,
        contact_person,
        contact_phone,
        contact_email,
        capacity if capacity_value != "" else None,
        start_time,
        end_time,
        exam_dates,
        holidays,
        num_teachers if teachers_value != "" else None,
    )


# ---------------------------
# Home → redirect to schools list
# ---------------------------
@app.route("/")
def home():
    return redirect(url_for("list_schools"))


# ---------------------------
# Show list of all schools
# ---------------------------
@app.route("/schools")
def list_schools():
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


# ---------------------------
# Edit school information
# ---------------------------
@app.route("/schools/<int:school_id>/edit", methods=["GET", "POST"])
def edit_school(school_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the current school data
    cursor.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    if school is None:
        conn.close()
        flash("School not found.", "error")
        return redirect(url_for("list_schools"))

    if request.method == "POST":

        (
            is_valid,
            errors,
            name,
            address,
            contact_person,
            contact_phone,
            contact_email,
            capacity,
            start_time,
            end_time,
            exam_dates,
            holidays,
            num_teachers,
        ) = validate_school_form(request.form)

        # If errors → show form again with messages
        if not is_valid:
            flash("Please fix the errors below and try again.", "error")
            conn.close()
            return render_template(
                "edit_school.html",
                school=school,
                form_data=request.form,
                errors=errors,
            )

        # Update database if everything is valid
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
                name,
                address,
                contact_person,
                contact_phone,
                contact_email,
                capacity,
                start_time,
                end_time,
                exam_dates,
                holidays,
                num_teachers,
                school_id,
            ),
        )
        conn.commit()
        conn.close()

        flash("School information updated successfully.", "success")
        return redirect(url_for("edit_school", school_id=school_id))

    # GET → show form with existing data
    conn.close()
    return render_template(
        "edit_school.html",
        school=school,
        form_data=school,
        errors={},
    )


# ---------------------------
# Run the app
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
    