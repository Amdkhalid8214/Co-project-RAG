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

CRICKET_PRIMARY_COLUMNS = [
    "Player Name",
    "Country",
    "Role",
    "Batting Average",
    "Matches Played",
    "Total Runs",
    "Highest Score",
    "Wickets Taken",
    "Bowling Average",
    "Economy Rate",
    "Strike Rate",
    "Centuries (100s)",
    "Fifties (50s)",
    "Catches",
    "Debut Year",
    "Current Team / Franchise",
    "ICC Ranking Tier",
    "Player Jersey Number",
    "Batting Style",
    "Bowling Style"
]

POLITICIAN_PRIMARY_COLUMNS = [
    "Politician Name",
    "Country",
    "Office / Position",
    "Political Party",
    "Years in Office",
    "Term Status",
    "Key Policy Focus",
    "Constituency / State",
    "Era / Century",
    "Notable Achievement",
    "Approval Rating (%)",
    "Born Year",
    "Education",
    "Previous Role",
    "Head of Government"
]

FOOTBALL_PRIMARY_COLUMNS = [
    "Player Name",
    "Country",
    "Position",
    "Current Club",
    "League",
    "Jersey Number",
    "Goals Scored",
    "Assists",
    "Matches Played",
    "Ballon d'Or Awards",
    "Market Value (M$)",
    "Foot Preference",
    "Age",
    "Contract Until",
    "Trophies Won"
]

MOVIE_PRIMARY_COLUMNS = [
    "Movie Title",
    "Release Year",
    "Director",
    "Genre",
    "Lead Actor / Actress",
    "IMDb Rating",
    "Box Office ($M)",
    "Budget ($M)",
    "Academy Awards (Oscars)",
    "Country of Origin",
    "Runtime (Minutes)",
    "Production Studio",
    "Rotten Tomatoes Score (%)"
]

TECH_COMPANY_PRIMARY_COLUMNS = [
    "Company Name",
    "Headquarters",
    "Founding Year",
    "Founder / CEO",
    "Sector / Industry",
    "Market Cap ($B)",
    "Annual Revenue ($B)",
    "Employee Count",
    "Stock Ticker",
    "Primary Product",
    "Stock Exchange",
    "R&D Spend ($B)"
]

COUNTRY_PRIMARY_COLUMNS = [
    "Country Name",
    "Capital City",
    "Continent",
    "Population (Millions)",
    "Official Language",
    "Currency",
    "GDP ($B)",
    "Area (sq km)",
    "Government Type",
    "Calling Code"
]

CAR_PRIMARY_COLUMNS = [
    "Make / Brand",
    "Model",
    "Vehicle Type",
    "Horsepower (HP)",
    "Base Price ($)",
    "Fuel Type",
    "0-60 mph (sec)",
    "Top Speed (mph)",
    "Transmission",
    "Seating Capacity"
]

# ==============================================================================
# Authentic Domain Data Pools (ChatGPT-Grade Knowledge)
# ==============================================================================

CRICKET_PLAYERS_POOL = [
    {"name": "Virat Kohli", "country": "India", "role": "Top-order Batsman", "avg": 58.7, "matches": 295, "runs": 13906, "hs": 183, "wkts": 5, "bowl_avg": 64.8, "econ": 6.2, "sr": 93.5, "100s": 50, "50s": 72, "catches": 152, "debut": 2008, "team": "Royal Challengers Bengaluru", "tier": "Top 5", "jersey": 18, "bat": "Right-hand bat", "bowl": "Right-arm medium"},
    {"name": "Sachin Tendulkar", "country": "India", "role": "Top-order Batsman", "avg": 44.8, "matches": 463, "runs": 18426, "hs": 200, "wkts": 154, "bowl_avg": 44.5, "econ": 5.1, "sr": 86.2, "100s": 49, "50s": 96, "catches": 140, "debut": 1989, "team": "Mumbai Indians", "tier": "Legend", "jersey": 10, "bat": "Right-hand bat", "bowl": "Right-arm legbreak"},
    {"name": "Rohit Sharma", "country": "India", "role": "Opening Batsman", "avg": 49.2, "matches": 265, "runs": 10866, "hs": 264, "wkts": 9, "bowl_avg": 64.3, "econ": 5.2, "sr": 92.4, "100s": 31, "50s": 57, "catches": 93, "debut": 2007, "team": "Mumbai Indians", "tier": "Top 10", "jersey": 45, "bat": "Right-hand bat", "bowl": "Right-arm offbreak"},
    {"name": "MS Dhoni", "country": "India", "role": "Wicket-Keeper Batsman", "avg": 50.6, "matches": 350, "runs": 10773, "hs": 183, "wkts": 1, "bowl_avg": 31.0, "econ": 5.1, "sr": 87.6, "100s": 10, "50s": 73, "catches": 321, "debut": 2004, "team": "Chennai Super Kings", "tier": "Legend", "jersey": 7, "bat": "Right-hand bat", "bowl": "Right-arm medium"},
    {"name": "Steve Smith", "country": "Australia", "role": "Top-order Batsman", "avg": 58.0, "matches": 109, "runs": 9685, "hs": 239, "wkts": 19, "bowl_avg": 56.4, "econ": 4.1, "sr": 53.5, "100s": 32, "50s": 41, "catches": 181, "debut": 2010, "team": "Sydney Sixers", "tier": "Top 5", "jersey": 49, "bat": "Right-hand bat", "bowl": "Right-arm legbreak"},
    {"name": "Joe Root", "country": "England", "role": "Top-order Batsman", "avg": 50.6, "matches": 146, "runs": 12402, "hs": 254, "wkts": 70, "bowl_avg": 44.7, "econ": 3.4, "sr": 56.8, "100s": 34, "50s": 64, "catches": 204, "debut": 2012, "team": "Trent Rockets", "tier": "Top 5", "jersey": 66, "bat": "Right-hand bat", "bowl": "Right-arm offbreak"},
    {"name": "Kane Williamson", "country": "New Zealand", "role": "Top-order Batsman", "avg": 54.9, "matches": 100, "runs": 8743, "hs": 251, "wkts": 29, "bowl_avg": 40.2, "econ": 3.8, "sr": 51.4, "100s": 32, "50s": 34, "catches": 88, "debut": 2010, "team": "Gujarat Titans", "tier": "Top 5", "jersey": 22, "bat": "Right-hand bat", "bowl": "Right-arm offbreak"},
    {"name": "Jasprit Bumrah", "country": "India", "role": "Fast Bowler", "avg": 6.8, "matches": 36, "runs": 259, "hs": 34, "wkts": 159, "bowl_avg": 20.7, "econ": 2.7, "sr": 45.4, "100s": 0, "50s": 0, "catches": 14, "debut": 2018, "team": "Mumbai Indians", "tier": "Top 1", "jersey": 93, "bat": "Right-hand bat", "bowl": "Right-arm fast"},
    {"name": "Pat Cummins", "country": "Australia", "role": "Fast Bowler", "avg": 17.1, "matches": 62, "runs": 1295, "hs": 64, "wkts": 269, "bowl_avg": 22.5, "econ": 2.8, "sr": 47.1, "100s": 0, "50s": 3, "catches": 48, "debut": 2011, "team": "Sunrisers Hyderabad", "tier": "Top 5", "jersey": 30, "bat": "Right-hand bat", "bowl": "Right-arm fast"},
    {"name": "Ben Stokes", "country": "England", "role": "All-Rounder", "avg": 35.8, "matches": 105, "runs": 6508, "hs": 258, "wkts": 203, "bowl_avg": 32.1, "econ": 3.3, "sr": 59.2, "100s": 13, "50s": 31, "catches": 106, "debut": 2013, "team": "Northern Superchargers", "tier": "Top 10", "jersey": 55, "bat": "Left-hand bat", "bowl": "Right-arm fast-medium"},
    {"name": "Babar Azam", "country": "Pakistan", "role": "Top-order Batsman", "avg": 56.7, "matches": 117, "runs": 5729, "hs": 158, "wkts": 0, "bowl_avg": 0, "econ": 0, "sr": 88.8, "100s": 19, "50s": 32, "catches": 50, "debut": 2015, "team": "Peshawar Zalmi", "tier": "Top 5", "jersey": 56, "bat": "Right-hand bat", "bowl": "Right-arm offbreak"},
    {"name": "AB de Villiers", "country": "South Africa", "role": "Middle-order Batsman", "avg": 53.5, "matches": 228, "runs": 9577, "hs": 176, "wkts": 7, "bowl_avg": 28.9, "econ": 4.8, "sr": 101.1, "100s": 25, "50s": 53, "catches": 176, "debut": 2004, "team": "Royal Challengers Bengaluru", "tier": "Legend", "jersey": 17, "bat": "Right-hand bat", "bowl": "Right-arm medium"},
    {"name": "Shane Warne", "country": "Australia", "role": "Leg-Spin Bowler", "avg": 17.3, "matches": 145, "runs": 3154, "hs": 99, "wkts": 708, "bowl_avg": 25.4, "econ": 2.3, "sr": 57.4, "100s": 0, "50s": 12, "catches": 125, "debut": 1992, "team": "Rajasthan Royals", "tier": "Legend", "jersey": 23, "bat": "Right-hand bat", "bowl": "Right-arm legbreak"},
    {"name": "Brian Lara", "country": "West Indies", "role": "Top-order Batsman", "avg": 52.9, "matches": 131, "runs": 11953, "hs": 400, "wkts": 4, "bowl_avg": 60.5, "econ": 3.1, "sr": 60.5, "100s": 34, "50s": 48, "catches": 164, "debut": 1990, "team": "Trinidad & Tobago", "tier": "Legend", "jersey": 9, "bat": "Left-hand bat", "bowl": "Right-arm legbreak"},
    {"name": "Jacques Kallis", "country": "South Africa", "role": "All-Rounder", "avg": 55.4, "matches": 166, "runs": 13289, "hs": 224, "wkts": 292, "bowl_avg": 32.7, "econ": 2.8, "sr": 45.9, "100s": 45, "50s": 58, "catches": 200, "debut": 1995, "team": "Kolkata Knight Riders", "tier": "Legend", "jersey": 3, "bat": "Right-hand bat", "bowl": "Right-arm fast-medium"},
    {"name": "Mitchell Starc", "country": "Australia", "role": "Fast Bowler", "avg": 20.8, "matches": 89, "runs": 2095, "hs": 99, "wkts": 358, "bowl_avg": 27.7, "econ": 3.4, "sr": 48.5, "100s": 0, "50s": 10, "catches": 39, "debut": 2011, "team": "Kolkata Knight Riders", "tier": "Top 10", "jersey": 56, "bat": "Left-hand bat", "bowl": "Left-arm fast"},
    {"name": "Ravindra Jadeja", "country": "India", "role": "All-Rounder", "avg": 36.4, "matches": 72, "runs": 3036, "hs": 175, "wkts": 294, "bowl_avg": 24.1, "econ": 2.4, "sr": 58.7, "100s": 4, "50s": 20, "catches": 43, "debut": 2012, "team": "Chennai Super Kings", "tier": "Top 5", "jersey": 8, "bat": "Left-hand bat", "bowl": "Slow left-arm orthodox"},
    {"name": "Wasim Akram", "country": "Pakistan", "role": "Fast Bowler", "avg": 22.6, "matches": 104, "runs": 2898, "hs": 257, "wkts": 414, "bowl_avg": 23.6, "econ": 2.6, "sr": 54.6, "100s": 3, "50s": 7, "catches": 44, "debut": 1985, "team": "Lancashire", "tier": "Legend", "jersey": 1, "bat": "Left-hand bat", "bowl": "Left-arm fast"},
    {"name": "Glenn Maxwell", "country": "Australia", "role": "All-Rounder", "avg": 35.4, "matches": 142, "runs": 3934, "hs": 201, "wkts": 70, "bowl_avg": 50.2, "econ": 5.0, "sr": 126.9, "100s": 4, "50s": 23, "catches": 82, "debut": 2012, "team": "Royal Challengers Bengaluru", "tier": "Top 15", "jersey": 32, "bat": "Right-hand bat", "bowl": "Right-arm offbreak"},
    {"name": "Ricky Ponting", "country": "Australia", "role": "Top-order Batsman", "avg": 51.9, "matches": 168, "runs": 13378, "hs": 257, "wkts": 5, "bowl_avg": 47.0, "econ": 3.4, "sr": 58.7, "100s": 41, "50s": 62, "catches": 196, "debut": 1995, "team": "Mumbai Indians", "tier": "Legend", "jersey": 14, "bat": "Right-hand bat", "bowl": "Right-arm medium"}
]

POLITICIANS_POOL = [
    {"name": "Barack Obama", "country": "United States", "office": "44th President", "party": "Democratic Party", "years": "2009-2017", "status": "Completed", "policy": "Affordable Care Act & Climate Accords", "state": "Illinois", "era": "21st Century", "achieve": "Nobel Peace Prize 2009", "approval": 59.0, "born": 1961, "edu": "Harvard Law School", "prev": "U.S. Senator", "head": "Yes"},
    {"name": "Narendra Modi", "country": "India", "office": "Prime Minister", "party": "Bharatiya Janata Party", "years": "2014-Present", "status": "Incumbent", "policy": "Digital India & Infrastructure", "state": "Varanasi, UP", "era": "21st Century", "achieve": "G20 Presidency & UPI Expansion", "approval": 73.0, "born": 1950, "edu": "Gujarat University", "prev": "Chief Minister of Gujarat", "head": "Yes"},
    {"name": "Winston Churchill", "country": "United Kingdom", "office": "Prime Minister", "party": "Conservative Party", "years": "1940-1945, 1951-1955", "status": "Historical", "policy": "WWII Allied Victory Defense", "state": "Woodstock, Oxfordshire", "era": "20th Century", "achieve": "Nobel Prize in Literature 1953", "approval": 83.0, "born": 1874, "edu": "Royal Military College, Sandhurst", "prev": "First Lord of the Admiralty", "head": "Yes"},
    {"name": "Abraham Lincoln", "country": "United States", "office": "16th President", "party": "Republican Party", "years": "1861-1865", "status": "Historical", "policy": "Preservation of Union & Emancipation", "state": "Illinois", "era": "19th Century", "achieve": "Emancipation Proclamation", "approval": 88.0, "born": 1809, "edu": "Self-educated (Law)", "prev": "U.S. Representative", "head": "Yes"},
    {"name": "Nelson Mandela", "country": "South Africa", "office": "President", "party": "African National Congress", "years": "1994-1999", "status": "Historical", "policy": "Anti-Apartheid Reconciliation", "state": "Eastern Cape", "era": "20th Century", "achieve": "Nobel Peace Prize 1993", "approval": 92.0, "born": 1918, "edu": "University of South Africa", "prev": "Anti-Apartheid Leader", "head": "Yes"},
    {"name": "Angela Merkel", "country": "Germany", "office": "Chancellor", "party": "Christian Democratic Union", "years": "2005-2021", "status": "Completed", "policy": "European Union Stability & Energy Transition", "state": "Mecklenburg-Vorpommern", "era": "21st Century", "achieve": "Longest Serving Female EU Leader", "approval": 68.0, "born": 1954, "edu": "Leipzig University (Ph.D. Physics)", "prev": "Minister of Environment", "head": "Yes"},
    {"name": "Emmanuel Macron", "country": "France", "office": "President", "party": "Renaissance", "years": "2017-Present", "status": "Incumbent", "policy": "European Strategic Autonomy & Pension Reform", "state": "Amiens", "era": "21st Century", "achieve": "Youngest French President", "approval": 38.0, "born": 1977, "edu": "ENA / Sciences Po", "prev": "Minister of Economy", "head": "Yes"},
    {"name": "Jacinda Ardern", "country": "New Zealand", "office": "Prime Minister", "party": "Labour Party", "years": "2017-2023", "status": "Completed", "policy": "Wellbeing Budget & Crisis Leadership", "state": "Mount Albert", "era": "21st Century", "achieve": "Christchurch Call Initiative", "approval": 65.0, "born": 1980, "edu": "University of Waikato", "prev": "Member of Parliament", "head": "Yes"},
    {"name": "Lee Kuan Yew", "country": "Singapore", "office": "Prime Minister", "party": "People's Action Party", "years": "1959-1990", "status": "Historical", "policy": "Economic Transformation & Anti-Corruption", "state": "Tanjong Pagar", "era": "20th Century", "achieve": "First World Metropolis Transformation", "approval": 89.0, "born": 1923, "edu": "Fitzwilliam College, Cambridge", "prev": "Barrister", "head": "Yes"},
    {"name": "Franklin D. Roosevelt", "country": "United States", "office": "32nd President", "party": "Democratic Party", "years": "1933-1945", "status": "Historical", "policy": "New Deal & WWII Allied Strategy", "state": "New York", "era": "20th Century", "achieve": "Social Security & Four Terms Elected", "approval": 76.0, "born": 1882, "edu": "Harvard University & Columbia Law", "prev": "Governor of New York", "head": "Yes"},
    {"name": "Justin Trudeau", "country": "Canada", "office": "Prime Minister", "party": "Liberal Party", "years": "2015-Present", "status": "Incumbent", "policy": "Climate Action & Immigration Growth", "state": "Papineau, Quebec", "era": "21st Century", "achieve": "Canada Child Benefit Reform", "approval": 42.0, "born": 1971, "edu": "McGill University", "prev": "Member of Parliament", "head": "Yes"},
    {"name": "Shinzo Abe", "country": "Japan", "office": "Prime Minister", "party": "Liberal Democratic Party", "years": "2006-2007, 2012-2020", "status": "Historical", "policy": "Abenomics & Free and Open Indo-Pacific", "state": "Yamaguchi", "era": "21st Century", "achieve": "CPTPP Trade Agreement Leadership", "approval": 62.0, "born": 1954, "edu": "Seikei University", "prev": "Chief Cabinet Secretary", "head": "Yes"},
    {"name": "Margaret Thatcher", "country": "United Kingdom", "office": "Prime Minister", "party": "Conservative Party", "years": "1979-1990", "status": "Historical", "policy": "Free Market Deregulation & Privatization", "state": "Finchley", "era": "20th Century", "achieve": "First Female British Prime Minister", "approval": 54.0, "born": 1925, "edu": "Somerville College, Oxford", "prev": "Secretary of State for Education", "head": "Yes"},
    {"name": "John F. Kennedy", "country": "United States", "office": "35th President", "party": "Democratic Party", "years": "1961-1963", "status": "Historical", "policy": "New Frontier & Apollo Moon Program", "state": "Massachusetts", "era": "20th Century", "achieve": "Peace Corps & Cuban Missile Resolution", "approval": 70.0, "born": 1917, "edu": "Harvard University", "prev": "U.S. Senator", "head": "Yes"},
    {"name": "APJ Abdul Kalam", "country": "India", "office": "11th President", "party": "Independent", "years": "2002-2007", "status": "Historical", "policy": "Vision 2020 & Scientific Education", "state": "Rameswaram, Tamil Nadu", "era": "21st Century", "achieve": "Puri Aerospace & Pokhran-II Leader", "approval": 95.0, "born": 1931, "edu": "Madras Institute of Technology", "prev": "Chief Scientific Adviser to PM", "head": "Yes"},
    {"name": "Tony Blair", "country": "United Kingdom", "office": "Prime Minister", "party": "Labour Party", "years": "1997-2007", "status": "Completed", "policy": "New Labour Modernization & Devolution", "state": "Sedgefield", "era": "20th/21st Century", "achieve": "Good Friday Agreement 1998", "approval": 52.0, "born": 1953, "edu": "St John's College, Oxford", "prev": "Leader of the Opposition", "head": "Yes"}
]

FOOTBALL_PLAYERS_POOL = [
    {"name": "Lionel Messi", "country": "Argentina", "pos": "Forward", "club": "Inter Miami CF", "league": "MLS", "jersey": 10, "goals": 838, "assists": 374, "matches": 1069, "ballon": 8, "val": 35.0, "foot": "Left", "age": 37, "contract": "2025", "trophies": 44},
    {"name": "Cristiano Ronaldo", "country": "Portugal", "pos": "Forward", "club": "Al-Nassr FC", "league": "Saudi Pro League", "jersey": 7, "goals": 901, "assists": 255, "matches": 1235, "ballon": 5, "val": 15.0, "foot": "Right", "age": 39, "contract": "2025", "trophies": 33},
    {"name": "Kylian Mbappé", "country": "France", "pos": "Forward", "club": "Real Madrid", "league": "La Liga", "jersey": 9, "goals": 332, "assists": 154, "matches": 450, "ballon": 0, "val": 180.0, "foot": "Right", "age": 25, "contract": "2029", "trophies": 19},
    {"name": "Erling Haaland", "country": "Norway", "pos": "Striker", "club": "Manchester City", "league": "Premier League", "jersey": 9, "goals": 256, "assists": 52, "matches": 312, "ballon": 0, "val": 180.0, "foot": "Left", "age": 24, "contract": "2027", "trophies": 9},
    {"name": "Kevin De Bruyne", "country": "Belgium", "pos": "Midfielder", "club": "Manchester City", "league": "Premier League", "jersey": 17, "goals": 145, "assists": 286, "matches": 610, "ballon": 0, "val": 50.0, "foot": "Right", "age": 33, "contract": "2025", "trophies": 21},
    {"name": "Luka Modrić", "country": "Croatia", "pos": "Midfielder", "club": "Real Madrid", "league": "La Liga", "jersey": 10, "goals": 88, "assists": 142, "matches": 820, "ballon": 1, "val": 8.0, "foot": "Right", "age": 39, "contract": "2025", "trophies": 27},
    {"name": "Vinícius Júnior", "country": "Brazil", "pos": "Winger", "club": "Real Madrid", "league": "La Liga", "jersey": 7, "goals": 95, "assists": 82, "matches": 280, "ballon": 0, "val": 180.0, "foot": "Right", "age": 24, "contract": "2027", "trophies": 13},
    {"name": "Jude Bellingham", "country": "England", "pos": "Midfielder", "club": "Real Madrid", "league": "La Liga", "jersey": 5, "goals": 52, "assists": 38, "matches": 220, "ballon": 0, "val": 180.0, "foot": "Right", "age": 21, "contract": "2029", "trophies": 5}
]

MOVIES_POOL = [
    {"title": "The Godfather", "year": 1972, "director": "Francis Ford Coppola", "genre": "Crime, Drama", "lead": "Marlon Brando, Al Pacino", "imdb": 9.2, "box": 250.0, "budget": 6.0, "oscars": 3, "country": "United States", "runtime": 175, "studio": "Paramount Pictures", "rt": 97},
    {"title": "The Dark Knight", "year": 2008, "director": "Christopher Nolan", "genre": "Action, Crime, Drama", "lead": "Christian Bale, Heath Ledger", "imdb": 9.0, "box": 1006.0, "budget": 185.0, "oscars": 2, "country": "United States", "runtime": 152, "studio": "Warner Bros.", "rt": 94},
    {"title": "Inception", "year": 2010, "director": "Christopher Nolan", "genre": "Sci-Fi, Action", "lead": "Leonardo DiCaprio, Elliot Page", "imdb": 8.8, "box": 836.8, "budget": 160.0, "oscars": 4, "country": "United States", "runtime": 148, "studio": "Warner Bros.", "rt": 87},
    {"title": "Pulp Fiction", "year": 1994, "director": "Quentin Tarantino", "genre": "Crime, Drama", "lead": "John Travolta, Samuel L. Jackson", "imdb": 8.9, "box": 213.9, "budget": 8.5, "oscars": 1, "country": "United States", "runtime": 154, "studio": "Miramax", "rt": 92},
    {"title": "Titanic", "year": 1997, "director": "James Cameron", "genre": "Drama, Romance", "lead": "Leonardo DiCaprio, Kate Winslet", "imdb": 7.9, "box": 2257.0, "budget": 200.0, "oscars": 11, "country": "United States", "runtime": 195, "studio": "20th Century Fox", "rt": 88},
    {"title": "Interstellar", "year": 2014, "director": "Christopher Nolan", "genre": "Sci-Fi, Adventure", "lead": "Matthew McConaughey, Anne Hathaway", "imdb": 8.7, "box": 731.0, "budget": 165.0, "oscars": 1, "country": "United States", "runtime": 169, "studio": "Paramount Pictures", "rt": 73},
    {"title": "Parasite", "year": 2019, "director": "Bong Joon-ho", "genre": "Drama, Thriller", "lead": "Song Kang-ho, Lee Sun-kyun", "imdb": 8.5, "box": 263.1, "budget": 15.5, "oscars": 4, "country": "South Korea", "runtime": 132, "studio": "CJ Entertainment", "rt": 99},
    {"title": "Forrest Gump", "year": 1994, "director": "Robert Zemeckis", "genre": "Drama, Romance", "lead": "Tom Hanks, Robin Wright", "imdb": 8.8, "box": 678.2, "budget": 55.0, "oscars": 6, "country": "United States", "runtime": 142, "studio": "Paramount Pictures", "rt": 71}
]

TECH_COMPANIES_POOL = [
    {"name": "Apple Inc.", "hq": "Cupertino, California, USA", "year": 1976, "ceo": "Tim Cook", "sector": "Consumer Electronics & Services", "mcap": 3500.0, "rev": 383.0, "emp": 161000, "ticker": "AAPL", "prod": "iPhone & iOS", "exch": "NASDAQ", "rnd": 29.9},
    {"name": "Microsoft Corporation", "hq": "Redmond, Washington, USA", "year": 1975, "ceo": "Satya Nadella", "sector": "Enterprise Software & Cloud", "mcap": 3150.0, "rev": 245.0, "emp": 221000, "ticker": "MSFT", "prod": "Azure & Windows", "exch": "NASDAQ", "rnd": 29.5},
    {"name": "NVIDIA Corporation", "hq": "Santa Clara, California, USA", "year": 1993, "ceo": "Jensen Huang", "sector": "Semiconductors & AI Compute", "mcap": 3400.0, "rev": 120.0, "emp": 29600, "ticker": "NVDA", "prod": "Blackwell & H100 GPUs", "exch": "NASDAQ", "rnd": 11.2},
    {"name": "Alphabet Inc.", "hq": "Mountain View, California, USA", "year": 1998, "ceo": "Sundar Pichai", "sector": "Internet Services & AI", "mcap": 2150.0, "rev": 307.0, "emp": 182500, "ticker": "GOOGL", "prod": "Google Search & YouTube", "exch": "NASDAQ", "rnd": 45.4},
    {"name": "Amazon.com Inc.", "hq": "Seattle, Washington, USA", "year": 1994, "ceo": "Andy Jassy", "sector": "E-Commerce & Cloud Computing", "mcap": 1950.0, "rev": 574.0, "emp": 1525000, "ticker": "AMZN", "prod": "Amazon Web Services (AWS)", "exch": "NASDAQ", "rnd": 85.6},
    {"name": "Meta Platforms Inc.", "hq": "Menlo Park, California, USA", "year": 2004, "ceo": "Mark Zuckerberg", "sector": "Social Media & AI", "mcap": 1450.0, "rev": 134.9, "emp": 67300, "ticker": "META", "prod": "Instagram, WhatsApp & Llama", "exch": "NASDAQ", "rnd": 38.5},
    {"name": "Tesla Inc.", "hq": "Austin, Texas, USA", "year": 2003, "ceo": "Elon Musk", "sector": "Electric Vehicles & Clean Energy", "mcap": 750.0, "rev": 96.8, "emp": 140000, "ticker": "TSLA", "prod": "Model Y & Autopilot FSD", "exch": "NASDAQ", "rnd": 3.9},
    {"name": "TSMC", "hq": "Hsinchu, Taiwan", "year": 1987, "ceo": "C.C. Wei", "sector": "Pure-Play Semiconductor Foundry", "mcap": 900.0, "rev": 72.0, "emp": 73000, "ticker": "TSM", "prod": "3nm & 2nm Wafer Fabrication", "exch": "NYSE", "rnd": 5.8}
]

COUNTRIES_POOL = [
    {"name": "United States", "capital": "Washington, D.C.", "continent": "North America", "pop": 334.9, "lang": "English", "curr": "USD ($)", "gdp": 27360.0, "area": 9833517, "gov": "Federal Republic", "code": "+1"},
    {"name": "India", "capital": "New Delhi", "continent": "Asia", "pop": 1428.6, "lang": "Hindi, English", "curr": "INR (₹)", "gdp": 3750.0, "area": 3287263, "gov": "Federal Parliamentary Republic", "code": "+91"},
    {"name": "United Kingdom", "capital": "London", "continent": "Europe", "pop": 67.7, "lang": "English", "curr": "GBP (£)", "gdp": 3340.0, "area": 242495, "gov": "Parliamentary Constitutional Monarchy", "code": "+44"},
    {"name": "Germany", "capital": "Berlin", "continent": "Europe", "pop": 84.4, "lang": "German", "curr": "EUR (€)", "gdp": 4450.0, "area": 357022, "gov": "Federal Parliamentary Republic", "code": "+49"},
    {"name": "Japan", "capital": "Tokyo", "continent": "Asia", "pop": 124.5, "lang": "Japanese", "curr": "JPY (¥)", "gdp": 4210.0, "area": 377975, "gov": "Parliamentary Constitutional Monarchy", "code": "+81"},
    {"name": "France", "capital": "Paris", "continent": "Europe", "pop": 68.0, "lang": "French", "curr": "EUR (€)", "gdp": 3030.0, "area": 551695, "gov": "Semi-Presidential Republic", "code": "+33"},
    {"name": "Australia", "capital": "Canberra", "continent": "Oceania", "pop": 26.6, "lang": "English", "curr": "AUD ($)", "gdp": 1720.0, "area": 7692024, "gov": "Federal Parliamentary Monarchy", "code": "+61"},
    {"name": "Canada", "capital": "Ottawa", "continent": "North America", "pop": 40.1, "lang": "English, French", "curr": "CAD ($)", "gdp": 2140.0, "area": 9984670, "gov": "Federal Parliamentary Monarchy", "code": "+1"}
]

CARS_POOL = [
    {"make": "Porsche", "model": "911 GT3 RS", "type": "Sports Car", "hp": 518, "price": 241300, "fuel": "Gasoline", "accel": 3.0, "top_spd": 184, "trans": "7-Speed Dual-Clutch (PDK)", "seats": 2},
    {"make": "Tesla", "model": "Model S Plaid", "type": "Sedan", "hp": 1020, "price": 89990, "fuel": "Electric (EV)", "accel": 1.99, "top_spd": 200, "trans": "Single-Speed Direct Drive", "seats": 5},
    {"make": "BMW", "model": "M3 Competition", "type": "Sport Sedan", "hp": 503, "price": 80200, "fuel": "Gasoline", "accel": 3.4, "top_spd": 180, "trans": "8-Speed Automatic", "seats": 5},
    {"make": "Mercedes-AMG", "model": "GT Coupe", "type": "Sports Coupe", "hp": 577, "price": 175900, "fuel": "Gasoline", "accel": 3.1, "top_spd": 196, "trans": "9-Speed Multi-Clutch", "seats": 4},
    {"make": "Toyota", "model": "Supra GR 3.0", "type": "Coupe", "hp": 382, "price": 56250, "fuel": "Gasoline", "accel": 3.9, "top_spd": 155, "trans": "6-Speed Manual / 8-Speed Auto", "seats": 2},
    {"make": "Ferrari", "model": "296 GTB", "type": "Supercar", "hp": 819, "price": 342200, "fuel": "Plug-in Hybrid", "accel": 2.9, "top_spd": 205, "trans": "8-Speed Dual-Clutch", "seats": 2},
    {"make": "Audi", "model": "RS6 Avant", "type": "Super Wagon", "hp": 621, "price": 125800, "fuel": "Mild Hybrid V8", "accel": 3.3, "top_spd": 190, "trans": "8-Speed Tiptronic", "seats": 5},
    {"make": "Ford", "model": "Mustang Dark Horse", "type": "Muscle Car", "hp": 500, "price": 60865, "fuel": "Gasoline V8", "accel": 4.1, "top_spd": 166, "trans": "6-Speed Tremec Manual", "seats": 4}
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
    elif "crick" in dt or "batsm" in dt or "bowl" in dt:
        primary = CRICKET_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "politi" in dt or "policti" in dt or "president" in dt or "minister" in dt:
        primary = POLITICIAN_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "football" in dt or "soccer" in dt:
        primary = FOOTBALL_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "movie" in dt or "film" in dt or "cinema" in dt:
        primary = MOVIE_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "compan" in dt or "tech" in dt:
        primary = TECH_COMPANY_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "countr" in dt or "nation" in dt or "capital" in dt:
        primary = COUNTRY_PRIMARY_COLUMNS
        extended = GENERAL_PRIMARY_COLUMNS
    elif "car" in dt or "auto" in dt or "vehicle" in dt:
        primary = CAR_PRIMARY_COLUMNS
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


def generate_cricket_row_value(column_name: str, row_idx: int) -> Any:
    p = CRICKET_PLAYERS_POOL[(row_idx - 1) % len(CRICKET_PLAYERS_POOL)]
    col = column_name.lower()
    if "name" in col or "player" in col:
        return p["name"]
    elif "country" in col or "nation" in col or ("team" in col and "franchise" not in col):
        return p["country"]
    elif "role" in col or "position" in col or "special" in col:
        return p["role"]
    elif "batting average" in col or "average" in col or "avg" in col:
        return p["avg"]
    elif "matches" in col or "match" in col:
        return p["matches"]
    elif "total runs" in col or "runs" in col:
        return p["runs"]
    elif "highest" in col or "hs" in col:
        return p["hs"]
    elif "wicket" in col:
        return p["wkts"]
    elif "bowling average" in col:
        return p["bowl_avg"]
    elif "economy" in col or "econ" in col:
        return p["econ"]
    elif "strike" in col or "sr" in col:
        return p["sr"]
    elif "centur" in col or "100" in col:
        return p["100s"]
    elif "fift" in col or "50" in col:
        return p["50s"]
    elif "catch" in col:
        return p["catches"]
    elif "debut" in col:
        return p["debut"]
    elif "franchise" in col or "club" in col:
        return p["team"]
    elif "tier" in col or "rank" in col:
        return p["tier"]
    elif "jersey" in col or "number" in col:
        return p["jersey"]
    elif "bowling style" in col:
        return p["bowl"]
    elif "batting style" in col or "style" in col:
        return p["bat"]
    else:
        return f"{p['name']} {column_name}"


def generate_politician_row_value(column_name: str, row_idx: int) -> Any:
    p = POLITICIANS_POOL[(row_idx - 1) % len(POLITICIANS_POOL)]
    col = column_name.lower()
    if "name" in col or "politician" in col or "leader" in col:
        return p["name"]
    elif "country" in col or "nation" in col:
        return p["country"]
    elif "office" in col or "position" in col or "role" in col:
        return p["office"]
    elif "party" in col:
        return p["party"]
    elif "years" in col or "term" in col or "period" in col:
        return p["years"]
    elif "status" in col:
        return p["status"]
    elif "policy" in col or "focus" in col:
        return p["policy"]
    elif "constituency" in col or "state" in col or "province" in col:
        return p["state"]
    elif "era" in col or "century" in col:
        return p["era"]
    elif "achieve" in col or "notable" in col:
        return p["achieve"]
    elif "approval" in col or "rating" in col:
        return p["approval"]
    elif "born" in col or "birth" in col:
        return p["born"]
    elif "edu" in col:
        return p["edu"]
    elif "previous" in col or "prior" in col:
        return p["prev"]
    elif "head" in col:
        return p["head"]
    else:
        return f"{p['name']} {column_name}"


def generate_football_row_value(column_name: str, row_idx: int) -> Any:
    p = FOOTBALL_PLAYERS_POOL[(row_idx - 1) % len(FOOTBALL_PLAYERS_POOL)]
    col = column_name.lower()
    if "name" in col or "player" in col:
        return p["name"]
    elif "country" in col or "nation" in col:
        return p["country"]
    elif "position" in col or "pos" in col or "role" in col:
        return p["pos"]
    elif "club" in col or "team" in col:
        return p["club"]
    elif "league" in col:
        return p["league"]
    elif "jersey" in col or "number" in col:
        return p["jersey"]
    elif "goal" in col:
        return p["goals"]
    elif "assist" in col:
        return p["assists"]
    elif "matches" in col or "appearance" in col:
        return p["matches"]
    elif "ballon" in col or "award" in col:
        return p["ballon"]
    elif "market" in col or "value" in col or "price" in col:
        return p["val"]
    elif "foot" in col:
        return p["foot"]
    elif "age" in col:
        return p["age"]
    elif "contract" in col:
        return p["contract"]
    elif "troph" in col or "title" in col:
        return p["trophies"]
    else:
        return f"{p['name']} {column_name}"


def generate_movie_row_value(column_name: str, row_idx: int) -> Any:
    p = MOVIES_POOL[(row_idx - 1) % len(MOVIES_POOL)]
    col = column_name.lower()
    if "title" in col or "movie" in col or "film" in col or "name" in col:
        return p["title"]
    elif "year" in col or "release" in col:
        return p["year"]
    elif "director" in col:
        return p["director"]
    elif "genre" in col:
        return p["genre"]
    elif "actor" in col or "actress" in col or "lead" in col or "star" in col:
        return p["lead"]
    elif "imdb" in col or "rating" in col:
        return p["imdb"]
    elif "box" in col or "gross" in col:
        return p["box"]
    elif "budget" in col:
        return p["budget"]
    elif "oscar" in col or "award" in col:
        return p["oscars"]
    elif "country" in col:
        return p["country"]
    elif "runtime" in col or "duration" in col:
        return p["runtime"]
    elif "studio" in col or "production" in col:
        return p["studio"]
    elif "rotten" in col or "score" in col:
        return p["rt"]
    else:
        return f"{p['title']} {column_name}"


def generate_company_row_value(column_name: str, row_idx: int) -> Any:
    p = TECH_COMPANIES_POOL[(row_idx - 1) % len(TECH_COMPANIES_POOL)]
    col = column_name.lower()
    if "name" in col or "company" in col:
        return p["name"]
    elif "headquarter" in col or "hq" in col or "location" in col:
        return p["hq"]
    elif "year" in col or "found" in col:
        return p["year"]
    elif "ceo" in col or "founder" in col or "leader" in col:
        return p["ceo"]
    elif "sector" in col or "industry" in col:
        return p["sector"]
    elif "market cap" in col or "cap" in col or "val" in col:
        return p["mcap"]
    elif "revenue" in col or "sales" in col:
        return p["rev"]
    elif "employee" in col or "staff" in col or "count" in col:
        return p["emp"]
    elif "ticker" in col or "symbol" in col:
        return p["ticker"]
    elif "product" in col or "service" in col:
        return p["prod"]
    elif "exchange" in col:
        return p["exch"]
    elif "rnd" in col or "r&d" in col:
        return p["rnd"]
    else:
        return f"{p['name']} {column_name}"


def generate_country_row_value(column_name: str, row_idx: int) -> Any:
    p = COUNTRIES_POOL[(row_idx - 1) % len(COUNTRIES_POOL)]
    col = column_name.lower()
    if "country" in col or "nation" in col or "name" in col:
        return p["name"]
    elif "capital" in col or "city" in col:
        return p["capital"]
    elif "continent" in col or "region" in col:
        return p["continent"]
    elif "population" in col or "pop" in col:
        return p["pop"]
    elif "language" in col or "lang" in col:
        return p["lang"]
    elif "currency" in col or "money" in col:
        return p["curr"]
    elif "gdp" in col:
        return p["gdp"]
    elif "area" in col or "size" in col:
        return p["area"]
    elif "government" in col or "gov" in col:
        return p["gov"]
    elif "code" in col:
        return p["code"]
    else:
        return f"{p['name']} {column_name}"


def generate_car_row_value(column_name: str, row_idx: int) -> Any:
    p = CARS_POOL[(row_idx - 1) % len(CARS_POOL)]
    col = column_name.lower()
    if "make" in col or "brand" in col or "manufacturer" in col:
        return p["make"]
    elif "model" in col:
        return p["model"]
    elif "type" in col or "class" in col:
        return p["type"]
    elif "hp" in col or "horsepower" in col or "power" in col:
        return p["hp"]
    elif "price" in col or "cost" in col or "msrp" in col:
        return p["price"]
    elif "fuel" in col or "engine" in col:
        return p["fuel"]
    elif "0-60" in col or "accel" in col:
        return p["accel"]
    elif "speed" in col or "top" in col:
        return p["top_spd"]
    elif "transmission" in col or "gearbox" in col:
        return p["trans"]
    elif "seat" in col or "capacity" in col:
        return p["seats"]
    elif "name" in col:
        return f"{p['make']} {p['model']}"
    else:
        return f"{p['make']} {column_name}"


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
    Directs to specialized domain generators for realistic entities (cricket, politicians, etc.).
    """
    dt = dataset_type.lower()
    if "student" in dt or "school" in dt or "academic" in dt:
        return [generate_student_row_value(col, row_index) for col in columns]
    elif "crick" in dt or "batsm" in dt or "bowl" in dt:
        return [generate_cricket_row_value(col, row_index) for col in columns]
    elif "politi" in dt or "policti" in dt or "president" in dt or "minister" in dt:
        return [generate_politician_row_value(col, row_index) for col in columns]
    elif "football" in dt or "soccer" in dt:
        return [generate_football_row_value(col, row_index) for col in columns]
    elif "movie" in dt or "film" in dt or "cinema" in dt:
        return [generate_movie_row_value(col, row_index) for col in columns]
    elif "compan" in dt or "tech" in dt:
        return [generate_company_row_value(col, row_index) for col in columns]
    elif "countr" in dt or "nation" in dt or "capital" in dt:
        return [generate_country_row_value(col, row_index) for col in columns]
    elif "car" in dt or "auto" in dt or "vehicle" in dt:
        return [generate_car_row_value(col, row_index) for col in columns]
    else:
        return [generate_generic_row_value(col, row_index, dataset_type) for col in columns]
