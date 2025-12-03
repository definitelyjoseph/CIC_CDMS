from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import os
import csv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import and_
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

app = Flask(__name__)
app.secret_key = "very-simple-secret-key"  # used for flash messages

# The SQLite database file (USED BY BOTH sqlite3 AND SQLAlchemy)
DATABASE = os.path.join(os.path.dirname(__file__), "cdms.db")

# --- SQLAlchemy config (THIS was missing) ---
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Now it's safe to initialize SQLAlchemy
db = SQLAlchemy(app)

# Directory where generated CSV reports will be stored
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)



# ---------------------------
# Connect to the database
# ---------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # allows column names
    return conn

def build_where_clause(
    report_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
    school_id: Optional[int],
    partner_id: Optional[int],  # we still accept it, but we won't use it in SQL
) -> Tuple[str, List[Any]]:
    conditions = []
    params: List[Any] = []

    # Date filters
    if start_date and end_date:
        conditions.append("visit_date BETWEEN ? AND ?")
        params.extend([start_date.isoformat(), end_date.isoformat()])
    elif start_date:
        conditions.append("visit_date >= ?")
        params.append(start_date.isoformat())
    elif end_date:
        conditions.append("visit_date <= ?")
        params.append(end_date.isoformat())

    # School filter (this column DOES exist)
    if report_type == "by_school" and school_id is not None:
        conditions.append("school_id = ?")
        params.append(school_id)

    # NOTE: we are **not** adding any condition for partner_id here,
    # because the visits table does not have a partner_id column.

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    return where_clause, params


def fetch_summary(
    report_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
    school_id: Optional[int],
    partner_id: Optional[int],
) -> Dict[str, Any]:
    """
    Uses raw sqlite3 to summarize the visits table.
    Assumes visits table has:
        - school_id
        - visit_date
        - students_count
        - teachers_count
        - parents_count
    """
    conn = get_db_connection()
    try:
        where_clause, params = build_where_clause(
            report_type, start_date, end_date, school_id, partner_id
        )

        query = f"""
            SELECT
                COUNT(DISTINCT school_id) AS number_of_schools,
                COUNT(*)                  AS number_of_visits
            FROM visits
            {where_clause};
        """

        cur = conn.execute(query, params)
        row = cur.fetchone()


        if row is None:
            return {
                "number_of_schools": 0,
                "number_of_visits": 0,
            }

        return dict(row)
    finally:
        conn.close()


def write_csv(summary: Dict[str, Any], report_type: str) -> Path:
    """
    Writes the summary dict out to a CSV file in REPORTS_DIR and
    returns the file path.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summary_{report_type}_{timestamp}.csv"
    output_path = REPORTS_DIR / filename

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        for key, value in summary.items():
            writer.writerow([key, value])

    return output_path


# ---------- MODELS ----------

class School(db.Model):
    __tablename__ = "schools"  # match your existing SQLite table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    capacity = db.Column(db.Integer)
    location = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    start_time = db.Column(db.String(20))
    end_time = db.Column(db.String(20))
    exam_dates = db.Column(db.String(255))   # simple for now
    holidays = db.Column(db.String(255))
    num_teachers = db.Column(db.Integer)

    visits = db.relationship('Visit', backref='school', lazy=True)


class Visit(db.Model):
    __tablename__ = "visits"

    id = db.Column(db.Integer, primary_key=True)
    # FK must point to "schools.id" now
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    visit_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled/Completed

    feedbacks = db.relationship('Feedback', backref='visit', lazy=True)


class Feedback(db.Model):
    __tablename__ = "feedback"  # or "feedbacks", just be consistent

    id = db.Column(db.Integer, primary_key=True)
    # FK must point to "visits.id"
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1–5
    comments = db.Column(db.Text)
    submitted_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
# Delete school information
# ---------------------------
@app.route("/schools/<int:school_id>/delete", methods=["POST"])
def delete_school(school_id):
    """
    Simple route to delete a school from the database.
    Uses sqlite3 directly (same style as list_schools and edit_school).
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the school exists first (optional but nice)
    cursor.execute("SELECT id FROM schools WHERE id = ?", (school_id,))
    school = cursor.fetchone()

    if school is None:
        conn.close()
        flash("School not found.", "error")
        return redirect(url_for("list_schools"))

    # Delete the school
    cursor.execute("DELETE FROM schools WHERE id = ?", (school_id,))
    conn.commit()
    conn.close()

    flash("School deleted successfully.", "success")
    return redirect(url_for("list_schools"))

# ---------------------------
# Add new school information
# ---------------------------
#this route creates a webpage at /schools/add
@app.route("/schools/add", methods=["GET", "POST"]) 
def add_school():
    if request.method == "POST":
        '''below calls the existing valid_school_form function that will check
        alll the fields making sure the input is valid
        '''
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

        #handles the case if the form info is not valid
        if not is_valid:
            flash("Please fix errors below and try again.","error")
            return render_template(
                "add_school.html",
                form_data=request.form,
                errors=errors,
                )

        # Inserts info into database
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO schools
                (name, address, contact_person, contact_phone, contact_email,
                capacity,  start_time, end_time, exam_dates, holidays, num_teachers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name,
                  address,
                  contact_person,
                  contact_phone,
                  contact_email,
                  capacity,
                  start_time,
                  end_time,
                  exam_dates,
                  holidays,
                  num_teachers),
            )

            conn.commit()
            conn.close()
            
            flash("School added successfully!", "success")
            return redirect(url_for("list_schools"))

        except Exception as e:
            flash(f"Database error: {str(e)}", "danger")

    return render_template("add_school.html", 
                           form_data={},
                           errors={},
                           )

# ---------------------------
# Schedule School Visits
# ---------------------------
from sqlalchemy import and_

@app.route('/visits', methods=['GET'])
def list_visits():
    visits = Visit.query.order_by(Visit.visit_date.desc()).all()
    return render_template('visits/list.html', visits=visits)


@app.route('/visits/schedule', methods=['GET', 'POST'])
def schedule_visit():
    schools = School.query.all()

    if request.method == 'POST':
        school_id = request.form.get('school_id')
        date_str = request.form.get('visit_date')
        time_str = request.form.get('visit_time')

        if not school_id or not date_str or not time_str:
            flash('All fields are required.', 'error')
            return redirect(url_for('schedule_visit'))

        visit_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Conflict check (SRS: 3.3)
        conflict = Visit.query.filter(
            and_(Visit.visit_date == visit_date,
                 Visit.visit_time == time_str)
        ).first()

        if conflict:
            flash('Conflict: there is already a visit at this date and time.', 'error')
            return redirect(url_for('schedule_visit'))

        new_visit = Visit(
            school_id=int(school_id),
            visit_date=visit_date,
            visit_time=time_str
        )
        db.session.add(new_visit)
        db.session.commit()
        flash('Visit scheduled successfully!', 'success')
        return redirect(url_for('list_visits'))

    return render_template('visits/schedule.html', schools=schools)

# ---------------------------
# Requirement 4: Summary Reports
# ---------------------------

@app.route("/reports", methods=["GET", "POST"])
def generate_report():
    """Generate summary reports based on date range, school, or partner."""
    if request.method == "GET":
        # Show the form
        return render_template("report_form.html")

    report_type = request.form.get("report_type", "by_date_range")

    # Helper to parse dates from the form
    def parse_date(field_name: str) -> Optional[date]:
        value = request.form.get(field_name, "").strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    start_date = parse_date("start_date")
    end_date = parse_date("end_date")

    # Helper to parse integers from the form
    def parse_int(field_name: str) -> Optional[int]:
        value = request.form.get(field_name, "").strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    school_id = parse_int("school_id")
    partner_id = parse_int("partner_id")

    # Build summary based on filters
    summary = fetch_summary(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        school_id=school_id,
        partner_id=partner_id,
    )

    # Write CSV version of this summary
    output_path = write_csv(summary, report_type)

    flash("Report generated successfully.", "success")

    return render_template(
        "report_result.html",
        summary=summary,
        report_file_name=output_path.name,
        report_type=report_type,
    )


@app.route("/reports/download/<filename>")
def download_report(filename: str):
    """Download a previously generated CSV report."""
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        flash("Report file not found.", "error")
        return redirect(url_for("generate_report"))

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype="text/csv",
    )


# ---------------------------
# Run the app
# ---------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
    