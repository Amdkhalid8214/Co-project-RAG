"""
DocuChat AI - Deterministic Dynamic Synthetic Dataset Engine
Generates realistic, schema-appropriate synthetic datasets with strictly validated dimensions.
Provides rich, distinct column pools for Student, Customer, Employee, Sales, and Healthcare domains.
"""

from typing import List, Any, Dict

# ==============================================================================
# Domain Column Pools
# ==============================================================================

# Primary 30 columns for Student Data (strictly matching specifications)
STUDENT_PRIMARY_COLUMNS = [
    "Student ID",
    "First Name",
    "Last Name",
    "Age",
    "Gender",
    "Email",
    "Phone",
    "Department",
    "Course",
    "Semester",
    "Year of Admission",
    "Date of Birth",
    "City",
    "State",
    "Country",
    "Postal Code",
    "Attendance Percentage",
    "Assignment Score",
    "Quiz Score",
    "Midterm Score",
    "Final Exam Score",
    "Total Marks",
    "Percentage",
    "Grade",
    "GPA",
    "Scholarship Status",
    "Enrollment Status",
    "Guardian Name",
    "Guardian Contact",
    "Registration Date",
]

# Extended columns for Student Data (when columns > 30)
STUDENT_EXTENDED_COLUMNS = [
    "Major Advisor",
    "Dormitory Building",
    "Room Number",
    "Library Card Number",
    "Credits Completed",
    "Cumulative Credits",
    "Degree Level",
    "Academic Standing",
    "Graduation Year",
    "Emergency Contact Name",
    "Emergency Contact Phone",
    "Blood Group",
    "Health Insurance ID",
    "Extracurricular Club",
    "Campus Employment Status",
    "Lab Section",
    "Tuition Fee Balance ($)",
    "Internship Status",
    "Thesis Title",
    "Faculty Mentor",
    "Locker Number",
    "Meal Plan Tier",
    "Parking Permit ID",
    "International Student Flag",
    "Language Proficiency",
    "Laptop Serial Number",
    "WiFi MAC Address",
    "Dean of Department",
    "Honor Society Member",
    "Alumni Network ID",
    "Field of Specialization",
    "Capstone Project ID",
    "Dean's List Semesters",
    "Prerequisite Status",
    "Career Track",
    "Hostel Block",
    "Disability Accommodation",
    "Alumni Mentor",
    "Bus Route Number",
    "Secondary Major"
]

CUSTOMER_PRIMARY_COLUMNS = [
    "Customer ID",
    "First Name",
    "Last Name",
    "Company Name",
    "Email",
    "Phone Number",
    "Billing Address",
    "City",
    "State",
    "Postal Code",
    "Country",
    "Customer Segment",
    "Account Status",
    "Registration Date",
    "Credit Limit ($)",
    "Annual Spend ($)",
    "Lifetime Value ($)",
    "Last Purchase Date",
    "Preferred Payment Method",
    "Loyalty Points Tier",
    "Support Tier",
    "Account Manager",
    "Contract Renewal Date",
    "Industry Sector",
    "Tax Exemption Status",
    "Website",
    "Lead Source",
    "Discount Tier (%)",
    "Total Orders",
    "Net Promoter Score (NPS)"
]

EMPLOYEE_PRIMARY_COLUMNS = [
    "Employee ID",
    "First Name",
    "Last Name",
    "Job Title",
    "Department",
    "Business Email",
    "Phone Number",
    "Hire Date",
    "Office Location",
    "Employment Type",
    "Base Salary ($)",
    "Bonus Percentage",
    "Performance Rating",
    "Manager Name",
    "Current Project",
    "Years of Service",
    "Health Plan Tier",
    "Stock Grant Units",
    "PTO Balance (Days)",
    "Emergency Contact Name",
    "Emergency Contact Phone",
    "Cost Center Code",
    "Workplace Mode",
    "Security Clearance Level",
    "Certifications Count",
    "Last Promotion Date",
    "Direct Reports Count",
    "Pay Grade",
    "Retirement Contribution (%)",
    "Desk Number"
]

SALES_PRIMARY_COLUMNS = [
    "Product SKU",
    "Product Name",
    "Category",
    "Sub-Category",
    "Brand",
    "Unit Cost ($)",
    "Unit Price ($)",
    "Units in Stock",
    "Reorder Level",
    "Units Sold (YTD)",
    "Total Revenue ($)",
    "Gross Margin (%)",
    "Warehouse Location",
    "Supplier Name",
    "Rating",
    "Review Count",
    "Discontinued Status",
    "Last Restock Date",
    "Tax Classification",
    "Shipping Weight (kg)",
    "Package Dimensions (cm)",
    "Warranty Period (Months)",
    "Lead Time (Days)",
    "Barcode (UPC)",
    "Handling Instructions",
    "Seasonal Demand Peak",
    "Return Rate (%)",
    "Safety Stock",
    "Fulfillment Channel",
    "Inventory Turnover Ratio"
]

HEALTHCARE_PRIMARY_COLUMNS = [
    "Patient ID",
    "First Name",
    "Last Name",
    "Date of Birth",
    "Age",
    "Gender",
    "Blood Group",
    "Phone Number",
    "Emergency Contact",
    "Admitting Doctor",
    "Department",
    "Room Number",
    "Diagnosis Code (ICD-10)",
    "Admission Date",
    "Discharge Date",
    "Insurance Provider",
    "Policy Number",
    "Total Billing ($)",
    "Prescribed Medication",
    "Follow-up Date",
    "Attending Nurse",
    "Dietary Restrictions",
    "Allergies",
    "Blood Pressure",
    "Heart Rate (BPM)",
    "Body Temperature (C)",
    "Oxygen Saturation (%)",
    "Lab Test Ordered",
    "Admission Status",
    "Ward Name"
]

GENERAL_PRIMARY_COLUMNS = [
    "Record ID",
    "Item Name",
    "Category",
    "Status",
    "Priority",
    "Created Date",
    "Updated Date",
    "Owner",
    "Value ($)",
    "Quantity",
    "Percentage (%)",
    "Score",
    "Rating",
    "Location",
    "Description",
    "Reference Code",
    "Department",
    "Tag",
    "Notes",
    "Active Flag",
    "Milestone",
    "Duration (Days)",
    "Budget ($)",
    "Risk Level",
    "Approval Status",
    "Assigned Team",
    "Review Cycle",
    "Verification Code",
    "Metric A",
    "Metric B"
]


# ==============================================================================
# Helper Pools for Realistic Values
# ==============================================================================

FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Sophia", "Jackson", "Ava", "Aiden", "Isabella", "Lucas",
    "Mia", "Ethan", "Harper", "Mason", "Evelyn", "Oliver", "Abigail", "Elijah", "Emily", "Logan",
    "Priya", "Rahul", "Aarav", "Ananya", "Chen", "Wei", "Elena", "Carlos", "Fatima", "Tariq",
    "Zoe", "Alexander", "Chloe", "Benjamin", "Ella", "Daniel", "Scarlett", "Matthew", "Grace", "Henry"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Patel", "Sharma", "Verma", "Rao", "Zhang", "Li", "Wang", "Kim", "Al-Mansoor", "Khan",
    "O'Connor", "Dubois", "Muller", "Kowalski", "Nakamura", "Santos", "Costa", "Rossi", "Novak", "Ivanov"
]

DEPARTMENTS = [
    "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Civil Engineering",
    "Biomedical Engineering", "Business Administration", "Economics", "Data Science",
    "Information Technology", "Mathematics & Statistics", "Physics", "Chemistry"
]

COURSES = [
    "Data Structures & Algorithms", "Database Management Systems", "Artificial Intelligence",
    "Computer Networks", "Operating Systems", "Software Engineering", "Cloud Computing",
    "Machine Learning Foundations", "Cybersecurity Principles", "Discrete Mathematics",
    "Object-Oriented Programming", "Applied Statistics"
]

CITIES_STATES = [
    ("Boston", "MA"), ("New York", "NY"), ("Chicago", "IL"), ("Seattle", "WA"),
    ("Austin", "TX"), ("San Francisco", "CA"), ("Atlanta", "GA"), ("Denver", "CO"),
    ("San Diego", "CA"), ("Philadelphia", "PA"), ("Raleigh", "NC"), ("Minneapolis", "MN")
]

GUARDIAN_NAMES = [
    "Robert", "Mary", "David", "Patricia", "James", "Jennifer", "Richard", "Linda",
    "Joseph", "Elizabeth", "Thomas", "Barbara", "Charles", "Susan", "Christopher", "Jessica"
]

DORMS = ["North Hall", "Beacon Tower", "Riverside Commons", "Pioneer Quad", "Oakridge Manor", "Summit Suites"]
PROF_NAMES = ["Alan Turing", "Barbara Liskov", "Grace Hopper", "Claude Shannon", "Donald Knuth", "Ada Lovelace"]


def get_columns_for_dataset(dataset_type: str, count: int) -> List[str]:
    """
    Returns exactly `count` distinct, relevant column names for the target dataset type.
    Never produces duplicates.
    """
    dt = dataset_type.lower()
    if "student" in dt or "school" in dt or "academic" in dt:
        primary = STUDENT_PRIMARY_COLUMNS
        extended = STUDENT_EXTENDED_COLUMNS
    elif "customer" in dt or "client" in dt:
        primary = CUSTOMER_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "employee" in dt or "payroll" in dt or "hr" in dt:
        primary = EMPLOYEE_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "sales" in dt or "product" in dt or "order" in dt or "ecommerce" in dt:
        primary = SALES_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "hospital" in dt or "patient" in dt or "healthcare" in dt or "medical" in dt:
        primary = HEALTHCARE_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    else:
        primary = GENERAL_PRIMARY_COLUMNS
        extended = STUDENT_EXTENDED_COLUMNS

    columns: List[str] = []
    seen = set()

    for col in primary:
        if len(columns) >= count:
            break
        if col not in seen:
            columns.append(col)
            seen.add(col)

    if len(columns) < count:
        for col in extended:
            if len(columns) >= count:
                break
            if col not in seen:
                columns.append(col)
                seen.add(col)

    # Dynamic fallback if count exceeds predefined pools
    fallback_idx = 1
    while len(columns) < count:
        candidate = f"Additional Attribute {fallback_idx}"
        if candidate not in seen:
            columns.append(candidate)
            seen.add(candidate)
        fallback_idx += 1

    return columns


def generate_student_row_value(column_name: str, row_idx: int) -> Any:
    """
    Generates a realistic, coherent synthetic value for row_idx (1-based index)
    given the column name.
    """
    i = row_idx
    fname = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
    lname = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
    city, state = CITIES_STATES[(i - 1) % len(CITIES_STATES)]
    age = 18 + ((i - 1) % 6)
    year_adm = 2022 + ((i - 1) % 4)
    sem = ((i - 1) % 8) + 1

    # Scores
    asgn = 75 + ((i * 7) % 25)
    quiz = 70 + ((i * 11) % 29)
    midterm = 72 + ((i * 13) % 27)
    final_exam = 74 + ((i * 17) % 26)
    total_marks = asgn + quiz + midterm + final_exam  # Out of 400
    percentage = round((total_marks / 400.0) * 100.0, 2)
    gpa = round(2.5 + (percentage / 100.0) * 1.5, 2)

    if percentage >= 90:
        grade = "A"
    elif percentage >= 85:
        grade = "A-"
    elif percentage >= 80:
        grade = "B+"
    elif percentage >= 75:
        grade = "B"
    elif percentage >= 70:
        grade = "B-"
    else:
        grade = "C+"

    # Map column to value
    col_lower = column_name.lower()

    FEMALE_NAMES = {"Emma", "Olivia", "Sophia", "Ava", "Isabella", "Mia", "Harper", "Evelyn", "Abigail", "Emily", "Priya", "Ananya", "Elena", "Fatima", "Zoe", "Chloe", "Ella", "Scarlett", "Grace"}
    if col_lower == "student id":
        return f"STU-2026-{i:04d}"
    elif col_lower == "first name":
        return fname
    elif col_lower == "last name":
        return lname
    elif col_lower == "age":
        return age
    elif col_lower == "gender":
        return "Female" if fname in FEMALE_NAMES else "Male"
    elif col_lower == "email":
        return f"{fname.lower()}.{lname.lower()}{i}@university.edu"
    elif col_lower == "phone":
        return f"+1-555-{1000 + i:04d}"
    elif col_lower == "department":
        return DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
    elif col_lower == "course":
        return COURSES[(i - 1) % len(COURSES)]
    elif col_lower == "semester":
        return f"Semester {sem}"
    elif col_lower in ("year of admission", "admission year"):
        return year_adm
    elif col_lower in ("date of birth", "dob"):
        b_year = 2026 - age
        b_month = ((i * 3) % 12) + 1
        b_day = ((i * 5) % 28) + 1
        return f"{b_year}-{b_month:02d}-{b_day:02d}"
    elif col_lower == "city":
        return city
    elif col_lower == "state":
        return state
    elif col_lower == "country":
        return "United States"
    elif col_lower in ("postal code", "zip code"):
        return f"{10000 + ((i * 317) % 89999):05d}"
    elif col_lower in ("attendance percentage", "attendance"):
        return round(82.0 + ((i * 3.7) % 17.5), 1)
    elif col_lower in ("assignment score", "assignment"):
        return asgn
    elif col_lower in ("quiz score", "quiz"):
        return quiz
    elif col_lower in ("midterm score", "midterm"):
        return midterm
    elif col_lower in ("final exam score", "final score", "final exam"):
        return final_exam
    elif col_lower in ("total marks", "total score"):
        return total_marks
    elif col_lower in ("percentage", "percent"):
        return percentage
    elif col_lower == "grade":
        return grade
    elif col_lower == "gpa":
        return gpa
    elif col_lower in ("scholarship status", "scholarship"):
        return "Merit Scholarship" if percentage >= 88 else ("Dean's List" if percentage >= 82 else "Standard")
    elif col_lower in ("enrollment status", "status"):
        return "Active Enrolled"
    elif col_lower in ("guardian name", "guardian"):
        return f"{GUARDIAN_NAMES[(i - 1) % len(GUARDIAN_NAMES)]} {lname}"
    elif col_lower in ("guardian contact", "guardian phone"):
        return f"+1-555-{9000 + i:04d}"
    elif col_lower in ("registration date", "enrolled date"):
        r_month = ((i * 2) % 12) + 1
        r_day = ((i * 3) % 28) + 1
        return f"2024-{r_month:02d}-{r_day:02d}"
    elif col_lower == "major advisor":
        return f"Dr. {PROF_NAMES[(i - 1) % len(PROF_NAMES)]}"
    elif col_lower == "dormitory building":
        return DORMS[(i - 1) % len(DORMS)]
    elif col_lower == "room number":
        return f"{100 + ((i * 7) % 400)}"
    elif col_lower == "library card number":
        return f"LIB-88{i:04d}"
    elif col_lower == "credits completed":
        return 15 * sem
    elif col_lower == "cumulative credits":
        return 128
    elif col_lower == "degree level":
        return "Undergraduate (B.S.)"
    elif col_lower == "academic standing":
        return "Good Standing"
    elif col_lower == "graduation year":
        return year_adm + 4
    elif col_lower == "emergency contact name":
        return f"{GUARDIAN_NAMES[(i * 3) % len(GUARDIAN_NAMES)]} {lname}"
    elif col_lower == "emergency contact phone":
        return f"+1-555-{8000 + i:04d}"
    elif col_lower == "blood group":
        return ["O+", "A+", "B+", "AB+", "O-", "A-"][(i - 1) % 6]
    elif col_lower == "health insurance id":
        return f"INS-99{i:04d}"
    elif col_lower == "extracurricular club":
        return ["Robotics Club", "Debate Society", "ACM Student Chapter", "Chess League", "Solar Car Team"][(i - 1) % 5]
    elif col_lower == "campus employment status":
        return "Teaching Assistant" if i % 3 == 0 else "None"
    elif col_lower == "lab section":
        return f"LAB-0{((i - 1) % 4) + 1}"
    elif col_lower == "tuition fee balance ($)":
        return 0.0 if percentage >= 88 else float(1200 * ((i % 5) + 1))
    elif col_lower == "internship status":
        return "Completed" if sem >= 6 else "Pending"
    elif col_lower == "thesis title":
        return f"Research Exploration in {COURSES[(i - 1) % len(COURSES)]}"
    elif col_lower == "faculty mentor":
        return f"Prof. {LAST_NAMES[(i * 2) % len(LAST_NAMES)]}"
    else:
        return f"Data_{i}_{column_name[:8]}"


def generate_generic_row_value(column_name: str, row_idx: int, dataset_type: str) -> Any:
    """Generates synthetic values for generic or other domain columns."""
    i = row_idx
    col_lower = column_name.lower()
    fname = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
    lname = LAST_NAMES[(i - 1) % len(LAST_NAMES)]

    if "id" in col_lower or "sku" in col_lower or "code" in col_lower:
        prefix = dataset_type[:3].upper() if dataset_type else "REC"
        return f"{prefix}-{2026}-{i:04d}"
    elif "first name" in col_lower:
        return fname
    elif "last name" in col_lower:
        return lname
    elif "name" in col_lower:
        return f"{fname} {lname}"
    elif "email" in col_lower:
        return f"{fname.lower()}.{lname.lower()}{i}@example.com"
    elif "phone" in col_lower:
        return f"+1-555-{2000 + i:04d}"
    elif "date" in col_lower:
        return f"2025-{((i * 2) % 12) + 1:02d}-{((i * 3) % 28) + 1:02d}"
    elif "city" in col_lower:
        return CITIES_STATES[(i - 1) % len(CITIES_STATES)][0]
    elif "state" in col_lower:
        return CITIES_STATES[(i - 1) % len(CITIES_STATES)][1]
    elif "country" in col_lower:
        return "United States"
    elif "postal" in col_lower or "zip" in col_lower:
        return f"{20000 + ((i * 419) % 79999):05d}"
    elif "salary" in col_lower or "billing" in col_lower or "spend" in col_lower or "price" in col_lower or "revenue" in col_lower:
        return round(float(2500.0 + ((i * 123.45) % 8500.0)), 2)
    elif "percent" in col_lower or "margin" in col_lower or "rate" in col_lower:
        return round(float(10.0 + ((i * 7.3) % 85.0)), 2)
    elif "score" in col_lower or "rating" in col_lower:
        return round(float(3.5 + ((i * 0.3) % 1.5)), 1)
    elif "status" in col_lower:
        return ["Active", "Completed", "Pending", "Verified"][(i - 1) % 4]
    elif "department" in col_lower:
        return DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
    elif "quantity" in col_lower or "count" in col_lower or "units" in col_lower or "age" in col_lower:
        return 10 + ((i * 3) % 90)
    else:
        return f"{column_name} {i}"


def generate_row_for_dataset(dataset_type: str, columns: List[str], row_index: int) -> List[Any]:
    """
    Produces a single row of values corresponding to the provided column names.
    """
    dt = dataset_type.lower()
    if "student" in dt or "school" in dt or "academic" in dt:
        return [generate_student_row_value(col, row_index) for col in columns]
    else:
        return [generate_generic_row_value(col, row_index, dataset_type) for col in columns]
