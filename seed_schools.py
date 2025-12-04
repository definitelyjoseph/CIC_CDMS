import sqlite3
import os

# Path to your SQLite DB - matches your app.py
DATABASE = os.path.join(os.path.dirname(__file__), "cdms.db")

schools = [
    # ---- PRIMARY & INFANT ----
    ("Whitfield Primary & Infant School", "2 Lyndhurst Road, Kingston", "Mrs. Beverly Brown", "876-555-0011", "whitfield@example.com", 420),
    ("St. Alban’s Primary & Infant School", "10 Charles Street, Kingston", "Mr. Andre Campbell", "876-555-0012", "stalbans@example.com", 300),
    ("Calabar Infant, Primary & Junior High", "61 Red Hills Road, Kingston", "Mrs. Nadine Thomas", "876-555-0013", "calabar@example.com", 600),
    ("Harbour View Primary School", "Seaside Drive, Harbour View, Kingston 17", "Mrs. Dawn McKenzie", "876-555-0014", "hvprimary@example.com", 800),
    ("Rollington Town Primary", "17 Victoria Street, Kingston", "Mr. Trevor Williams", "876-555-0015", "rtprimary@example.com", 500),
    ("Clan Carthy Primary", "50 Deanery Road, Kingston 3", "Mrs. Paulette Meikle", "876-555-0016", "clancarthy@example.com", 450),
    ("Rousseau Primary School", "1 Ritchings Avenue, Kingston 5", "Ms. Natalie Robinson", "876-555-0017", "rousseau@example.com", 520),
    ("Holy Family Primary", "104-106 Tower Street, Kingston", "Ms. Judith Gayle", "876-555-0018", "holyfamily@example.com", 550),
    ("Alpha Primary School", "26 South Camp Road, Kingston", "Mrs. Kelisha Spencer", "876-555-0019", "alpha@example.com", 370),
    ("St. Aloysius Primary", "33 Duke Street, Kingston", "Mrs. Claire Martin", "876-555-0020", "staloy@example.com", 410),

    # ---- HIGH SCHOOLS ----
    ("Rhodes Hall High School", "Green Island P.O., Hanover", "Mr. Damian Burke", "876-555-0021", "rhodeshall@example.com", 900),
    ("Excelsior High School", "137 Mountain View Avenue, Kingston", "Mr. Anthony Hinds", "876-555-0022", "excel@example.com", 2500),
    ("Camperdown High School", "2A Swallowfield Road, Kingston 5", "Mr. Christopher Smart", "876-555-0023", "camperdown@example.com", 1800),
    ("Pembroke Hall High School", "62-64 Chesterfield Drive, Kingston 20", "Ms. Lorraine Salmon", "876-555-0024", "pembroke@example.com", 1400),
    ("Papine High School", "160 Old Hope Road, Kingston 6", "Mr. Owen McLeod", "876-555-0025", "papine@example.com", 1500),
    ("Waterford High School", "Waterford Parkway, Portmore", "Mrs. Marcia Clarke", "876-555-0026", "waterford@example.com", 1300),
    ("Jonathan Grant High", "11 Ginger Ridge Road, Spanish Town", "Mr. Horace Robinson", "876-555-0027", "jgrant@example.com", 1600),
    ("St. Catherine High", "Brunswick Avenue, Spanish Town", "Ms. Marlene Jennings", "876-555-0028", "stcatherine@example.com", 2000),
    ("Kingston High School", "172 King Street, Kingston", "Mr. Lionel Grant", "876-555-0029", "khs@example.com", 1200),
    ("Meadowbrook High School", "41 Meadowbrook Avenue, Kingston 19", "Mrs. Fay Whyte", "876-555-0030", "meadowbrook@example.com", 1600),

    # ---- ADDITIONAL SCHOOLS ----
    ("Vauxhall High School", "Slipe Pen Road, Kingston", "Mr. Leo Davis", "876-555-0031", "vauxhall@example.com", 1100),
    ("Greater Portmore High", "Braeton Parkway, Portmore", "Ms. Keisha Forbes", "876-555-0032", "gphs@example.com", 1500),
    ("Donald Quarrie High", "Harbour View, Kingston 17", "Mr. Peter Sinclair", "876-555-0033", "dqhigh@example.com", 1200),
    ("Ardenne High School", "10 Ardenne Road, Kingston 10", "Mrs. Nadine Molloy", "876-555-0034", "ardenne@example.com", 1700),
    ("Calabar High School", "61 Red Hills Road, Kingston", "Mr. Vassell", "876-555-0035", "calabarhs@example.com", 1800),
    ("Campion College", "105 Hope Road, Kingston 6", "Mrs. Henry", "876-555-0036", "campion@example.com", 1300),
    ("Immaculate Conception High", "152c Constant Spring Road", "Sister Angella Harris", "876-555-0037", "ichs@example.com", 2000),
    ("Merl Grove High", "77-79 Constant Spring Road", "Mrs. Andrea Davis", "876-555-0038", "merlgrove@example.com", 1500),
    ("St. George’s Girls Primary", "North Street, Kingston", "Ms. Sophia Blake", "876-555-0039", "sggps@example.com", 350),
    ("John Mills Infant & Primary", "Donald Quarrie High Drive, Kingston", "Mrs. Karen Gray", "876-555-0040", "johnmills@example.com", 450),
]

def seed():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    print("Inserting schools...")

    for school in schools:
        cur.execute("""
            INSERT INTO schools
            (name, address, contact_person, contact_phone, contact_email, capacity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, school)

    conn.commit()
    conn.close()
    print("DONE! Successfully added", len(schools), "schools.")

if __name__ == "__main__":
    seed()
