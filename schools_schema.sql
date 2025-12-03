-- Create the table only if it does not already exist
CREATE TABLE IF NOT EXISTS schools (

    -- Unique ID for each school. Automatically increases.
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- School name (required field)
    name TEXT NOT NULL,

    -- School address (required field)
    address TEXT NOT NULL,

    -- Name of the main contact person (required)
    contact_person TEXT NOT NULL,

    -- Optional contact phone number
    contact_phone TEXT,

    -- Optional contact email address
    contact_email TEXT,

    -- Number of students at the school (can be empty)
    capacity INTEGER,

    -- The time school starts (stored as text for simplicity)
    start_time TEXT,

    -- The time school ends
    end_time TEXT,

    -- The exam dates for the school (saved as plain text)
    exam_dates TEXT,

    -- Any holidays or special notes
    holidays TEXT,

    -- Number of teachers (can be empty)
    num_teachers INTEGER
);