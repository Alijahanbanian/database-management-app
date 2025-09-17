import sys
import sqlite3
import xml.etree.ElementTree as ET
import json
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QTabWidget, QLabel, QTableWidget, QTableWidgetItem, QDialog, QTextEdit,
    QScrollArea
)
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.figure import Figure  
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


# Logging setup
logging.basicConfig(filename='errors.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def is_number(value, allow_float=True):
    try:
        if value is None:
            return False
        if allow_float:
            float(value)
        else:
            int(value)
        return True
    except (ValueError, TypeError):
        return False
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi) 
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

class DatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Management System")
        self.setGeometry(400, 250, 500, 300)
        
        # connect to DataBase
        self.conn = sqlite3.connect('project.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

        # tabs
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # upload tab
        upload_tab = QWidget()
        upload_layout = QVBoxLayout()
        upload_layout.addWidget(QLabel("Upload your data files here:"))
        btn_xml = QPushButton("Upload XML")
        btn_xml.clicked.connect(self.upload_xml)
        btn_json = QPushButton("Upload JSON")
        btn_json.clicked.connect(self.upload_json)
        upload_layout.addSpacing(10)
        upload_layout.addWidget(btn_xml)
        upload_layout.addWidget(btn_json)
        upload_layout.addStretch()
        upload_tab.setLayout(upload_layout)
        self.tabs.addTab(upload_tab, "Upload Files")

        # view tab
        views_tab = QWidget()
        views_layout = QVBoxLayout()
        views_layout.addWidget(QLabel("View pre-defined data summaries:"))
        btn_view1 = QPushButton("Show Facilities by State")
        btn_view1.clicked.connect(lambda: self.show_view('FacilitiesByState', ['State', 'FacilityCount']))
        btn_view2 = QPushButton("Show Avg Salary by Job")
        btn_view2.clicked.connect(lambda: self.show_view('View_AvgSalaryByJob', ['Job Title', 'Avg Salary', 'Employee Count']))
        btn_view3 = QPushButton("Show Programs by Interest Type")
        btn_view3.clicked.connect(lambda: self.show_view('CountProgramsByInterestType', ['Interest Type ID', 'Program Count', 'Program Common Name']))
        views_layout.addSpacing(10)
        views_layout.addWidget(btn_view1)
        views_layout.addWidget(btn_view2)
        views_layout.addWidget(btn_view3)
        views_layout.addStretch()
        views_tab.setLayout(views_layout)
        self.tabs.addTab(views_tab, "Views")

        # SQL tab
        sql_tab = QWidget()
        sql_layout = QVBoxLayout()
        sql_layout.addWidget(QLabel("Run custom SQL queries:"))
        self.sql_entry = QTextEdit()
        sql_layout.addWidget(self.sql_entry)
        btn_run = QPushButton("Run Query")
        btn_run.clicked.connect(self.run_sql_query)
        sql_layout.addSpacing(10)
        sql_layout.addWidget(btn_run)
        sql_layout.addStretch()
        sql_tab.setLayout(sql_layout)
        self.tabs.addTab(sql_tab, "SQL Query")
        
        vis_tab = QWidget()
        vis_layout = QVBoxLayout()
        vis_layout.addWidget(QLabel("Visualize data:"))
        btn_chart2 = QPushButton("Avg Salary by Job Title")
        btn_chart2.clicked.connect(self.plot_avg_salary_by_job)
        btn_chart3 = QPushButton("Employees by Gender")
        btn_chart3.clicked.connect(self.plot_gender_distribution)
        btn_programs = QPushButton("Programs by InterestType")
        btn_programs.clicked.connect(self.plot_programs_by_interest)
        btn_avg_exp_by_dept = QPushButton("Avg Experience by Department")
        btn_avg_exp_by_dept.clicked.connect(self.plot_avg_experience_by_department)
        btn_facilities_per_state = QPushButton("Facilities per State (Bar)")
        btn_facilities_per_state.clicked.connect(self.plot_facilities_per_state)
        btn_employee_dept_pie = QPushButton("Employee Dept Distribution (Pie)")
        btn_employee_dept_pie.clicked.connect(self.plot_employee_dept_pie)
        btn_employee_job_pie = QPushButton("Employee job Distribution (Pie)")
        btn_employee_job_pie.clicked.connect(self.plot_employee_job_pie)
        btn_age_histogram = QPushButton("Age Distribution (Histogram)")
        btn_age_histogram.clicked.connect(self.plot_age_histogram)
        btn_salary_vs_exp_line = QPushButton("Salary vs Experience (Line)")
        btn_salary_vs_exp_line.clicked.connect(self.plot_salary_vs_exp_line)
        btn_facilities_map = QPushButton("Facilities on Map")
        btn_facilities_map.clicked.connect(self.plot_facilities_scatter)
        
        
        vis_layout.addSpacing(10)
        vis_layout.addWidget(btn_chart2)
        vis_layout.addWidget(btn_chart3)
        vis_layout.addWidget(btn_programs)
        vis_layout.addWidget(btn_avg_exp_by_dept)        
        vis_layout.addWidget(btn_facilities_per_state)
        vis_layout.addWidget(btn_employee_dept_pie)
        vis_layout.addWidget(btn_employee_job_pie)
        vis_layout.addWidget(btn_age_histogram)
        vis_layout.addWidget(btn_salary_vs_exp_line)
        vis_layout.addWidget(btn_facilities_map)
        vis_layout.addStretch()
        vis_tab.setLayout(vis_layout)
        self.tabs.addTab(vis_tab, "Visualization")


        # help
        

    def create_tables(self):
        # Table Facilities
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Facilities (
                registry_id TEXT PRIMARY KEY,
                facility_site_name TEXT,
                location_address_text TEXT,
                electronic_address TEXT,
                electronic_address_typename TEXT
            )
        ''')
        # Table Coordinates
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Coordinates (
                registry_id TEXT PRIMARY KEY,
                latitude_measure REAL,
                longitude_measure REAL,
                horizontal_coordinate_reference_system_datum_name TEXT,
                horizontal_collection_method_name TEXT
            )
        ''')
        # Table Locations
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Locations (
                registry_id TEXT PRIMARY KEY,
                location_zip_code TEXT,
                locality_name TEXT,
                location_address_state_code TEXT
            )
        ''')
        # Table ProgramAttributes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProgramAttributes (
                interest_type_id TEXT PRIMARY KEY,
                program_common_name TEXT,
                program_acronym_name TEXT,
                program_description TEXT,
                electronic_address TEXT,
                electronic_address_typename TEXT,
                FOREIGN KEY (interest_type_id) REFERENCES ProgramInterestTypes (interest_type_id)
            )
        ''')
        # Table Programs
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Programs (
                program_identifier TEXT,
                program_full_name TEXT,
                interest_type_id TEXT,
                PRIMARY KEY (program_identifier, program_full_name),
                FOREIGN KEY (interest_type_id) REFERENCES ProgramInterestTypes (interest_type_id)
            )
        ''')
        # Table FacilityPrograms
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS FacilityPrograms (
                registry_id TEXT,
                program_identifier TEXT,
                program_full_name TEXT,
                PRIMARY KEY (registry_id, program_identifier, program_full_name),
                FOREIGN KEY (registry_id) REFERENCES Facilities (registry_id),
                FOREIGN KEY (program_identifier, program_full_name) REFERENCES Programs (program_identifier, program_full_name)
            )
        ''')
        # Table JobTitles
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS JobTitles (
                job_title TEXT PRIMARY KEY,
                department TEXT
            )
        ''')
        # Table Employees
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Employees (
                id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                gender TEXT,
                age INTEGER,
                job_title TEXT,
                years_of_experience INTEGER,
                salary REAL,
                FOREIGN KEY (job_title) REFERENCES JobTitles(job_title)
            )
        ''')
        self.conn.commit()

        # Create Views

        # View FacilitiesByState
        self.cursor.execute('''
            CREATE VIEW IF NOT EXISTS FacilitiesByState AS
            SELECT 
                l.location_address_state_code AS State,
                COUNT(f.registry_id) AS FacilityCount
            FROM Locations l
            JOIN Facilities f ON l.registry_id = f.registry_id
            WHERE l.location_address_state_code IS NOT NULL
            GROUP BY l.location_address_state_code
            ORDER BY FacilityCount DESC
        ''')
        # View View_AvgSalaryByJob
        self.cursor.execute('''
            CREATE VIEW IF NOT EXISTS View_AvgSalaryByJob AS
            SELECT job_title,
                   AVG(salary) AS avg_salary,
                   COUNT(*) AS employee_count
            FROM Employees
            GROUP BY job_title
        ''')
        # View CountProgramsByInterestType
        self.cursor.execute('''
            CREATE VIEW IF NOT EXISTS CountProgramsByInterestType AS
            SELECT 
                interest_type_id,
                COUNT(program_identifier) AS ProgramCount
            FROM Programs 
     
            GROUP BY interest_type_id
            ORDER BY ProgramCount DESC
        ''')
        self.conn.commit()

    def upload_xml(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open XML", "", "XML Files (*.xml)")
        if not file_path:
            return
        try:
            program_interest_types = {}
            facilities = []
            coordinates = []
            locations = []
            programs = []
            program_attributes = []
            facility_programs = []
            processed_programs = {}
            parser = ET.XMLParser(encoding='utf-8')
            tree = ET.parse(file_path, parser=parser)
            root = tree.getroot()
            facility_sites = root.findall('.//FacilitySite')
            logging.debug(f"Found {len(facility_sites)} FacilitySite elements")
            for facility in facility_sites:
                try:
                    registry_id = facility.get('registryId')
                    if not registry_id:
                        logging.error("Missing facility_id (registryId) in XML record.")
                        continue
                    logging.debug(f"Processing facility with registryId={registry_id}")
                    lat_text = facility.find('LatitudeMeasure').text if facility.find('LatitudeMeasure') is not None else None
                    lon_text = facility.find('LongitudeMeasure').text if facility.find('LongitudeMeasure') is not None else None
                    if lat_text and not is_number(lat_text, allow_float=True):
                        logging.error(f"Invalid latitude for registryId={registry_id}")
                        continue
                    if lon_text and not is_number(lon_text, allow_float=True):
                        logging.error(f"Invalid longitude for registryId={registry_id}")
                        continue
                    facility_addr = facility.find('GeneralProfileElectronicAddress')
                    electronicfacility_text = facility_addr.find('ElectronicAddressText').text if facility_addr is not None and facility_addr.find('ElectronicAddressText') is not None else None
                    electronicfacility_type = facility_addr.find('ElectronicAddressTypeName').text if facility_addr is not None and facility_addr.find('ElectronicAddressTypeName') is not None else None
                    facilities.append((registry_id, facility.find('FacilitySiteName').text if facility.find('FacilitySiteName') is not None else None, facility.find('LocationAddressText').text if facility.find('LocationAddressText') is not None else None, electronicfacility_text, electronicfacility_type))
                    coordinates.append((registry_id, float(lat_text) if lat_text else None, float(lon_text) if lon_text else None, facility.find('HorizontalCoordinateReferenceSystemDatumName').text if facility.find('HorizontalCoordinateReferenceSystemDatumName') is not None else None, facility.find('HorizontalCollectionMethodName').text if facility.find('HorizontalCollectionMethodName') is not None else None))
                    locations.append((registry_id, facility.find('LocationZIPCode').text if facility.find('LocationZIPCode') is not None else None, facility.find('LocalityName').text if facility.find('LocalityName') is not None else None, facility.find('LocationAddressStateCode').text if facility.find('LocationAddressStateCode') is not None else None))
                    program = facility.find('Program' )
                    if program is not None:
                        program_identifier = program.find('ProgramIdentifier').text if program.find('ProgramIdentifier' ) is not None else None
                        if program_identifier is None:
                            logging.error(f"Missing program_identifier for registryId={registry_id}")
                            continue
                        program_full_name = program.find('ProgramFullName' ).text if program.find('ProgramFullName' ) is not None else None
                        program_key = (program_identifier, program_full_name)
                        if program_key not in processed_programs:
                            program_interest = program.find('ProgramInterestType' )
                            interest_type_id = None
                            if program_interest is not None and program_interest.text:
                                if program_interest.text not in program_interest_types:
                                    program_interest_types[program_interest.text] = program_interest.text
                                interest_type_id = program_interest_types[program_interest.text]
                            programs.append((program_identifier, program_full_name, interest_type_id))
                            profile_addr = program.find('ProgramProfileElectronicAddress' )
                            electronic_text = profile_addr.find('ElectronicAddressText' ).text if profile_addr is not None and profile_addr.find('ElectronicAddressText' ) is not None else None
                            electronic_type = profile_addr.find('ElectronicAddressTypeName' ).text if profile_addr is not None and profile_addr.find('ElectronicAddressTypeName' ) is not None else None
                            program_attributes.append((interest_type_id, program.find('ProgramCommonName' ).text if program.find('ProgramCommonName' ) is not None else None, program.find('ProgramAcronymName' ).text if program.find('ProgramAcronymName' ) is not None else None, program.find('ProgramDescription' ).text if program.find('ProgramDescription' ) is not None else None, electronic_text, electronic_type))
                            processed_programs[program_key] = None
                        facility_programs.append((registry_id, program_identifier, program_full_name))
                except Exception as e:
                    logging.error(f"Error processing facility registryId={registry_id}: {str(e)}")
                    continue
            logging.debug(f"Facilities to insert: {len(facilities)}")
            logging.debug(f"Coordinates to insert: {len(coordinates)}")
            logging.debug(f"Locations to insert: {len(locations)}")
            logging.debug(f"Programs to insert: {len(programs)}")
            logging.debug(f"ProgramAttributes to insert: {len(program_attributes)}")
            logging.debug(f"FacilityPrograms to insert: {len(facility_programs)}")
            try:
                # self.cursor.execute('BEGIN TRANSACTION')
                self.cursor.executemany("INSERT OR IGNORE INTO Facilities (registry_id, facility_site_name, location_address_text, electronic_address, electronic_address_typename) VALUES (?, ?, ?, ?, ?)", facilities)
                self.cursor.executemany("INSERT OR IGNORE INTO Coordinates (registry_id, latitude_measure, longitude_measure, horizontal_coordinate_reference_system_datum_name, horizontal_collection_method_name) VALUES (?, ?, ?, ?, ?)", coordinates)
                self.cursor.executemany("INSERT OR IGNORE INTO Locations (registry_id, location_zip_code, locality_name, location_address_state_code) VALUES (?, ?, ?, ?)", locations)
                self.cursor.executemany("INSERT OR IGNORE INTO Programs (program_identifier, program_full_name, interest_type_id) VALUES (?, ?, ?)", programs)
                self.cursor.executemany("INSERT OR IGNORE INTO ProgramAttributes (interest_type_id, program_common_name, program_acronym_name, program_description, electronic_address, electronic_address_typename) VALUES (?, ?, ?, ?, ?, ?)", program_attributes)
                self.cursor.executemany("INSERT OR IGNORE INTO FacilityPrograms (registry_id, program_identifier, program_full_name) VALUES (?, ?, ?)", facility_programs)
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Database error occurred: {e}")
                # self.conn.rollback()
            except Exception as e:
                print(f"An error occurred: {e}")
                # self.conn.rollback()
            QMessageBox.information(self, "Success", "XML file processed successfully!", QMessageBox.Icon.Information)
        except Exception as e:
            logging.error(f"Error processing XML: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error processing XML: {str(e)}", QMessageBox.Icon.Critical)

    def upload_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            job_titles = set()
            employees = []
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for employee in data:
                try:
                    emp_id = employee.get('id')
                    if emp_id is None:
                        logging.error("Missing id in JSON record.")
                        continue
                    if not is_number(employee.get('age'), allow_float=False):
                        logging.error(f"Invalid age for employee id={emp_id}")
                        continue
                    if not is_number(employee.get('salary'), allow_float=True):
                        logging.error(f"Invalid salary for employee id={emp_id}")
                        continue
                    job_titles.add((employee['job_title'], employee['department']))
                    employees.append((
                        employee['id'],
                        employee['first_name'],
                        employee['last_name'],
                        employee['email'],
                        employee['phone'],
                        employee['gender'],
                        int(employee.get('age')),
                        employee['job_title'],
                        employee['years_of_experience'],
                        float(employee.get('salary'))
                    ))
                except KeyError as e:
                    logging.error(f"Missing key {e} in JSON employee record with id={employee.get('id')}")
                    continue
            try:
                self.cursor.execute('BEGIN TRANSACTION')
                self.cursor.executemany("INSERT OR IGNORE INTO JobTitles (job_title, department) VALUES (?, ?)", list(job_titles))
                self.cursor.executemany("INSERT OR IGNORE INTO Employees (id, first_name, last_name, email, phone, gender, age, job_title, years_of_experience, salary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", employees)
                self.conn.commit()
                QMessageBox.information(self, "Success", "JSON file processed successfully!", QMessageBox.Icon.Information)
            except sqlite3.Error as e:
                print(f"Database error occurred: {e}")
                self.conn.rollback()
            except Exception as e:
                print(f"An error occurred: {e}")
                self.conn.rollback()
        except Exception as e:
            logging.error(f"Error processing JSON: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error processing JSON: {str(e)}", QMessageBox.Icon.Critical)

    def show_view(self, view_name, columns):
        try:
            self.cursor.execute(f"SELECT * FROM {view_name}")
            rows = self.cursor.fetchall()

            dialog = QDialog(self)
            dialog.setWindowTitle(view_name)
            dialog.resize(700, 500)

            layout = QVBoxLayout()
            table = QTableWidget()
            table.setRowCount(len(rows))
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)
            table.horizontalHeader().setStretchLastSection(True)
            table.setStyleSheet("QTableWidget { border: 1px solid #ccc; }")

            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(i, j, item)

            layout.addWidget(table)
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Icon.Critical)

    def run_sql_query(self):
        query = self.sql_entry.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a SQL query.", QMessageBox.StandardButton.Ok)
            return

        try:
            first_word = query.split()[0].upper()
            rows, columns = [], []

            if first_word == "INSERT":
                self.cursor.execute("BEGIN TRANSACTION")
                self.cursor.execute(query)
                self.conn.commit()
                QMessageBox.information(self, "Success", "Insert done successfully.", QMessageBox.StandardButton.Ok)

            elif first_word == "UPDATE":
                self.cursor.execute("BEGIN TRANSACTION")
                self.cursor.execute(query)
                self.conn.commit()
                QMessageBox.information(self, "Success", "Update done successfully.", QMessageBox.StandardButton.Ok)
            
            elif first_word == "DELETE":
                self.cursor.execute("BEGIN TRANSACTION")
                self.cursor.execute(query)
                self.conn.commit()
                QMessageBox.information(self, "Success", "Delete done successfully.", QMessageBox.StandardButton.Ok)
                
            else:
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
                

            if rows and columns:
                dialog = QDialog(self)
                dialog.setWindowTitle("SQL Query Result")
                dialog.resize(700, 500)

                layout = QVBoxLayout()
                table = QTableWidget()
                table.setRowCount(len(rows))
                table.setColumnCount(len(columns))
                table.setHorizontalHeaderLabels(columns)
                table.horizontalHeader().setStretchLastSection(True)
                table.setStyleSheet("QTableWidget { border: 1px solid #ccc; }")

                for i, row in enumerate(rows):
                    for j, val in enumerate(row):
                        item = QTableWidgetItem(str(val))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        table.setItem(i, j, item)

                layout.addWidget(table)
                dialog.setLayout(layout)
                dialog.exec()

        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error", f"Error executing query: {e}", QMessageBox.StandardButton.Ok)

    def plot_facilities_per_state(self):
        self.cursor.execute("SELECT State, FacilityCount FROM FacilitiesByState")
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available for Facilities per State.")
            return
        states, counts = zip(*data)

        canvas = MplCanvas(self, width=8, height=4)
        canvas.axes.bar(states, counts)
        canvas.axes.set_title("Facilities per State")
        canvas.axes.set_ylabel("Count")
        canvas.axes.set_xticks(range(len(states)))
        canvas.axes.set_xticklabels(states, rotation=90, ha='center' , fontsize=8)
        canvas.fig.tight_layout()
        canvas.fig.savefig("facilities_per_state.png", bbox_inches='tight')
        self.show_plot_dialog(canvas, "Facilities per State")

    def plot_employee_dept_pie(self):
        self.cursor.execute("SELECT department, COUNT(*) FROM Employees e JOIN JobTitles j ON e.job_title = j.job_title GROUP BY department")
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available for Employee Dept Distribution.")
            return
        depts, counts = zip(*data)

        canvas = MplCanvas(self, width=5, height=4)
        canvas.axes.pie(counts, labels=depts, autopct='%1.1f%%')
        canvas.axes.set_title("Employee Dept Distribution")
        canvas.fig.savefig("employee_dept_distribution.png", bbox_inches='tight')
        self.show_plot_dialog(canvas, "Employee Dept Distribution")
    
    def plot_employee_job_pie(self):
        self.cursor.execute("SELECT job_title, COUNT(*) FROM Employees GROUP BY job_title")
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available for Employee Dept Distribution.")
            return
        jobs, counts = zip(*data)

        canvas = MplCanvas(self, width=5, height=4)
        canvas.axes.pie(counts, labels=jobs, autopct='%1.1f%%')
        canvas.axes.set_title("Employee job Distribution")
        canvas.fig.savefig("employee_job_distribution.png", bbox_inches='tight')
        self.show_plot_dialog(canvas, "Employee job Distribution")

    def plot_age_histogram(self):
        self.cursor.execute("SELECT age FROM Employees WHERE age IS NOT NULL")
        ages = [row[0] for row in self.cursor.fetchall()]
        if not ages:
            QMessageBox.warning(self, "No Data", "No data available for Age Distribution.")
            return

        canvas = MplCanvas(self, width=6, height=4)
        canvas.axes.hist(ages, bins=10, edgecolor='black')
        canvas.axes.set_title("Age Distribution of Employees")
        canvas.axes.set_xlabel("Age")
        canvas.axes.set_ylabel("Frequency")
        canvas.fig.savefig("age_distribution.png", bbox_inches='tight')
        self.show_plot_dialog(canvas, "Age Distribution")

    def plot_salary_vs_exp_line(self):
        self.cursor.execute("SELECT years_of_experience, AVG(salary) FROM Employees WHERE years_of_experience IS NOT NULL AND salary IS NOT NULL group by years_of_experience")
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available for Salary vs Experience.")
            return
        years, salaries = zip(*data)

        canvas = MplCanvas(self, width=6, height=4)
        canvas.axes.plot(years, salaries, marker='o')
        canvas.axes.set_title("Salary vs Years of Experience")
        canvas.axes.set_xlabel("Years of Experience")
        canvas.axes.set_ylabel("Salary")
        canvas.fig.savefig("salary_vs_experience.png", bbox_inches='tight')
        self.show_plot_dialog(canvas, "Salary vs Experience (Line)")
        
    def plot_avg_salary_by_job(self):
        self.cursor.execute("SELECT job_title, avg_salary FROM View_AvgSalaryByJob")
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available for Average Salary by Job.")
            return
        jobs, avg_salaries = zip(*data)

        canvas = MplCanvas(self, width=5, height=4)
        canvas.axes.barh(jobs, avg_salaries)
        canvas.axes.set_yticks(range(len(jobs)))
        canvas.axes.set_yticklabels(jobs, rotation=45 , fontsize=7)
        canvas.fig.tight_layout() 
        canvas.axes.set_title("Average Salary by Job Title")
        canvas.axes.set_xlabel("Salary")

        self.show_plot_dialog(canvas, "Avg Salary by Job")

    def plot_gender_distribution(self):
        self.cursor.execute("SELECT gender, COUNT(*) FROM Employees GROUP BY gender")
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available for Gender Distribution.")
            return
        labels, values = zip(*data)

        canvas = MplCanvas(self, width=5, height=4)
        canvas.axes.pie(values, labels=labels, autopct='%1.1f%%')
        canvas.axes.set_title("Employees by Gender")

        self.show_plot_dialog(canvas, "Employees by Gender")


    def plot_programs_by_interest(self):
        self.cursor.execute("SELECT interest_type_id, COUNT(*) FROM Programs GROUP BY interest_type_id")
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No data available for Programs by InterestType.")
            return
        interests, counts = zip(*data)

        canvas = MplCanvas(self, width=6, height=4)
        canvas.axes.bar(interests, counts)
        canvas.axes.set_title("Programs by InterestType")
        canvas.axes.set_ylabel("Count")
        canvas.axes.set_xticks(range(len(interests)))
        canvas.axes.set_xticklabels(interests, rotation=45, ha='center' , fontsize=8)
        canvas.fig.tight_layout() 
        
        self.show_plot_dialog(canvas, "Programs by InterestType")

    def plot_avg_experience_by_department(self):
        self.cursor.execute("""
            SELECT j.department, AVG(e.years_of_experience)
            FROM Employees e
            JOIN JobTitles j ON e.job_title = j.job_title
            GROUP BY j.department
        """)
        rows = self.cursor.fetchall()
        if not rows:
            QMessageBox.information(self, "No Data", "No department data found.")
            return

        depts, avgs = zip(*rows)

        canvas = MplCanvas(self, width=6, height=4)
        canvas.axes.bar(depts, avgs)
        canvas.axes.set_title("Avg Experience by Department")
        canvas.axes.set_ylabel("Years of Experience")

        self.show_plot_dialog(canvas, "Avg Experience by Department")

    def show_plot_dialog(self, canvas, title):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidget(canvas)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        dialog.setLayout(layout)
        dialog.resize(700, 500)
        dialog.exec()
    
    def plot_facilities_scatter(self):
        self.cursor.execute("""
            SELECT c.registry_id, c.latitude_measure, c.longitude_measure, f.facility_site_name
            FROM Coordinates c
            JOIN Facilities f ON c.registry_id = f.registry_id
            WHERE c.latitude_measure IS NOT NULL AND c.longitude_measure IS NOT NULL
        """)
        data = self.cursor.fetchall()
        if not data:
            QMessageBox.warning(self, "No Data", "No valid coordinate data available for Facilities.")
            return
        
       
        lats = [row[1] for row in data]
        lons = [row[2] for row in data]
        
        canvas = MplCanvas(self, width=8, height=6)
        canvas.axes.scatter(lons, lats, color='blue')
        
        
        canvas.axes.set_title("Facilities on Scatter Plot")
        canvas.axes.set_xlabel("Longitude")
        canvas.axes.set_ylabel("Latitude")
        canvas.axes.grid(True)
        canvas.fig.tight_layout()
        canvas.fig.savefig("facilities_scatter.png", bbox_inches='tight')
        self.show_plot_dialog(canvas, "Facilities on Scatter Plot")

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec())