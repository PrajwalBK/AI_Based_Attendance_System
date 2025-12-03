import mysql.connector
from mysql.connector import errorcode
import pickle
import base64
from datetime import datetime, date
from config.config import MYSQL_CONFIG

class DatabaseManager:
    def __init__(self):
        self.config = MYSQL_CONFIG
        self.init_database()
    
    def get_connection(self):
        """Helper to get a fresh connection"""
        return mysql.connector.connect(**self.config)

    def init_database(self):
        """Initialize MySQL tables"""
        try:
            # 1. Create Database if not exists
            self.create_database_if_not_exists()

            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. Persons Table (With Shift Columns)
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS persons (
                        person_id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100),
                        department VARCHAR(100),
                        shift_start VARCHAR(10) DEFAULT '09:00',
                        shift_end VARCHAR(10) DEFAULT '18:00',
                        registered_date VARCHAR(30) NOT NULL,
                        face_encoding LONGTEXT
                    )
                ''')
                print("Table 'persons' checked/created.")
            except mysql.connector.Error as err:
                print(f"Error creating 'persons' table: {err}")
            
            # 2. Attendance Summary
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attendance (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        person_id VARCHAR(50) NOT NULL,
                        date VARCHAR(20) NOT NULL,
                        arrival_time VARCHAR(20),
                        leaving_time VARCHAR(20),
                        status VARCHAR(20) DEFAULT 'Present',
                        FOREIGN KEY (person_id) REFERENCES persons (person_id) ON DELETE CASCADE,
                        UNIQUE KEY unique_attendance (person_id, date)
                    )
                ''')
                print("Table 'attendance' checked/created.")
            except mysql.connector.Error as err:
                print(f"Error creating 'attendance' table: {err}")

            # 3. Raw Logs (With Name Column)
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS face_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        person_id VARCHAR(50),
                        name VARCHAR(100),
                        date VARCHAR(20),
                        time VARCHAR(20),
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
                    )
                ''')
                print("Table 'face_logs' checked/created.")
            except mysql.connector.Error as err:
                print(f"Error creating 'face_logs' table: {err}")

            # 4. Unknown Faces Table
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS unknown_faces (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        snapshot_path VARCHAR(255),
                        face_encoding LONGTEXT
                    )
                ''')
                print("Table 'unknown_faces' checked/created.")
            except mysql.connector.Error as err:
                print(f"Error creating 'unknown_faces' table: {err}")
            
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")

    def create_database_if_not_exists(self):
        """Creates the database if it doesn't exist"""
        db_name = self.config.get('database')
        if not db_name: return

        # Connect without database
        temp_config = self.config.copy()
        if 'database' in temp_config:
            del temp_config['database']
        
        try:
            conn = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Database '{db_name}' checked/created successfully.")
        except mysql.connector.Error as err:
            print(f"Error creating database: {err}")

    # --- CORE LOGGING & ATTENDANCE ---

    def log_raw_detection(self, person_id, person_name):
        """Logs detection with Name, Date and Time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            current_date = now.strftime('%Y-%m-%d')
            current_time = now.strftime('%H:%M:%S')
            
            cursor.execute('''
                INSERT INTO face_logs (person_id, name, date, time, timestamp) 
                VALUES (%s, %s, %s, %s, NOW())
            ''', (person_id, person_name, current_date, current_time))
            
            conn.commit()
        except Exception as e:
            print(f"Log Error: {e}")
        finally:
            conn.close()

    def log_unknown_person(self, snapshot_path, face_encoding):
        """Logs unknown person with snapshot and encoding"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            pickled_data = pickle.dumps(face_encoding)
            safe_data_string = base64.b64encode(pickled_data).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO unknown_faces (snapshot_path, face_encoding) 
                VALUES (%s, %s)
            ''', (snapshot_path, safe_data_string))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Log Unknown Error: {e}")
            return False
        finally:
            conn.close()

    def sync_daily_attendance(self, person_id):
        """
        Manages Attendance based on PERSON-SPECIFIC Shift:
        1. Get the person's shift_end from DB.
        2. If current time >= shift_end, update Logout.
        """
        today = date.today().isoformat()
        now = datetime.now()
        current_time = now.strftime('%H:%M:%S')
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Get Person's Shift Details
            cursor.execute('SELECT shift_end FROM persons WHERE person_id = %s', (person_id,))
            person_data = cursor.fetchone()
            
            if not person_data:
                return "Error: Person not found"
                
            # Parse user's specific shift end (e.g., "18:00")
            user_shift_end_str = person_data[0] 
            try:
                user_shift_end_hour = int(user_shift_end_str.split(':')[0])
            except:
                user_shift_end_hour = 18 # Default fallback
            
            # 2. Check Attendance Record
            cursor.execute('SELECT id FROM attendance WHERE person_id = %s AND date = %s', (person_id, today))
            record = cursor.fetchone()
            
            if record is None:
                # --- LOGIN ---
                cursor.execute('''
                    INSERT INTO attendance (person_id, date, arrival_time, leaving_time, status)
                    VALUES (%s, %s, %s, %s, 'Present')
                ''', (person_id, today, current_time, current_time))
                conn.commit()
                return f"LOGIN: {current_time}"
            else:
                # --- UPDATE LEAVING TIME (Always update to latest seen) ---
                cursor.execute('''
                    UPDATE attendance 
                    SET leaving_time = %s 
                    WHERE person_id = %s AND date = %s
                ''', (current_time, person_id, today))
                conn.commit()
                
                # Check if shift is over for voice feedback
                if now.hour >= user_shift_end_hour:
                    return f"LOGOUT UPDATE: {current_time}"
                else:
                    return f"Shift Ongoing (Ends {user_shift_end_str})"
                
        except mysql.connector.Error as err:
            return f"DB Error: {err}"
        finally:
            conn.close()

    # --- PERSON MANAGEMENT ---

    def add_person(self, person_id, name, face_encoding, email=None, department=None, shift_start="09:00", shift_end="18:00"):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            pickled_data = pickle.dumps(face_encoding)
            safe_data_string = base64.b64encode(pickled_data).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO persons (person_id, name, email, department, shift_start, shift_end, registered_date, face_encoding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (person_id, name, email, department, shift_start, shift_end, datetime.now().isoformat(), safe_data_string))
            
            conn.commit()
            return True, "Person added successfully"
        except mysql.connector.IntegrityError:
            return False, "Person ID already exists"
        except Exception as e:
            return False, str(e)
        finally:
            if conn.is_connected(): conn.close()

    def update_person(self, person_id, name, email, dept, s_start, s_end):
        """Update a person's details"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE persons 
                SET name=%s, email=%s, department=%s, shift_start=%s, shift_end=%s
                WHERE person_id=%s
            ''', (name, email, dept, s_start, s_end, person_id))
            conn.commit()
            return True, "Update Successful"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def delete_person(self, person_id):
        """Delete a person and their logs"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM persons WHERE person_id=%s', (person_id,))
            conn.commit()
            return True, "Deleted Successfully"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    # --- STATS & REPORTS (This was missing!) ---

    def get_person_stats(self, person_id):
        """
        Calculate detailed stats: Late In, Early Out, Avg Hours
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Get Person Details (Shift info)
        cursor.execute('SELECT name, shift_start, shift_end FROM persons WHERE person_id = %s', (person_id,))
        person = cursor.fetchone()
        
        if not person:
            conn.close()
            return None, "Person not found"
            
        name, s_start_str, s_end_str = person
        
        # 2. Get All Attendance Records for this person
        cursor.execute('SELECT arrival_time, leaving_time FROM attendance WHERE person_id = %s', (person_id,))
        records = cursor.fetchall()
        conn.close()
        
        # 3. Calculate Stats
        total_days = len(records)
        late_count = 0
        early_out_count = 0
        total_seconds_worked = 0
        days_with_full_data = 0
        
        def parse_time(t_str, fmt='%H:%M:%S'):
            try: return datetime.strptime(t_str, fmt)
            except: return None
            
        try:
            shift_start_dt = datetime.strptime(s_start_str, '%H:%M')
            shift_end_dt = datetime.strptime(s_end_str, '%H:%M')
        except:
            return None, "Error parsing shift times in DB"

        for arrival, leaving in records:
            # Check Late
            if arrival:
                arr_dt = parse_time(arrival)
                if arr_dt and arr_dt.time() > shift_start_dt.time():
                    late_count += 1
            
            # Check Early Out & Avg Hours
            if leaving:
                leave_dt = parse_time(leaving)
                if leave_dt:
                    if leave_dt.time() < shift_end_dt.time():
                        early_out_count += 1
                    
                    if arrival:
                        arr_dt = parse_time(arrival)
                        if arr_dt:
                            duration = (leave_dt - arr_dt).total_seconds()
                            if duration > 0:
                                total_seconds_worked += duration
                                days_with_full_data += 1

        avg_hours = 0
        if days_with_full_data > 0:
            avg_hours = (total_seconds_worked / days_with_full_data) / 3600 

        return {
            'name': name,
            'id': person_id,
            'shift': f"{s_start_str} - {s_end_str}",
            'total_days': total_days,
            'late': late_count,
            'early': early_out_count,
            'avg_hours': round(avg_hours, 1)
        }, "Success"

    # --- DATA FETCHING ---

    def get_statistics(self):
        today = date.today().isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM persons')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = %s', (today,))
        present = cursor.fetchone()[0]
        conn.close()
        return {'total_persons': total, 'present_today': present}

    def get_today_attendance(self):
        today = date.today().isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.person_id, p.name, a.arrival_time, a.leaving_time, a.status
            FROM attendance a JOIN persons p ON a.person_id = p.person_id
            WHERE a.date = %s ORDER BY a.arrival_time DESC
        ''', (today,))
        records = cursor.fetchall()
        conn.close()
        return records
    
    def get_recent_logs(self):
        """Fetch the detailed raw logs (Last 100 records)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT person_id, name, date, time 
            FROM face_logs 
            ORDER BY id DESC LIMIT 100
        ''')
        records = cursor.fetchall()
        conn.close()
        return records
    
    def get_all_persons_details(self):
        """Fetch all details for the Edit View"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT person_id, name, email, department, shift_start, shift_end 
            FROM persons
        ''')
        records = cursor.fetchall()
        conn.close()
        return records

    def export_to_csv(self, filename):
        import csv
        records = self.get_today_attendance()
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Login Time', 'Last Seen (Logout)', 'Status'])
                writer.writerows(records)
            return True, f"Exported to {filename}"
        except Exception as e:
            return False, str(e)

    def get_attendance_report(self, start_date, end_date, person_id=None):
        """
        Fetch attendance records for a specific date range.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT a.date, p.name, a.person_id, a.arrival_time, a.leaving_time, a.status
            FROM attendance a 
            JOIN persons p ON a.person_id = p.person_id
            WHERE a.date BETWEEN %s AND %s
        '''
        params = [start_date, end_date]
        
        if person_id and person_id != "All":
            query += ' AND a.person_id = %s'
            params.append(person_id)
            
        query += ' ORDER BY a.date DESC, a.arrival_time DESC'
        
        cursor.execute(query, tuple(params))
        records = cursor.fetchall()
        conn.close()
        return records

    def export_to_pdf(self, data, filename, title="Attendance Report"):
        """
        Generate a PDF report using ReportLab.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            doc = SimpleDocTemplate(filename, pagesize=letter)
            elements = []
            
            styles = getSampleStyleSheet()
            elements.append(Paragraph(title, styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Table Header
            table_data = [['Date', 'Name', 'ID', 'Arrival', 'Leaving', 'Status']]
            
            # Table Data
            for row in data:
                # Ensure all items are strings
                table_data.append([str(item) if item is not None else "" for item in row])
                
            # Create Table
            t = Table(table_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(t)
            doc.build(elements)
            return True, f"PDF Exported: {filename}"
        except ImportError:
            return False, "ReportLab not installed. Cannot generate PDF."
        except Exception as e:
            return False, str(e)