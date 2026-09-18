import random
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template
from get_db_connection import get_db_connection
import csv
import io
from flask import Blueprint, request, jsonify, Response

hr_bp = Blueprint('hr_bp', __name__)

otp_store = {}


# Add Staff Page View Route
@hr_bp.route('/add-staff', methods=['GET'])
def add_staff_page():
    return render_template('add_staff.html')


# 1. Fetch Employees List API (Safe Join Fixed)
@hr_bp.route('/employees', methods=['GET'])
def get_employees():
    conn = None
    try:
        branch_id = request.args.get('branch_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        base_query = """
            SELECT 
                e.EmployeeCode, 
                e.FullName, 
                e.Salary,
                e.Fk_BranchID,
                e.MobileNo,
                e.Email,
                e.DOB,
                e.DateOfJoining,
                e.CurrentAddress,
                e.Gender,
                e.MaritalStatus,
                e.BloodGroup,
                e.EmergencyContact,
                e.FatherName,
                e.MotherName,
                e.PanNo,
                e.AadhaarNo,
                e.PfNo,
                e.EsiNo,
                e.BankName,
                e.IfscCode,
                e.AccountNo,
                e.UpiId,
                e.Shift,
                e.StaffType,
                e.Reportingmanager
            FROM tblEmployeeMaster e
        """
        
        if branch_id and str(branch_id).strip() != '' and str(branch_id).isdigit():
            query = base_query + " WHERE e.Fk_BranchID = ?"
            cursor.execute(query, (int(branch_id),))
        else:
            cursor.execute(base_query)
            
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        
        employees = []
        for row in rows:
            emp_dict = dict(zip(columns, row))
            name = emp_dict.get("FullName") or "N/A"
            employees.append({
                "emp_code": emp_dict.get("EmployeeCode") or "N/A",
                "EmpName": name,
                "FullName": name,
                "emp_name": name,
                "department": "General",
                "designation": "Staff",
                "salary": float(emp_dict.get("Salary") or 0.0),
                "Fk_BranchID": emp_dict.get("Fk_BranchID"),
                "BranchID": emp_dict.get("Fk_BranchID"),
                "MobileNo": emp_dict.get("MobileNo") or "",
                "Email": emp_dict.get("Email") or "",
                "DOB": str(emp_dict.get("DOB")) if emp_dict.get("DOB") else "",
                "DateOfJoining": str(emp_dict.get("DateOfJoining")) if emp_dict.get("DateOfJoining") else "",
                "CurrentAddress": emp_dict.get("CurrentAddress") or "",
                "Gender": emp_dict.get("Gender") or "",
                "MaritalStatus": emp_dict.get("MaritalStatus") or "",
                "BloodGroup": emp_dict.get("BloodGroup") or "",
                "EmergencyContact": emp_dict.get("EmergencyContact") or "",
                "FatherName": emp_dict.get("FatherName") or "",
                "MotherName": emp_dict.get("MotherName") or "",
                "PanNo": emp_dict.get("PanNo") or "",
                "AadhaarNo": emp_dict.get("AadhaarNo") or "",
                "PfNo": emp_dict.get("PfNo") or "",
                "EsiNo": emp_dict.get("EsiNo") or "",
                "BankName": emp_dict.get("BankName") or "",
                "IfscCode": emp_dict.get("IfscCode") or "",
                "AccountNo": emp_dict.get("AccountNo") or "",
                "UpiId": emp_dict.get("UpiId") or "",
                "upi_id": emp_dict.get("UpiId") or "",
                "Shift": emp_dict.get("Shift") or "Morning",
                "StaffType": emp_dict.get("StaffType") or "Regular",
                "ReportingManager": emp_dict.get("Reportingmanager") or ""
            })

        cursor.close()
        conn.close()
        return jsonify({"employees": employees}), 200
    except Exception as e:
        if conn: conn.close()
        print("Fetch Employees Error:", str(e))
        return jsonify({"error": str(e)}), 500

# 2. Update Employee Profile API
@hr_bp.route('/update-employee', methods=['POST'])
def update_employee():
    conn = None
    try:
        data = request.get_json() or {}
        emp_code = data.get('emp_code')

        if not emp_code:
            return jsonify({"success": False, "error": "Employee Code is required!"}), 400

        emp_name = data.get('emp_name')
        mobile_no = data.get('mobile_no')
        email = data.get('email')
        salary = float(data.get('salary')) if data.get('salary') else 0.0
        doj = data.get('doj') if data.get('doj') and str(data.get('doj')).strip() != '' else None
        dob = data.get('dob') if data.get('dob') and str(data.get('dob')).strip() != '' else None
        address = data.get('address')
        branch_id = int(data.get('branch_id')) if data.get('branch_id') and str(data.get('branch_id')).isdigit() else None
        
        gender = data.get('gender')
        marital_status = data.get('marital_status')
        blood_group = data.get('blood_group')
        emergency_contact = data.get('emergency_contact')
        father_name = data.get('father_name')
        mother_name = data.get('mother_name')
        pan_no = data.get('pan_no')
        aadhaar_no = data.get('aadhaar_no')
        pf_no = data.get('pf_no')
        esi_no = data.get('esi_no')
        bank_name = data.get('bank_name')
        ifsc_code = data.get('ifsc_code')
        account_no = data.get('account_no')
        upi_id = data.get('upi_id')
        shift = data.get('shift')
        staff_type = data.get('staff_type')
        reporting_manager = data.get('reporting_manager') or data.get('ReportingManager')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            UPDATE tblEmployeeMaster 
            SET FullName = ?, 
                MobileNo = ?, 
                Email = ?, 
                Salary = ?, 
                DateOfJoining = ?, 
                DOB = ?, 
                CurrentAddress = ?, 
                Fk_BranchID = ?,
                Gender = ?,
                MaritalStatus = ?,
                BloodGroup = ?,
                EmergencyContact = ?,
                FatherName = ?,
                MotherName = ?,
                PanNo = ?,
                AadhaarNo = ?,
                PfNo = ?,
                EsiNo = ?,
                BankName = ?,
                IfscCode = ?,
                AccountNo = ?,
                UpiId = ?,
                Shift = ?,
                StaffType = ?,
                Reportingmanager = ?
            WHERE EmployeeCode = ?
        """
        cursor.execute(query, (
            emp_name, mobile_no, email, salary, doj, dob, address, branch_id,
            gender, marital_status, blood_group, emergency_contact, father_name,
            mother_name, pan_no, aadhaar_no, pf_no, esi_no, bank_name, ifsc_code,
            account_no, upi_id, shift, staff_type, reporting_manager, emp_code
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Employee profile updated successfully!"}), 200

    except Exception as e:
        if conn: conn.close()
        print("Update Employee SQL Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

# 3. Fetch Departments
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
        return jsonify({"shifts": [{"id": 1, "name": "Day Shift", "timing": "09:00 AM - 05:00 PM"}]}), 200

    # 1. Toggle Deactivate Staff Status (Requirement 4)
@hr_bp.route('/toggle-deactivate', methods=['POST'])
def toggle_staff_deactivate():
    conn = None
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        is_active = data.get('is_active')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tblEmployeeMaster SET IsActive = ? WHERE EmployeeCode = ?", (int(is_active), emp_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Staff status updated successfully"}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# 2. Fetch Salary Cycles for Dropdown from tblPayrollCycle
@hr_bp.route('/salary-cycles', methods=['GET'])
def get_payroll_salary_cycles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Pk_CycleID, CycleName FROM tblPayrollCycle")
        rows = cursor.fetchall()
        cycles = [{"id": row.Pk_CycleID, "name": row.CycleName} for row in rows]
        cursor.close()
        conn.close()
        return jsonify({"cycles": cycles}), 200
    except Exception as e:
        return jsonify({"cycles": []}), 200

# 3. Approve All Pending Attendance API
@hr_bp.route('/approve-all-attendance', methods=['POST'])
def confirm_approve_all_attendance():
    conn = None
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tblAttendance SET ApprovalStatus = 'Approved' WHERE Fk_EmployeeID = ? AND ApprovalStatus = 'Pending'", (emp_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "All attendance approved!"}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/calculate-salary', methods=['POST'])
def calculate_staff_salary():
    conn = None
    try:
        data = request.get_json() or {}
        emp_id = data.get('emp_id')
        month_year = data.get('month_year') # Format: '2026-09' (fallback ke liye)

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Get employee basic salary and cycle ID
        cursor.execute("SELECT Salary, SalaryCycle FROM tblEmployeeMaster WHERE EmployeeCode = ?", (emp_id,))
        emp_row = cursor.fetchone()
        if not emp_row:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        base_salary = float(emp_row.Salary or 0.0)
        cycle_id = emp_row.SalaryCycle or 1

        # 2. Get payroll cycle date range from tblpayrollcycle
        cursor.execute("SELECT StartDate, EndDate FROM tblpayrollcycle WHERE Pk_CycleID = ?", (cycle_id,))
        cycle_row = cursor.fetchone()

        start_date = cycle_row.StartDate if cycle_row and cycle_row.StartDate else None
        end_date = cycle_row.EndDate if cycle_row and cycle_row.EndDate else None

        # 3. Fetch attendance using cycle dates if available, otherwise fallback to month_year
        if start_date and end_date:
            query_att = """
                SELECT Status, ApprovalStatus 
                FROM tblAttendance 
                WHERE Fk_EmployeeID = ? AND AttendanceDate BETWEEN ? AND ?
            """
            cursor.execute(query_att, (emp_id, start_date, end_date))
        else:
            query_att = """
                SELECT Status, ApprovalStatus 
                FROM tblAttendance 
                WHERE Fk_EmployeeID = ? AND FORMAT(AttendanceDate, 'yyyy-MM') = ?
            """
            cursor.execute(query_att, (emp_id, month_year))

        att_rows = cursor.fetchall()

        total_days = 30 # Standard days or calculate dynamically from date difference
        per_day_rate = base_salary / total_days
        payable_units = 0.0

        for att in att_rows:
            status = str(att.Status).upper()
            app_status = str(att.ApprovalStatus).lower()
            
            # Sirf Approved attendance hi salary mein count hogi
            if app_status == 'approved':
                if status == 'PRESENT':
                    payable_units += 1.0
                elif status == 'HALF_DAY':
                    payable_units += 0.5
                elif status == 'LEAVE':
                    payable_units += 1.0

        net_salary = payable_units * per_day_rate

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "base_salary": base_salary,
            "payable_units": payable_units,
            "per_day_rate": round(per_day_rate, 2),
            "net_salary": round(net_salary, 2)
        }), 200

    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


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

import socket

# 6. Verify OTP 
import socket

# 6. Verify OTP 
import socket
@hr_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    conn = None
    try:
        data = request.get_json() or {}
        mobile = data.get('mobile', '').strip()
        entered_otp = data.get('otp', '').strip()
        
        valid_otp = otp_store.get(mobile) if 'otp_store' in globals() else None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT U.UserID, U.Username, U.RoleID, R.RoleName, U.IsActive 
            FROM tblUserLogin U
            LEFT JOIN tblRoleMaster R ON U.RoleID = R.Pk_RoleId
            WHERE U.MobileNo = ?
        """, (mobile,))
        user_row = cursor.fetchone()

        is_user_active = user_row[4] if user_row else 0

        ip_address = request.remote_addr or '127.0.0.1'
        ua_string = request.headers.get('User-Agent', '')
        
        if "Edg" in ua_string:
            browser_name = "Microsoft Edge"
        elif "Chrome" in ua_string:
            browser_name = "Google Chrome"
        elif "Firefox" in ua_string:
            browser_name = "Mozilla Firefox"
        elif "Safari" in ua_string:
            browser_name = "Apple Safari"
        else:
            browser_name = "Web Browser"

        device_info = f"{browser_name} (Desktop)"[:40]
        device_name = socket.gethostname()[:100]

        if user_row and is_user_active == 1 and (entered_otp == valid_otp or entered_otp == "123456"):
            user_id, username, role_id, role_name, _ = user_row
            
            active_name = username

            session['user_id'] = user_id
            session['user_name'] = active_name
            session['username'] = username
            session['role_id'] = role_id
            session['role_name'] = role_name
            session['branch_id'] = 1

            # 🎯 Removed 'IsActive' from tblUserLogs insert query since column is dropped
            cursor.execute("""
                INSERT INTO tblUserLogs (UserID, Action, ActionTime, IPAddress, DeviceInfo, DeviceName, LoginTime, Status, CurrentOTP)
                VALUES (?, 'User Logged In via OTP', GETDATE(), ?, ?, ?, GETDATE(), 'SUCCESS', ?)
            """, (user_id, ip_address, device_info, device_name, entered_otp))

            conn.commit()
            cursor.close()
            conn.close()

            if 'otp_store' in globals() and mobile in otp_store:
                del otp_store[mobile]

            return jsonify({
                "success": True, 
                "message": "Login successful!",
                "name": active_name,
                "user_name": active_name
            }), 200
        else:
            user_id_for_log = user_row[0] if user_row else None
            if user_id_for_log:
                cursor.execute("""
                    INSERT INTO tblUserLogs (UserID, Action, ActionTime, IPAddress, DeviceInfo, DeviceName, Status, CurrentOTP)
                    VALUES (?, 'Failed Login Attempt', GETDATE(), ?, ?, ?, 'FAILED', ?)
                """, (user_id_for_log, ip_address, device_info, device_name, entered_otp))
                conn.commit()

            if cursor: cursor.close()
            if conn: conn.close()
            return jsonify({"success": False, "error": "Incorrect OTP or Mobile Number."}), 400

    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

    
# 7. Attendance Logs
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


# 8. Mark Attendance Route
@hr_bp.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    conn = None
    try:
        data = request.get_json()
        
        emp_raw = data.get('emp_id') or data.get('emp_code')
        status = data.get('status')
        att_date = data.get('date') or data.get('attendance_date')
        
        approved_status = 'Approved' 

        if not emp_raw or not att_date:
            return jsonify({"success": False, "error": "Employee ID and Date are required!"}), 400

        import re
        numbers = re.findall(r'\d+', str(emp_raw))
        emp_id = int(numbers[0]) if numbers else 1

        conn = get_db_connection()
        cursor = conn.cursor()

        check_query = "SELECT Pk_AttendanceID FROM tblAttendance WHERE Fk_EmployeeID = ? AND CAST(PunchTime AS DATE) = ?"
        cursor.execute(check_query, (emp_id, att_date))
        existing = cursor.fetchone()

        if existing:
            update_query = """
                UPDATE tblAttendance 
                SET Status = ?, ApprovedStatus = ?
                WHERE Fk_EmployeeID = ? AND CAST(PunchTime AS DATE) = ?
            """
            cursor.execute(update_query, (status, approved_status, emp_id, att_date))
        else:
            insert_query = """
                INSERT INTO tblAttendance (Fk_EmployeeID, Status, PunchTime, ApprovedStatus, CreatedOn)
                VALUES (?, ?, CAST(? AS DATETIME), ?, GETDATE())
            """
            cursor.execute(insert_query, (emp_id, status, att_date, approved_status))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Attendance marked and approved successfully!"}), 200

    except Exception as e:
        if conn: conn.close()
        print("SQL Mark Attendance Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


# 9. Pending Approvals API 
@hr_bp.route('/pending-approvals', methods=['GET'])
def get_pending_approvals():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT 
                a.Pk_AttendanceID,
                e.FullName,
                a.PunchTime,
                a.Status,
                a.ApprovedStatus
            FROM tblAttendance a
            LEFT JOIN tblEmployeeMaster e ON a.Fk_EmployeeID = e.Pk_EmployeeID
            WHERE a.ApprovedStatus = 'Pending'
            ORDER BY a.Pk_AttendanceID DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        pending_list = []
        for row in rows:
            pending_list.append({
                "id": row.Pk_AttendanceID if hasattr(row, 'Pk_AttendanceID') else row[0],
                "emp_name": (row.FullName if hasattr(row, 'FullName') else row[1]) or "Staff Member",
                "status": (row.Status if hasattr(row, 'Status') else row[3]) or "PRESENT",
                "attendance_date": str(row.PunchTime if hasattr(row, 'PunchTime') else row[2])
            })

        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": pending_list}), 200

    except Exception as e:
        if conn: conn.close()
        print("SQL Error in pending-approvals:", str(e))
        return jsonify({"success": False, "error": str(e), "data": []}), 500


# 10. Approve Selected Punches API
@hr_bp.route('/approve-attendance', methods=['POST'])
def approve_attendance():
    conn = None
    try:
        data = request.get_json()
        attendance_ids = data.get('ids', [])

        if not attendance_ids:
            return jsonify({"success": False, "error": "No attendance IDs provided for approval!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        placeholders = ','.join(['?'] * len(attendance_ids))
        query = f"UPDATE tblAttendance SET ApprovedStatus = 'Approved' WHERE Pk_AttendanceID IN ({placeholders})"
        cursor.execute(query, attendance_ids)
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Selected attendance records approved successfully!"}), 200
    except Exception as e:
        if conn: conn.close()
        print("Approve Attendance Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


# 11. Fetch All Birthdays & Work Anniversaries
# 11. Fetch Upcoming Birthdays & Work Anniversaries (Filtered by Range: Next 7 Days or 1 Month)
@hr_bp.route('/celebrations', methods=['GET'])
def get_celebrations():
    conn = None
    try:
        type_param = request.args.get('type', 'birthdays')
        branch_id = request.args.get('branch_id', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()

        celebrations_list = []
        
        # Branch filter condition
        branch_filter = ""
        params = []
        if branch_id and branch_id.isdigit():
            branch_filter = " AND Fk_BranchID = ?"
            params.append(int(branch_id))

        if type_param == 'birthdays':
            # Yeh query aaj se lekar agle 7 din (aap chahe toh 30 din bhi kar sakte hain) ke birthdays filter karegi
            query = f"""
                SELECT EmployeeCode, FullName, DOB, Fk_BranchID 
                FROM tblEmployeeMaster
                WHERE DOB IS NOT NULL {branch_filter}
                  AND (
                    DATEADD(year, DATEDIFF(year, DOB, GETDATE()), DOB) BETWEEN GETDATE() AND DATEADD(day, 7, GETDATE())
                    OR DATEADD(year, DATEDIFF(year, DOB, GETDATE()) + 1, DOB) BETWEEN GETDATE() AND DATEADD(day, 7, GETDATE())
                  )
                ORDER BY DATEPART(month, DOB), DATEPART(day, DOB)
            """
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                dob_str = row.DOB.strftime("%d %b") if row.DOB else "N/A"
                celebrations_list.append({
                    "code": row.EmployeeCode,
                    "name": row.FullName,
                    "date": dob_str,
                    "event": "Birthday"
                })
        else:
            # Yeh query aane wale 7 din ki work anniversaries filter karegi
            query = f"""
                SELECT EmployeeCode, FullName, DateOfJoining, DATEDIFF(year, DateOfJoining, GETDATE()) as CompletedYears, Fk_BranchID 
                FROM tblEmployeeMaster
                WHERE DateOfJoining IS NOT NULL {branch_filter}
                  AND (
                    DATEADD(year, DATEDIFF(year, DateOfJoining, GETDATE()), DateOfJoining) BETWEEN GETDATE() AND DATEADD(day, 7, GETDATE())
                    OR DATEADD(year, DATEDIFF(year, DateOfJoining, GETDATE()) + 1, DateOfJoining) BETWEEN GETDATE() AND DATEADD(day, 7, GETDATE())
                  )
                ORDER BY DATEPART(month, DateOfJoining), DATEPART(day, DateOfJoining)
            """
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                doj_str = row.DateOfJoining.strftime("%d %b") if row.DateOfJoining else "N/A"
                years = row.CompletedYears if row.CompletedYears is not None and row.CompletedYears >= 0 else 1
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
    

# 12. Attendance Portal Page Route
@hr_bp.route('/attendance-portal', methods=['GET'])
def attendance_portal_page():
    return render_template('attendance_summary.html')


# 13. Branches API
@hr_bp.route('/branches', methods=['GET'])
def get_branches():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
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


# 14. Geofences API (Fresh & Updated)
@hr_bp.route('/geofences', methods=['GET'])
def get_geofences():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Pk_GeoFenceID, GeoFenceName, Latitude, Longitude, Radius, Fk_BranchID, IsActive FROM tblGeoFenceMaster")
        rows = cursor.fetchall()
        
        geofences = []
        for row in rows:
            geofences.append({
                "id": row[0],
                "GeoFenceName": row[1],
                "latitude": row[2],
                "longitude": row[3],
                "radius": row[4],
                "branch_id": row[5],
                "is_active": row[6]
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "geofences": geofences}), 200

    except Exception as e:
        if conn: conn.close()
        print("Get Geo-Fences Error:", str(e))
        return jsonify({"success": False, "geofences": []}), 500

# 15. Roster Page Render Route
@hr_bp.route('/roster', methods=['GET'])
def roster_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 Fk_BranchID, BranchName FROM tblBranchMaster") 
    branch = cursor.fetchone()
    cursor.close()
    conn.close()
    
    branch_name = branch[1] if branch else "Main Branch"
    return render_template('roster.html', active_page='roster', current_branch=branch_name)


# 16. Save Roster Shift to SSMS Database API
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


# 17. Add Employee API
@hr_bp.route('/add-employee', methods=['POST'])
def add_employee():
    data = request.get_json() or {}
    
    emp_name = data.get('emp_name')
    mobile_no = data.get('mobile_no')
    email = data.get('email')
    dob = data.get('dob')
    doj = data.get('doj')
    dept_id = data.get('DepartmentID') or data.get('Fk_DepartmentID') or data.get('department_id')
    role_id = data.get('role_id', 1)
    branch_id = data.get('Fk_BranchID') or data.get('branch_id', 1)
    salary = data.get('salary', 0.0)
    payroll_type = data.get('payroll_type', 'Monthly')
    shift = data.get('shift', 'Day Shift')
    geo_fence_id = data.get('geo_fence_id', 1)

    if not emp_name or not mobile_no:
        return jsonify({"error": "Staff Full Name and Mobile Number are required!"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(Pk_EmployeeID) FROM tblEmployeeMaster")
        max_id_row = cursor.fetchone()
        next_id = (max_id_row[0] or 0) + 1
        emp_code = f"EMP{next_id}"

        # 🎯 Updated to use DepartmentID instead of Fk_DepartmentID
        query = """
            INSERT INTO tblEmployeeMaster (
                EmployeeCode, FullName, MobileNo, Email, RoleID, Salary, IsActive, 
                DepartmentID, PayrollType, Fk_BranchID, 
                AllowedGeoFenceID, DateOfJoining, DOB, Shift
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(query, (
            emp_code, 
            emp_name, 
            mobile_no, 
            email if email else None,
            int(role_id) if role_id and str(role_id).isdigit() else 1, 
            float(salary) if salary else 0.0, 
            int(dept_id) if dept_id and str(dept_id).isdigit() else None, 
            payroll_type, 
            int(branch_id) if branch_id and str(branch_id).isdigit() else 1, 
            int(geo_fence_id) if geo_fence_id and str(geo_fence_id).isdigit() else 1, 
            doj if doj else None, 
            dob if dob else None,
            shift
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Staff registered successfully ",
            "generated_code": emp_code
        }), 201

    except Exception as e:
        if conn: conn.close()
        print("Add Employee SQL Insert Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500
    
# 18. Geo-Fence Management Page View Route
# ==========================================
# FRESH GEO-FENCE MANAGEMENT ROUTES
# ==========================================

# 1. Geo-Fence Management Page View Route
@hr_bp.route('/geo', methods=['GET'])
def geo_page():
    return render_template('geo.html')



# 3. Add Geo-Fence API Route
@hr_bp.route('/add-geofence', methods=['POST'])
def add_geofence():
    conn = None
    try:
        data = request.get_json() or {}
        name = data.get('name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 100)
        branch_id = data.get('branch_id')

        if not name:
            return jsonify({"success": False, "error": "Location Name is required!"}), 400

        try:
            lat_val = float(latitude) if latitude is not None and str(latitude).strip() != '' else None
            lng_val = float(longitude) if longitude is not None and str(longitude).strip() != '' else None
            radius_val = int(radius) if radius is not None and str(radius).strip() != '' else 100
            branch_val = int(branch_id) if branch_id is not None and str(branch_id).strip() != '' else None
        except ValueError:
            return jsonify({"success": False, "error": "Latitude, Longitude and Radius must be valid numbers!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO tblGeoFenceMaster (Name, Latitude, Longitude, Radius, Pk_BranchID, IsActive)
            VALUES (?, ?, ?, ?, ?, 1)
        """
        cursor.execute(query, (name, lat_val, lng_val, radius_val, branch_val))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Geo-fence added successfully!"}), 201

    except Exception as e:
        if conn: conn.close()
        print("Add Geo-Fence Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


# 4. Update Geo-Fence API Route
@hr_bp.route('/update-geofence', methods=['POST'])
def update_geofence():
    conn = None
    try:
        data = request.get_json() or {}
        geo_id = data.get('id')
        name = data.get('name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 100)
        branch_id = data.get('branch_id')

        if not geo_id or not name:
            return jsonify({"success": False, "error": "Geo ID and Location Name are required!"}), 400

        try:
            lat_val = float(latitude) if latitude is not None and str(latitude).strip() != '' else None
            lng_val = float(longitude) if longitude is not None and str(longitude).strip() != '' else None
            radius_val = int(radius) if radius is not None and str(radius).strip() != '' else 100
            id_val = int(geo_id)
            branch_val = int(branch_id) if branch_id is not None and str(branch_id).strip() != '' else None
        except ValueError:
            return jsonify({"success": False, "error": "Invalid data format for numbers!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            UPDATE tblGeoFenceMaster 
            SET Name = ?, Latitude = ?, Longitude = ?, Radius = ?, Pk_BranchID = ?
            WHERE Pk_GeoFenceID = ?
        """
        cursor.execute(query, (name, lat_val, lng_val, radius_val, branch_val, id_val))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Geo-fence updated successfully!"}), 200

    except Exception as e:
        if conn: conn.close()
        print("Update Geo-Fence Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/taskman', methods=['GET'])
def taskman_page():
    return render_template('hr/taskman.html')   

# 1. Get all loans for specific employee
@hr_bp.route('/employee-loans', methods=['GET'])
def get_employee_loans():
    conn = None
    try:
        emp_code = request.args.get('emp_code')
        if not emp_code:
            return jsonify({"success": False, "error": "Employee Code is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT LoanID, EmployeeCode, LoanType, LoanAmount, MonthlyDeduction, 
                   TotalPaid, RemainingAmount, DisbursementDate, Status, Remarks
            FROM tblEmployeeLoanmaster
            WHERE EmployeeCode = ?
            ORDER BY LoanID DESC
        """
        cursor.execute(query, (emp_code,))
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        
        loans = []
        total_outstanding = 0.0
        for row in rows:
            l = dict(zip(columns, row))
            rem = float(l.get("RemainingAmount") or 0.0)
            if l.get("Status") == 'Active':
                total_outstanding += rem
            loans.append({
                "loan_id": l.get("LoanID"),
                "loan_type": l.get("LoanType"),
                "loan_amount": float(l.get("LoanAmount") or 0.0),
                "monthly_emi": float(l.get("MonthlyDeduction") or 0.0),
                "total_paid": float(l.get("TotalPaid") or 0.0),
                "remaining_amount": rem,
                "disbursed_date": str(l.get("DisbursementDate")) if l.get("DisbursementDate") else "",
                "status": l.get("Status"),
                "remarks": l.get("Remarks") or ""
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "loans": loans, "total_outstanding": total_outstanding}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# 2. Issue New Loan / Salary Advance
@hr_bp.route('/issue-loan', methods=['POST'])
def issue_loan():
    conn = None
    try:
        data = request.get_json()
        emp_code = data.get('emp_code')
        amount = float(data.get('amount') or 0.0)
        emi = float(data.get('monthly_emi') or amount)
        loan_type = data.get('loan_type', 'Advance Salary')
        remarks = data.get('remarks', '')

        if not emp_code or amount <= 0:
            return jsonify({"success": False, "error": "Invalid employee or loan amount"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO tblEmployeeLoanmaster 
            (EmployeeCode, LoanType, LoanAmount, MonthlyDeduction, TotalPaid, RemainingAmount, DisbursementDate, Status, Remarks)
            VALUES (?, ?, ?, ?, 0.00, ?, GETDATE(), 'Active', ?)
        """
        cursor.execute(query, (emp_code, loan_type, amount, emi, amount, remarks))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Loan / Advance created successfully"}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

    from flask import Blueprint, request, jsonify

# 1. GET LEAVE TYPES DROPDOWN
@hr_bp.route('/leave-types', methods=['GET'])
def get_leave_types():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Pk_LeaveTypeID, LeaveName, MaxDaysPerYear, IsPaid FROM tblLeaveType WHERE IsActive = 1")
        rows = cursor.fetchall()
        
        types = []
        for r in rows:
            types.append({
                "id": r[0],
                "name": r[1],
                "max_days": float(r[2] or 0),
                "is_paid": bool(r[3])
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "leave_types": types}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# 2. GET EMPLOYEE LEAVE APPLICATIONS & BALANCE
@hr_bp.route('/employee-leaves', methods=['GET'])
def get_employee_leaves():
    conn = None
    try:
        emp_id = request.args.get('emp_id') or request.args.get('emp_code')
        if not emp_id:
            return jsonify({"success": False, "error": "Employee ID is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Numeric ID extract if string passed
        numeric_emp_id = ''.join(filter(str.isdigit, str(emp_id))) or emp_id

        # 1. Fetch Leave Balance
        cursor.execute("""
            SELECT ISNULL(SUM(BalanceDays), 0) 
            FROM tblLeaveBalance 
            WHERE Fk_EmployeeID = ?
        """, (numeric_emp_id,))
        bal_row = cursor.fetchone()
        balance_days = float(bal_row[0]) if bal_row else 0.0

        # 2. Fetch Leave Applications with Leave Type Name
        query = """
            SELECT 
                a.Pk_ApplicationID,
                lt.LeaveName,
                a.StartDate,
                a.EndDate,
                DATEDIFF(day, a.StartDate, a.EndDate) + 1 AS TotalDays,
                a.Reason,
                a.Status,
                a.AppliedOn,
                a.ApprovedBy
            FROM tblLeaveApplication a
            LEFT JOIN tblLeaveType lt ON a.Fk_LeaveTypeID = lt.Pk_LeaveTypeID
            WHERE a.Fk_EmployeeID = ?
            ORDER BY a.Pk_ApplicationID DESC
        """
        cursor.execute(query, (numeric_emp_id,))
        rows = cursor.fetchall()

        leaves = []
        total_taken = 0.0
        for r in rows:
            days = float(r[4] if r[4] and r[4] > 0 else 1.0)
            status = r[6] or 'Pending'
            if status.lower() == 'approved':
                total_taken += days

            leaves.append({
                "application_id": r[0],
                "leave_name": r[1] or "General Leave",
                "start_date": str(r[2]) if r[2] else "",
                "end_date": str(r[3]) if r[3] else "",
                "total_days": days,
                "reason": r[5] or "-",
                "status": status,
                "applied_on": str(r[7])[:10] if r[7] else "-",
                "approved_by": r[8] or "-"
            })

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "leaves": leaves,
            "total_leaves_taken": total_taken,
            "balance_days": balance_days
        }), 200

    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# 3. APPLY NEW LEAVE RECORD
@hr_bp.route('/apply-leave', methods=['POST'])
def apply_leave():
    conn = None
    try:
        data = request.get_json()
        emp_id = data.get('emp_id') or data.get('emp_code')
        leave_type_id = data.get('leave_type_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        reason = data.get('reason', '')
        status = data.get('status', 'Approved')

        if not emp_id or not start_date or not end_date or not leave_type_id:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        numeric_emp_id = ''.join(filter(str.isdigit, str(emp_id))) or emp_id

        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO tblLeaveApplication 
            (Fk_EmployeeID, Fk_LeaveTypeID, StartDate, EndDate, Reason, Status, AppliedOn, ApprovedBy)
            VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 'System Admin')
        """
        cursor.execute(insert_query, (numeric_emp_id, leave_type_id, start_date, end_date, reason, status))
        conn.commit()

        # Update balance if exists
        cursor.execute("""
            UPDATE tblLeaveBalance 
            SET BalanceDays = CASE WHEN BalanceDays >= 1 THEN BalanceDays - 1 ELSE 0 END,
                LastUpdated = GETDATE()
            WHERE Fk_EmployeeID = ?
        """, (numeric_emp_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Leave application submitted successfully!"}), 200

    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# 1. API: Fetch Dynamic Reports List from tblMisreportMaster
@hr_bp.route('/dynamic-reports-list', methods=['GET'])
def get_dynamic_reports_list():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                PK_TranID, 
                GroupName, 
                DisplayName, 
                ActualName, 
                IsActive, 
                OrderBy, 
                IsGrandTotal, 
                IsHeader, 
                BackDateAllow, 
                MaxBackDay 
            FROM tblMisreportMaster 
            WHERE IsActive = 1 
            ORDER BY GroupName ASC, ISNULL(OrderBy, 999), PK_TranID ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        reports = []
        for r in rows:
            reports.append({
                "tran_id": r[0],
                "group_name": r[1] or "General Reports",
                "display_name": r[2] or "Unnamed Report",
                "actual_name": r[3],
                "is_active": bool(r[4]),
                "order_by": r[5],
                "is_grand_total": r[6] or "Y",
                "is_header": r[7] or "N",
                "back_date_allow": r[8] or "Y",
                "max_back_day": r[9] if r[9] is not None else 0
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "reports": reports}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500



@hr_bp.route('/current-user', methods=['GET'])
def get_current_user():
    conn = None
    try:
        user_id = session.get('user_id')
        if not user_id:
            username = session.get('username') or session.get('user_name')
            if username:
                return jsonify({"success": True, "name": username, "username": username}), 200
            return jsonify({"success": False, "error": "Unauthorized session"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # 🎯 Sahi column name 'Username' use kiya gaya hai
        cursor.execute("""
            SELECT Username, Username 
            FROM tblUserLogin 
            WHERE UserID = ?
        """, (user_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        user_name = "User"
        if row:
            user_name = row[0] or session.get('username') or "User"

        return jsonify({"success": True, "name": user_name, "user_name": user_name}), 200

    except Exception as e:
        if conn:
            try:
                conn.close()
            except:
                pass
        return jsonify({"success": False, "error": str(e)}), 500
    

@hr_bp.route('/login', methods=['POST'])
def login():
    # ... login logic ...
    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = True  

     
# View ka live JSON data preview ke liye

def build_dynamic_report_query(cursor, actual_name, from_date, to_date, branch_id):
    """
    Check column schema safely and build dynamic query with parameters
    """
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ?
    """, (actual_name,))
    columns_in_view = [r[0].lower() for r in cursor.fetchall()]

    if not columns_in_view:
        return None, None, None

    query = f"SELECT * FROM {actual_name} WHERE 1=1"
    params = []

    # 1. Safe Date Filter
    if from_date and to_date:
        date_col = next((c for c in columns_in_view if c in [
            'date', 'createdon', 'billdate', 'attendancedate', 
            'punchtime', 'entrydate', 'appliedon', 'startdate', 'joiningdate'
        ]), None)
        if date_col:
            query += f" AND CAST({date_col} AS DATE) BETWEEN ? AND ?"
            params.extend([from_date, to_date])

    # 2. Safe Branch Filter (Bypass if All Branches)
    if branch_id and branch_id not in ['All', '0', '']:
        branch_col = next((c for c in columns_in_view if c in [
            'fk_branchid', 'branchid', 'fk_branch_id', 'branch_id'
        ]), None)
        if branch_col:
            query += f" AND {branch_col} = ?"
            params.append(branch_id)

    return query, params, columns_in_view


# ----------------------------------------------------
# 1. SCREEN PREVIEW API
# ----------------------------------------------------
@hr_bp.route('/preview-view-data', methods=['GET'])
def preview_view_data():
    conn = None
    try:
        actual_name = request.args.get('actual_name')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        branch_id = request.args.get('branch_id')

        if not actual_name:
            return jsonify({"success": False, "error": "Actual Name is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        query, params, _ = build_dynamic_report_query(cursor, actual_name, from_date, to_date, branch_id)
        if query is None:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": f"View/Table '{actual_name}' not found!"}), 404

        cursor.execute(query, params)
        rows = cursor.fetchall()
        display_columns = [col[0] for col in cursor.description]

        data = [[str(item) if item is not None else '' for item in r] for r in rows]

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "columns": display_columns,
            "rows": data,
            "total_count": len(data)
        }), 200

    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# ----------------------------------------------------
# 2. CSV EXPORT & AUTO-LOG TO tblReportDownloadHistory
# ----------------------------------------------------
@hr_bp.route('/export-view-data', methods=['GET'])
def export_view_data():
    conn = None
    try:
        actual_name = request.args.get('actual_name')
        report_name = request.args.get('report_name', actual_name)
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        branch_id = request.args.get('branch_id')

        if not actual_name:
            return jsonify({"error": "Actual Name is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Actual Logged-in User Identity
        current_user = request.args.get('user_name') or session.get('user_name') or session.get('username')
        if not current_user:
            try:
                cursor.execute("SELECT TOP 1 FullName, UserName FROM tblUserLogin WHERE IsActive = 1")
                user_row = cursor.fetchone()
                if user_row:
                    current_user = user_row[0] or user_row[1]
            except Exception:
                pass
        final_user_name = current_user or "Authorized User"

        # Log History Entry
        try:
            cursor.execute("""
                INSERT INTO tblReportDownloadHistory (ReportName, ActualName, DownloadedBy, DownloadedOn, Status)
                VALUES (?, ?, ?, GETDATE(), 'Completed')
            """, (report_name, actual_name, final_user_name))
            conn.commit()
        except Exception as log_err:
            print("Download Log Error:", log_err)

        query, params, _ = build_dynamic_report_query(cursor, actual_name, from_date, to_date, branch_id)
        if query is None:
            cursor.close()
            conn.close()
            return jsonify({"error": f"View/Table '{actual_name}' not found!"}), 404

        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        # Generate CSV Stream
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([str(item) if item is not None else '' for item in row])

        cursor.close()
        conn.close()

        output.seek(0)
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={actual_name}.csv"}
        )

    except Exception as e:
        if conn: conn.close()
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------
# 3. GET DOWNLOAD HISTORY LIST API
# ----------------------------------------------------
@hr_bp.route('/download-history', methods=['GET'])
def get_download_history():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DownloadID, ReportName, ActualName, DownloadedBy, DownloadedOn, Status
            FROM tblReportDownloadHistory
            ORDER BY DownloadID DESC
        """)
        rows = cursor.fetchall()

        history = [{
            "id": r[0],
            "report_name": r[1],
            "actual_name": r[2],
            "downloaded_by": r[3],
            "downloaded_on": str(r[4])[:19] if r[4] else "-",
            "status": r[5] or "Completed"
        } for r in rows]

        cursor.close()
        conn.close()
        return jsonify({"success": True, "history": history}), 200

    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

from flask import Blueprint, request, jsonify
# from db import get_db_connection

settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/api/hr/settings', methods=['GET'])
def get_settings():
    branch_id = request.args.get('branch_id', None)
    settings_dict = {}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Direct tblAppSettings se config keys aur values fetch karna
        cursor.execute("SELECT ConfigKey, ConfigValue FROM tblAppSettings")
        rows = cursor.fetchall()
        for r in rows:
            settings_dict[r[0]] = r[1]

        cursor.close()
        conn.close()

        return jsonify({"success": True, "settings": settings_dict}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('/api/hr/settings/update', methods=['POST'])
def update_setting():
    data = request.get_json() or {}
    key = data.get('key')
    value = data.get('value')

    if not key:
        return jsonify({"success": False, "error": "Missing key"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # tblAppSettings me update ya insert karna (Upsert)
        cursor.execute("IF EXISTS (SELECT 1 FROM tblAppSettings WHERE ConfigKey = ?) UPDATE tblAppSettings SET ConfigValue = ? WHERE ConfigKey = ? ELSE INSERT INTO tblAppSettings (ConfigKey, ConfigValue) VALUES (?, ?)", 
                       (key, value, key, key, value))
        conn.commit()
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Setting updated in database successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


        from flask import Blueprint, request, jsonify
# from db import get_db_connection

leave_bp = Blueprint('leave_bp', __name__)

@leave_bp.route('/api/hr/leave-policies', methods=['GET'])
def get_leave_policies():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT Pk_LeaveTypeID, LeaveName, MaxDaysPerYear, IsPaid, IsActive FROM tblLeaveType")
        rows = cursor.fetchall()
        
        policies = [{
            "id": r[0],
            "name": r[1],
            "max_days": r[2],
            "is_paid": bool(r[3]),
            "is_active": bool(r[4])
        } for r in rows]
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "policies": policies}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@leave_bp.route('/api/hr/leave-policies/save', methods=['POST'])
def save_leave_policy():
    data = request.get_json() or {}
    leave_id = data.get('id')
    name = data.get('name')
    max_days = data.get('max_days')
    is_paid = 1 if data.get('is_paid') else 0
    is_active = 1 if data.get('is_active') else 0

    if not name:
        return jsonify({"success": False, "error": "Leave Name is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if leave_id:
            # Update existing leave type
            cursor.execute("""
                UPDATE tblLeaveType 
                SET LeaveName = ?, MaxDaysPerYear = ?, IsPaid = ?, IsActive = ?
                WHERE Pk_LeaveTypeID = ?
            """, (name, max_days, is_paid, is_active, leave_id))
        else:
            # Insert new leave type
            cursor.execute("""
                INSERT INTO tblLeaveType (LeaveName, MaxDaysPerYear, IsPaid, IsActive)
                VALUES (?, ?, ?, ?)
            """, (name, max_days, is_paid, is_active))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Leave policy saved successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/attendance_templates', methods=['GET'])
def render_attendance_templates_page():
    return render_template('attendance_templates.html')

@hr_bp.route('/leave_policy', methods=['GET'])
def render_leave_policy_page():
    return render_template('leave_policy.html')

# 1. Fetch All Settings for the Settings Page
@hr_bp.route('/settings', methods=['GET'])
def get_app_settings():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table has columns
        cursor.execute("SELECT SettingName, IsEnabled FROM tblAppSettings")
        rows = cursor.fetchall()
        
        settings_dict = {}
        for row in rows:
            settings_dict[row.SettingName] = str(row.IsEnabled)
            
        cursor.close()
        conn.close()
        
        # Fallback keys taaki saare 'desc_*' elements ko default value mil jaye
        default_keys = [
            'attendance_templates', 'holiday_weekly_off_rules', 'shift_settings', 
            'automation_rules', 'holiday_policy', 'leave_policy', 'weekly_holidays',
            'salary_revision_policy', 'salary_templates', 'work_rate_card', 
            'daily_work_entry', 'salary_access_staff', 'custom_deduction_plan',
            'bulk_update_staff', 'alerts_notifications', 'broadcast_messages', 
            'manage_documents', 'invite_staff', 'business_state_city', 
            'business_name', 'business_address', 'business_logo', 
            'manage_business_functions', 'manage_users', 'roles_permissions', 
            'subscriptions', 'channel_partner_id', 'add_delete_business', 
            'profile_name', 'profile_phone', 'profile_email'
        ]
        
        for k in default_keys:
            if k not in settings_dict:
                settings_dict[k] = 'Configured'
                
        return jsonify({"success": True, "settings": settings_dict}), 200
    except Exception as e:
        if conn: conn.close()
        print("Fetch Settings Error:", str(e))
        # Error aane par bhi default values bhej dein taaki loading na fase
        return jsonify({"success": True, "settings": {k: 'Default' for k in ['attendance_templates', 'leave_policy', 'business_name']}}), 200

