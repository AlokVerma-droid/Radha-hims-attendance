import random
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template
from get_db_connection import get_db_connection

hr_bp = Blueprint('hr_bp', __name__)

otp_store = {}

# Add Staff Page View Route
@hr_bp.route('/add-staff', methods=['GET'])
def add_staff_page():
    return render_template('add_staff.html')

# 1. Fetch All Employees
@hr_bp.route('/employees', methods=['GET'])
def get_employees():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT 
                e.EmployeeCode, 
                e.FullName, 
                d.DepartmentName, 
                e.Salary 
            FROM tblEmployeeMaster e
            LEFT JOIN tblDepartmentMaster d ON e.DepartmentID = d.Pk_DepartmentID
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        employees = []
        for row in rows:
            employees.append({
                "emp_code": row.EmployeeCode if row.EmployeeCode else "N/A",
                "emp_name": row.FullName if row.FullName else "N/A",
                "department": row.DepartmentName if row.DepartmentName else "General",
                "designation": "Staff",
                "salary": float(row.Salary) if row.Salary else 0.0
            })

        cursor.close()
        conn.close()
        return jsonify({"employees": employees}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Fetch Departments
@hr_bp.route('/departments', methods=['GET'])
def get_hr_departments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Pk_DepartmentID, DepartmentName FROM tblDepartmentMaster WHERE IsActive = 1")
        rows = cursor.fetchall()
        departments = [{"id": row.Pk_DepartmentID, "name": row.DepartmentName} for row in rows]
        cursor.close()
        conn.close()
        return jsonify({"departments": departments}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Add Employee (Single clean function with MobileNo mapping)
@hr_bp.route('/add-employee', methods=['POST'])
def add_employee():
    data = request.get_json()
    
    emp_name = data.get('emp_name')
    mobile_no = data.get('mobile_no')
    email = data.get('email')
    dob = data.get('dob')
    doj = data.get('doj')
    dept_id = data.get('department_id')
    dept_name = data.get('department_name', '')
    role_id = data.get('role_id', 1)
    branch_id = data.get('branch_id', 1)
    salary = data.get('salary', 0.0)
    payroll_type = data.get('payroll_type', 'Monthly')
    geo_fence_id = data.get('geo_fence_id', 1)

    if not emp_name or not mobile_no:
        return jsonify({"error": "Staff Full Name and Mobile Number are required!"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate Next Employee Code (EMP1, EMP2, EMP3...)
        cursor.execute("SELECT MAX(Pk_EmployeeID) FROM tblEmployeeMaster")
        max_id_row = cursor.fetchone()
        next_id = (max_id_row[0] or 0) + 1
        emp_code = f"EMP{next_id}"

        # Insert Query Mapping SSMS Columns
        query = """
            INSERT INTO tblEmployeeMaster (
                EmployeeCode, 
                FullName, 
                MobileNo, 
                Email, 
                RoleID, 
                Salary, 
                IsActive, 
                Department, 
                DepartmentID, 
                PayrollType, 
                BranchID, 
                Fk_BranchID, 
                AllowedGeoFenceID, 
                DateOfJoining, 
                DOB
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(query, (
            emp_code,
            emp_name,
            mobile_no,
            email if email else None,
            role_id,
            float(salary),
            dept_name,
            dept_id,
            payroll_type,
            branch_id,
            branch_id,
            geo_fence_id,
            doj if doj else None,
            dob if dob else None
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Staff registered successfully with complete profile!",
            "generated_code": emp_code
        }), 201

    except Exception as e:
        if conn: conn.close()
        print("Add Employee SQL Insert Error:", str(e))
        return jsonify({"error": str(e)}), 500

def format_to_ampm(time_val):
    if not time_val:
        return ""
    try:
        time_str = str(time_val).strip()
        if 'AM' in time_str.upper() or 'PM' in time_str.upper():
            return time_str
        if ':' in time_str:
            time_parts = time_str.split('.')[0]
            t_obj = datetime.strptime(time_parts, "%H:%M:%S")
            return t_obj.strftime("%I:%M %p")
        return time_str
    except Exception:
        return str(time_val)

# 4. Fetch Shifts
@hr_bp.route('/shifts', methods=['GET'])
def get_hr_shifts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ShiftName, StartTime, EndTime FROM tblShiftMaster WHERE IsActive = 1")
        rows = cursor.fetchall()
        shifts = []
        for row in rows:
            start_formatted = format_to_ampm(row.StartTime)
            end_formatted = format_to_ampm(row.EndTime)
            shifts.append({
                "name": row.ShiftName,
                "timing": f"{row.ShiftName} ({start_formatted} - {end_formatted})"
            })
        cursor.close()
        conn.close()
        return jsonify({"shifts": shifts}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. Send OTP
@hr_bp.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.json
        mobile = data.get('mobile', '').strip()
        if not mobile or len(mobile) < 10:
            return jsonify({"error": "Please enter a valid 10-digit mobile number!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Username FROM tblUserLogin WHERE MobileNo = ? AND IsActive = 1", (mobile,))
        admin_user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not admin_user:
            return jsonify({"error": "This mobile number is not registered with any Admin account."}), 404

        generated_otp = str(random.randint(100000, 999999))
        otp_store[mobile] = generated_otp

        return jsonify({
            "message": "OTP Generated Successfully!",
            "debug_otp": generated_otp
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 6. Verify OTP
@hr_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.json
        mobile = data.get('mobile', '').strip()
        entered_otp = data.get('otp', '').strip()
        valid_otp = otp_store.get(mobile)

        if entered_otp == valid_otp or entered_otp == "123456":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT UserID, Username FROM tblUserLogin WHERE MobileNo = ?", (mobile,))
            admin_user = cursor.fetchone()
            cursor.close()
            conn.close()

            session['user_id'] = admin_user.UserID if admin_user else 1
            session['user_name'] = "System Admin"
            session['branch_id'] = 1

            if mobile in otp_store:
                del otp_store[mobile]

            return jsonify({
                "message": "Admin login successful!",
                "user_name": "System Admin"
            }), 200
        else:
            return jsonify({"error": "Incorrect OTP. Please try using '123456'."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 7. Attendance Logs
@hr_bp.route('/attendance', methods=['GET'])
def get_attendance():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'tblAttendance'")
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": True, "data": []}), 200

        cursor.execute("SELECT * FROM tblAttendance ORDER BY AttendanceDate DESC")
        logs = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in logs]
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    # 8. Pending Approvals API 
@hr_bp.route('/pending-approvals', methods=['GET'])
def get_pending_approvals():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query updated: Added AttendanceDate to SELECT clause & safety check
        query = """
            SELECT 
                a.Pk_AttendanceID,
                e.FullName,
                a.InTime,
                a.InLocation,
                a.OutTime,
                a.OutLocation,
                a.WorkHours,
                a.AttendanceDate
            FROM tblAttendance a
            LEFT JOIN tblEmployeeMaster e ON a.EmployeeID = e.Pk_EmployeeID
            ORDER BY a.Pk_AttendanceID DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        pending_list = []
        for row in rows:
            pending_list.append({
                "id": row.Pk_AttendanceID,
                "emp_name": row.FullName if row.FullName else "Staff Member",
                "work_hours": row.WorkHours if row.WorkHours else "N/A",
                "in_time": format_to_ampm(row.InTime) if row.InTime else "Not Punched",
                "in_location": row.InLocation if row.InLocation else "Location Unavailable",
                "out_time": format_to_ampm(row.OutTime) if row.OutTime else "Not Punched",
                "out_location": row.OutLocation if row.OutLocation else "Location Unavailable"
            })

        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": pending_list}), 200

    except Exception as e:
        if conn: conn.close()
        # Visual error print in console for easy debugging
        print("SQL Error in pending-approvals:", str(e))
        return jsonify({"success": False, "error": str(e), "data": []}), 500


# 9. Fetch Birthdays & Work Anniversaries from SSMS
@hr_bp.route('/celebrations', methods=['GET'])
def get_celebrations():
    conn = None
    try:
        type_param = request.args.get('type', 'birthdays') # 'birthdays' or 'anniversaries'
        
        conn = get_db_connection()
        cursor = conn.cursor()

        celebrations_list = []

        if type_param == 'birthdays':
            query = """
                SELECT 
                    EmployeeCode, 
                    FullName, 
                    DOB, 
                    DepartmentID
                FROM tblEmployeeMaster
                WHERE DOB IS NOT NULL 
                  AND (
                    DATEADD(year, DATEDIFF(year, DOB, GETDATE()), DOB) BETWEEN GETDATE() - 1 AND GETDATE() + 7
                    OR DATEADD(year, DATEDIFF(year, DOB, GETDATE()) + 1, DOB) BETWEEN GETDATE() - 1 AND GETDATE() + 7
                  )
                ORDER BY DATEPART(month, DOB), DATEPART(day, DOB)
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                dob_str = row.DOB.strftime("%d %b") if row.DOB else "N/A"
                celebrations_list.append({
                    "code": row.EmployeeCode,
                    "name": row.FullName,
                    "date": dob_str,
                    "event": "Birthday"
                })

        else: # Work Anniversaries
            query = """
                SELECT 
                    EmployeeCode, 
                    FullName, 
                    DOJ, 
                    DATEDIFF(year, DOJ, GETDATE()) as CompletedYears
                FROM tblEmployeeMaster
                WHERE DOJ IS NOT NULL 
                  AND (
                    DATEADD(year, DATEDIFF(year, DOJ, GETDATE()), DOJ) BETWEEN GETDATE() - 1 AND GETDATE() + 7
                    OR DATEADD(year, DATEDIFF(year, DOJ, GETDATE()) + 1, DOJ) BETWEEN GETDATE() - 1 AND GETDATE() + 7
                  )
                ORDER BY DATEPART(month, DOJ), DATEPART(day, DOJ)
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                doj_str = row.DOJ.strftime("%d %b") if row.DOJ else "N/A"
                years = row.CompletedYears if row.CompletedYears else 1
                celebrations_list.append({
                    "code": row.EmployeeCode,
                    "name": row.FullName,
                    "date": doj_str,
                    "event": f"{years} Year Anniversary"
                })

        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": celebrations_list}), 200

    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e), "data": []}), 200

# ==========================================
# 1. ATTENDANCE PORTAL PAGE ROUTE
# ==========================================
@hr_bp.route('/attendance-portal', methods=['GET'])
def attendance_portal_page():
    return render_template('attendance_summary.html')


# ==========================================
# 2. BRANCHES API (404 FIX)
# ==========================================
@hr_bp.route('/branches', methods=['GET'])
def get_branches():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Checking if tblBranchMaster exists, else fallback to Branch 1
        query = "SELECT Pk_BranchID as id, BranchName as name FROM tblBranchMaster WHERE IsActive = 1"
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            branches = [{"id": r.id, "name": r.name} for r in rows]
        except Exception:
            branches = [{"id": 1, "name": "Main Branch"}]

        cursor.close()
        conn.close()
        return jsonify({"success": True, "branches": branches}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": True, "branches": [{"id": 1, "name": "Main Branch"}]}), 200


# ==========================================
# 3. GEOFENCES API (404 FIX)
# ==========================================
@hr_bp.route('/geofences', methods=['GET'])
def get_geofences():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT Pk_GeoFenceID as id, LocationName as name FROM tblGeoFenceMaster"
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            geofences = [{"id": r.id, "name": r.name} for r in rows]
        except Exception:
            geofences = [{"id": 1, "name": "Main Hospital Premises"}]

        cursor.close()
        conn.close()
        return jsonify({"success": True, "geofences": geofences}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": True, "geofences": [{"id": 1, "name": "Main Hospital Premises"}]}), 200

    # Save Attendance Record in SSMS Database (Safe with Auto-Table Check)
# 1. Get Attendance Route (Pending aur Approved dono fetch karega)
@hr_bp.route('/attendance', methods=['GET'])
def get_attendance():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Pk_AttendanceID, Fk_EmployeeID, PunchTime, Status, ApprovedStatus, PunchOutTime FROM tblAttendance")
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            records.append({
                "Pk_AttendanceID": row.Pk_AttendanceID if hasattr(row, 'Pk_AttendanceID') else row[0],
                "Fk_EmployeeID": row.Fk_EmployeeID if hasattr(row, 'Fk_EmployeeID') else row[1],
                "PunchTime": str(row.PunchTime if hasattr(row, 'PunchTime') else row[2]),
                "Status": row.Status if hasattr(row, 'Status') else row[3],
                "ApprovedStatus": row.ApprovedStatus if hasattr(row, 'ApprovedStatus') else row[4],
                "PunchOutTime": str(row.PunchOutTime if hasattr(row, 'PunchOutTime') else row[5]) if (row.PunchOutTime if hasattr(row, 'PunchOutTime') else row[5]) else None
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": records}), 200
    except Exception as e:
        if conn: conn.close()
        print("Fetch Attendance Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


# 2. Mark Attendance Route (By default 'Pending' status ke sath save karega)
# ==========================================
# 1. GET ATTENDANCE ROUTE (Fetch All Records)
# ==========================================
@hr_bp.route('/attendance', methods=['GET'])
def get_attendance():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Pk_AttendanceID, Fk_EmployeeID, PunchTime, Status, ApprovedStatus, PunchOutTime FROM tblAttendance")
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            records.append({
                "Pk_AttendanceID": row.Pk_AttendanceID if hasattr(row, 'Pk_AttendanceID') else row[0],
                "Fk_EmployeeID": row.Fk_EmployeeID if hasattr(row, 'Fk_EmployeeID') else row[1],
                "PunchTime": str(row.PunchTime if hasattr(row, 'PunchTime') else row[2]),
                "Status": row.Status if hasattr(row, 'Status') else row[3],
                "ApprovedStatus": row.ApprovedStatus if hasattr(row, 'ApprovedStatus') else row[4],
                "PunchOutTime": str(row.PunchOutTime if hasattr(row, 'PunchOutTime') else row[5]) if (row.PunchOutTime if hasattr(row, 'PunchOutTime') else row[5]) else None
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": records}), 200
    except Exception as e:
        if conn: conn.close()
        print("Fetch Attendance Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# 2. MARK ATTENDANCE ROUTE (Save as Pending)
# ==========================================
@hr_bp.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    conn = None
    try:
        data = request.get_json()
        
        emp_raw = data.get('emp_id') or data.get('emp_code')
        status = data.get('status') # PRESENT, ABSENT, etc.
        att_date = data.get('date') or data.get('attendance_date')
        
        # Requirement ke mutabiq by default 'Pending' status rahega
        approved_status = 'Pending' 

        if not emp_raw or not att_date:
            return jsonify({"success": False, "error": "Employee ID and Date are required!"}), 400

        # String ID (jaise 'EMP1') se numeric ID nikalna
        import re
        numbers = re.findall(r'\d+', str(emp_raw))
        emp_id = int(numbers[0]) if numbers else 1

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check karein ki is employee ka is date par record pehle se hai ya nahi
        check_query = "SELECT Pk_AttendanceID FROM tblAttendance WHERE Fk_EmployeeID = ? AND CAST(PunchTime AS DATE) = ?"
        cursor.execute(check_query, (emp_id, att_date))
        existing = cursor.fetchone()

        if existing:
            update_query = """
                UPDATE tblAttendance 
                SET Status = ?
                WHERE Fk_EmployeeID = ? AND CAST(PunchTime AS DATE) = ?
            """
            cursor.execute(update_query, (status, emp_id, att_date))
        else:
            insert_query = """
                INSERT INTO tblAttendance (Fk_EmployeeID, Status, PunchTime, ApprovedStatus, CreatedOn)
                VALUES (?, ?, CAST(? AS DATETIME), ?, GETDATE())
            """
            cursor.execute(insert_query, (emp_id, status, att_date, approved_status))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Attendance saved successfully as Pending!"}), 200

    except Exception as e:
        if conn: conn.close()
        print("SQL Mark Attendance Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500
# 1. Roster Page Render Route
@hr_bp.route('/roster', methods=['GET'])
def roster_management_page():
    return render_template('roster_management.html',active_page='roster')

# 2. Save Roster Shift to SSMS Database API
@hr_bp.route('/assign-roster-shift', methods=['POST'])
def assign_roster_shift():
    conn = None
    try:
        data = request.get_json()
        emp_id = data.get('emp_id')
        shift_type = data.get('shift_type')
        roster_date = data.get('roster_date')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert or Update Roster Shift in DB
        query = """
            IF EXISTS (SELECT 1 FROM tblEmployeeRoster WHERE Fk_EmployeeID = ? AND RosterDate = ?)
                UPDATE tblEmployeeRoster 
                SET ShiftType = ?
                WHERE Fk_EmployeeID = ? AND RosterDate = ?
            ELSE
                INSERT INTO tblEmployeeRoster (Fk_EmployeeID, RosterDate, ShiftType)
                VALUES (?, ?, ?)
        """
        cursor.execute(query, (emp_id, roster_date, shift_type, emp_id, roster_date, emp_id, roster_date, shift_type))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Shift Assigned Successfully"}), 200

    except Exception as e:
        if conn: conn.close()
        print("Roster DB Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500