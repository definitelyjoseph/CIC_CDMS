CREATE TABLE IF NOT EXISTS schools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    contact_person TEXT NOT NULL,
    contact_phone TEXT,
    contact_email TEXT,
    capacity INTEGER,
    location TEXT,
    start_time TEXT,
    end_time TEXT,
    exam_dates TEXT,
    holidays TEXT,
    num_teachers INTEGER
);