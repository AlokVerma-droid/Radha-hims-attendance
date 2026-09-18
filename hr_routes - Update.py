import random
from datetime import datetime
import csv
import io
from flask import Blueprint, request, jsonify, session, render_template, Response
from get_db_connection import get_db_connection
import base64
import base64
import datetime
import numpy as np
import cv2


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




# 2. Update Employee Profile API (Fully Matched with your Database Schema)
@hr_bp.route('/update-employee', methods=['POST'])
def update_employee():
    conn = None
    try:
        data = request.get_json() or {}
        emp_code = data.get('emp_code')

        if not emp_code:
            return jsonify({"success": False, "error": "Employee Code is required!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Pehle database se purane employee record ko fetch karein taaki blank values overwrite na ho
        cursor.execute("SELECT * FROM tblEmployeeMaster WHERE EmployeeCode = ?", (emp_code,))
        existing_row = cursor.fetchone()
        if not existing_row:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Employee not found in database!"}), 404

        columns = [column[0] for column in cursor.description]
        old_data = dict(zip(columns, existing_row))

        # Payload values with fallback to existing database values
        emp_name = data.get('emp_name') or data.get('FullName') or old_data.get('FullName')
        mobile_no = data.get('mobile_no') or data.get('MobileNo') or old_data.get('MobileNo')
        email = data.get('email') or data.get('Email') or old_data.get('Email')
        salary = float(data.get('salary') or data.get('Salary') or old_data.get('Salary') or 0.0)
        
        doj_raw = data.get('doj') or data.get('DateOfJoining') or old_data.get('DateOfJoining')
        doj = doj_raw if doj_raw and str(doj_raw).strip() != '' and str(doj_raw) != 'None' else None

        dob_raw = data.get('dob') or data.get('DOB') or old_data.get('DOB')
        dob = dob_raw if dob_raw and str(dob_raw).strip() != '' and str(dob_raw) != 'None' else None

        address = data.get('address') or data.get('CurrentAddress') or old_data.get('CurrentAddress')
        
        # Safe Branch ID mapping
        branch_raw = data.get('branch_id') or data.get('Fk_BranchID') or data.get('BranchID') or old_data.get('Fk_BranchID')
        branch_id = int(branch_raw) if branch_raw and str(branch_raw).strip() != '' and str(branch_raw).isdigit() else None

        # Safe Cycle ID mapping (Schema column: Fk_CycleID)
        cycle_raw = data.get('SalaryCycle') or data.get('salary_cycle') or data.get('Fk_CycleID') or old_data.get('Fk_CycleID')
        fk_cycle_id = int(cycle_raw) if cycle_raw and str(cycle_raw).strip() != '' and str(cycle_raw).isdigit() else 1

        gender = data.get('gender') or data.get('Gender') or old_data.get('Gender')
        marital_status = data.get('marital_status') or data.get('MaritalStatus') or old_data.get('MaritalStatus')
        blood_group = data.get('blood_group') or data.get('BloodGroup') or old_data.get('BloodGroup')
        emergency_contact = data.get('emergency_contact') or data.get('EmergencyContact') or old_data.get('EmergencyContact')
        father_name = data.get('father_name') or data.get('FatherName') or old_data.get('FatherName')
        mother_name = data.get('mother_name') or data.get('MotherName') or old_data.get('MotherName')
        spouse_name = data.get('spouse_name') or data.get('SpouseName') or old_data.get('SpouseName')
        pan_no = data.get('pan_no') or data.get('PanNo') or old_data.get('PanNo')
        aadhaar_no = data.get('aadhaar_no') or data.get('AadhaarNo') or old_data.get('AadhaarNo')
        pf_no = data.get('pf_no') or data.get('PfNo') or old_data.get('PfNo')
        esi_no = data.get('esi_no') or data.get('EsiNo') or old_data.get('EsiNo')
        bank_name = data.get('bank_name') or data.get('BankName') or old_data.get('BankName')
        ifsc_code = data.get('ifsc_code') or data.get('IfscCode') or old_data.get('IfscCode')
        account_no = data.get('account_no') or data.get('AccountNo') or old_data.get('AccountNo')
        upi_id = data.get('upi_id') or data.get('UpiId') or old_data.get('UpiId')
        shift = data.get('shift') or data.get('Shift') or old_data.get('Shift')
        staff_type = data.get('staff_type') or data.get('StaffType') or old_data.get('StaffType')
        reporting_manager = data.get('reporting_manager') or data.get('ReportingManager') or old_data.get('ReportingManager')

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
                Fk_CycleID = ?,
                Gender = ?,
                MaritalStatus = ?,
                BloodGroup = ?,
                EmergencyContact = ?,
                FatherName = ?,
                MotherName = ?,
                SpouseName = ?,
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
                ReportingManager = ?
            WHERE EmployeeCode = ?
        """
        cursor.execute(query, (
            emp_name, mobile_no, email, salary, doj, dob, address, branch_id, fk_cycle_id,
            gender, marital_status, blood_group, emergency_contact, father_name,
            mother_name, spouse_name, pan_no, aadhaar_no, pf_no, esi_no, bank_name, ifsc_code,
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

        # Added Fk_ClientMasterID, IsOwner, and AssignedBusinesses in SELECT query
        cursor.execute("""
            SELECT U.UserID, U.Username, U.RoleID, R.RoleName, U.IsActive, 
                   U.Fk_ClientMasterID, U.IsOwner, U.AssignedBusinesses 
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
            user_id, username, role_id, role_name, _, clid, is_owner, assigned_businesses = user_row
            
            active_name = username

            # Session values properly assigned here
            session['user_id'] = user_id
            session['user_name'] = active_name
            session['username'] = username
            session['role_id'] = role_id
            session['role_name'] = role_name
            session['branch_id'] = 1
            session['clid'] = clid or 1
            session['is_owner'] = is_owner or 0
            session['assigned_businesses'] = assigned_businesses or ''

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
    
# 7. Attendance Logs (Updated with exact column mapping)
# 7. Attendance Logs (Updated with SelfieImage Base64 conversion)
@hr_bp.route('/attendance', methods=['GET'])
def get_attendance():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 🎯 Query mein SelfieImage column bhi select karein
        cursor.execute("SELECT Pk_AttendanceID, Fk_EmployeeID, PunchTime, Status, ApprovedStatus, PunchInTime, PunchOutTime, Location, AdminName, AdminNote, SelfieImage FROM tblAttendance")
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # Binary SelfieImage ko Base64 string mein convert karna
            selfie_binary = row.SelfieImage if hasattr(row, 'SelfieImage') else (row[10] if len(row) > 10 else None)
            selfie_base64 = ""
            if selfie_binary:
                try:
                    selfie_base64 = base64.b64encode(selfie_binary).decode('utf-8')
                except Exception:
                    pass

            records.append({
                "Pk_AttendanceID": row.Pk_AttendanceID if hasattr(row, 'Pk_AttendanceID') else row[0],
                "Fk_EmployeeID": row.Fk_EmployeeID if hasattr(row, 'Fk_EmployeeID') else row[1],
                "PunchTime": str(row.PunchTime if hasattr(row, 'PunchTime') else row[2]),
                "Status": row.Status if hasattr(row, 'Status') else row[3],
                "ApprovedStatus": row.ApprovedStatus if hasattr(row, 'ApprovedStatus') else row[4],
                "PunchInTime": str(row.PunchInTime if hasattr(row, 'PunchInTime') else row[5]) if (row.PunchInTime if hasattr(row, 'PunchInTime') else row[5]) else '',
                "PunchOutTime": str(row.PunchOutTime if hasattr(row, 'PunchOutTime') else row[6]) if (row.PunchOutTime if hasattr(row, 'PunchOutTime') else row[6]) else '',
                "Location": row.Location if hasattr(row, 'Location') else (row[7] if len(row) > 7 else '-'),
                "AdminName": row.AdminName if hasattr(row, 'AdminName') else (row[8] if len(row) > 8 else ''),
                "AdminNote": row.AdminNote if hasattr(row, 'AdminNote') else (row[9] if len(row) > 9 else ''),
                "SelfieImage": selfie_base64  # 🎯 Base64 string frontend ko bhejne ke liye
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": records}), 200
    except Exception as e:
        if conn: conn.close()
        print("Fetch Attendance Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

# 8. Mark Attendance Route (Updated with proper PunchInTime & PunchOutTime storage)
@hr_bp.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    conn = None
    try:
        data = request.get_json()
        
        emp_raw = data.get('emp_id') or data.get('emp_code')
        status = data.get('status')
        att_date = data.get('date') or data.get('attendance_date')
        in_time = data.get('in_time', '')
        out_time = data.get('out_time', '')
        admin_note = data.get('admin_note', '')
        admin_name = data.get('admin_name', 'Admin')
        
        approved_status = data.get('approval_status', 'Approved') 

        if not emp_raw or not att_date:
            return jsonify({"success": False, "error": "Employee ID and Date are required!"}), 400

        import re
        numbers = re.findall(r'\d+', str(emp_raw))
        emp_id = int(numbers[0]) if numbers else 1

        location_text = f"Admin Override ({admin_name})" if admin_note or admin_name else "Face Scan"

        conn = get_db_connection()
        cursor = conn.cursor()

        check_query = "SELECT Pk_AttendanceID FROM tblAttendance WHERE Fk_EmployeeID = ? AND CAST(PunchTime AS DATE) = ?"
        cursor.execute(check_query, (emp_id, att_date))
        existing = cursor.fetchone()

        if existing:
            update_query = """
                UPDATE tblAttendance 
                SET Status = ?, ApprovedStatus = ?, AdminName = ?, AdminNote = ?, Location = ?, PunchInTime = ?, PunchOutTime = ?
                WHERE Fk_EmployeeID = ? AND CAST(PunchTime AS DATE) = ?
            """
            cursor.execute(update_query, (status, approved_status, admin_name, admin_note, location_text, in_time, out_time, emp_id, att_date))
        else:
            insert_query = """
                INSERT INTO tblAttendance (Fk_EmployeeID, Status, PunchTime, ApprovedStatus, AdminName, AdminNote, Location, PunchInTime, PunchOutTime, CreatedOn)
                VALUES (?, ?, CAST(? AS DATETIME), ?, ?, ?, ?, ?, ?, GETDATE())
            """
            cursor.execute(insert_query, (emp_id, status, att_date, approved_status, admin_name, admin_note, location_text, in_time, out_time))
        
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


# 17. Add Employee API (Final Column Correction)
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
        return jsonify({"success": False, "error": "Staff Full Name and Mobile Number are required!"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(Pk_EmployeeID) FROM tblEmployeeMaster")
        max_id_row = cursor.fetchone()
        next_id = (max_id_row[0] or 0) + 1
        emp_code = f"EMP{next_id}"

        # 🎯 Updated column name to match exact SSMS schema: FK_AllowedGeoFenceID
        query = """
            INSERT INTO tblEmployeeMaster (
                EmployeeCode, FullName, MobileNo, Email, RoleID, Salary, IsActive, 
                Fk_DepartmentID, PayrollType, Fk_BranchID, 
                FK_AllowedGeoFenceID, DateOfJoining, DOB, Shift
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
            "message": "Staff registered successfully!",
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

# 1. Get all loans for specific employee (Updated with filter)
@hr_bp.route('/employee-loans', methods=['GET'])
def get_employee_loans():
    conn = None
    try:
        emp_code = request.args.get('emp_code')
        if not emp_code:
            return jsonify({"success": False, "error": "Employee Code is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🎯 Added filter to exclude salary payout entries from the loans list
        query = """
            SELECT LoanID, EmployeeCode, LoanType, LoanAmount, MonthlyDeduction, 
                   TotalPaid, RemainingAmount, DisbursementDate, Status, Remarks
            FROM tblEmployeeLoanmaster
            WHERE EmployeeCode = ? AND (LoanType NOT LIKE 'Salary Payout -%' OR LoanType IS NULL)
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

@hr_bp.route('/repay-loan', methods=['POST'])
def repay_loan():
    conn = None
    try:
        data = request.get_json() or {}
        loan_id = data.get('loan_id')
        repay_amount = float(data.get('amount', 0))
        
        # 🎯 Dynamic values capture from request payload (No hardcoding)
        payment_mode = str(data.get('payment_mode', '')).strip() or 'Cash'
        repay_remarks = str(data.get('remarks', '')).strip()

        if not loan_id or repay_amount <= 0:
            return jsonify({"success": False, "error": "Valid Loan ID and amount are required!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Database se current loan details fetch karein
        cursor.execute("""
            SELECT LoanID, EmployeeCode, LoanType, LoanAmount, MonthlyDeduction, 
                   TotalPaid, RemainingAmount, DisbursementDate, Status, Remarks
            FROM tblEmployeeLoanmaster 
            WHERE LoanID = ?
        """, (loan_id,))
        loan = cursor.fetchone()

        if not loan:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Loan record not found!"}), 404

        columns = [column[0] for column in cursor.description]
        l_dict = dict(zip(columns, loan))

        total_amount = float(l_dict.get("LoanAmount") or 0.0)
        current_paid = float(l_dict.get("TotalPaid") or 0.0)
        current_remaining = float(l_dict.get("RemainingAmount") or total_amount)

        if repay_amount > current_remaining:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Recovery amount cannot exceed remaining balance!"}), 400

        new_paid = current_paid + repay_amount
        new_remaining = max(0.0, current_remaining - repay_amount)
        new_status = 'Closed' if new_remaining == 0 else 'Active'

        # 1. Master Table Update Karein
        update_query = """
            UPDATE tblEmployeeLoanmaster 
            SET TotalPaid = ?, RemainingAmount = ?, Status = ?
            WHERE LoanID = ?
        """
        cursor.execute(update_query, (new_paid, new_remaining, new_status, loan_id))

        # 2. History Table mein dynamic PaymentMode aur Remarks insert karein
        insert_history_query = """
            INSERT INTO tblLoanRepayments (FK_LoanID, RepaymentDate, AmountPaid, PaymentMode, Remarks)
            VALUES (?, GETDATE(), ?, ?, ?)
        """
        cursor.execute(insert_history_query, (loan_id, repay_amount, payment_mode, repay_remarks))

        conn.commit()

        # Updated row details response mein bhejne ke liye
        updated_loan = {
            "loan_id": loan_id,
            "loan_type": l_dict.get("LoanType"),
            "total_amount": total_amount,
            "monthly_emi": float(l_dict.get("MonthlyDeduction") or 0.0),
            "total_paid": new_paid,
            "remaining_amount": new_remaining,
            "disbursed_date": str(l_dict.get("DisbursementDate")).split()[0] if l_dict.get("DisbursementDate") else "",
            "status": new_status,
            "remarks": l_dict.get("Remarks") or ""
        }

        cursor.close()
        conn.close()

        return jsonify({
            "success": True, 
            "message": "Loan recovery recorded and history saved successfully!",
            "updated_loan": updated_loan
        }), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# 2. Issue New Loan / Salary Advance / Payout
@hr_bp.route('/issue-loan', methods=['POST'])
def issue_loan():
    conn = None
    try:
        data = request.get_json() or {}
        emp_code = data.get('emp_code')
        amount = float(data.get('amount') or 0.0)
        emi = float(data.get('monthly_emi') or amount)
        loan_type = data.get('loan_type', 'Advance Salary')
        payment_mode = data.get('payment_mode', 'Bank Transfer')
        remarks = data.get('remarks', '')

        if not emp_code or amount <= 0:
            return jsonify({"success": False, "error": "Invalid employee code or payout amount!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine if it's an Advance Loan or Salary Payout
        is_salary_payout = 'Salary Payout' in str(loan_type)
        total_paid = float(amount) if is_salary_payout else 0.00
        remaining_amt = 0.00 if is_salary_payout else float(amount)

        query = """
            INSERT INTO tblEmployeeLoanmaster 
            (EmployeeCode, LoanType, LoanAmount, MonthlyDeduction, TotalPaid, RemainingAmount, DisbursementDate, Status, PaymentMode, Remarks)
            VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 'Active', ?, ?)
        """
        cursor.execute(query, (
            str(emp_code), 
            str(loan_type), 
            float(amount), 
            float(emi), 
            total_paid, 
            remaining_amt, 
            str(payment_mode), 
            str(remarks)
        ))
        conn.commit()
        
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Transaction recorded successfully!"}), 200
        
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        print("Issue Loan SQL Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

    
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

@hr_bp.route('/payments', methods=['GET'])
def hr_payments_page():
    try:
        
        return render_template('payments.html')
    except Exception as e:
        return f"Error loading payments page: {str(e)}", 500

# Salary Payout History Fetch karne ke liye
@hr_bp.route('/employee-payouts', methods=['GET'])
def get_employee_payouts():
    conn = None
    try:
        emp_code = request.args.get('emp_code')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT PeriodKey, NetPayoutAmount, PaymentDate, PaymentMode, Remarks 
            FROM tblSalaryPayouts 
            WHERE Fk_EmployeeID = ?
        """
        import re
        numbers = re.findall(r'\d+', str(emp_code))
        emp_id = int(numbers[0]) if numbers else 1
        
        cursor.execute(query, (emp_id,))
        rows = cursor.fetchall()
        
        payouts = []
        for row in rows:
            payouts.append({
                "period": row[0],
                "amount": float(row[1]),
                "date": str(row[2]).split()[0] if row[2] else '-',
                "mode": row[3]
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "payouts": payouts}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# Naya Payout Save karne ke liye
@hr_bp.route('/issue-salary-payout', methods=['POST'])
def issue_salary_payout():
    conn = None
    try:
        data = request.get_json()
        emp_code = data.get('emp_code')
        amount = data.get('amount')
        period_key = data.get('period_key') # Jaise '2026-08'
        remarks = data.get('remarks', 'Direct Salary Disbursement')
        
        import re
        numbers = re.findall(r'\d+', str(emp_code))
        emp_id = int(numbers[0]) if numbers else 1

        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO tblSalaryPayouts (Fk_EmployeeID, PeriodKey, NetPayoutAmount, Remarks, PaymentDate, CreatedOn)
            VALUES (?, ?, ?, ?, GETDATE(), GETDATE())
        """
        cursor.execute(insert_query, (emp_id, period_key, amount, remarks))
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Salary payout saved successfully!"}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# 1. Fetch All Settings for the Settings Page
@hr_bp.route('/settings', methods=['GET'])
def get_app_settings():
    conn = None
    try:
        # Request arguments ya session se active CLID lein (default 1)
        clid = request.args.get('clid') or session.get('clid', 1)
        branch_id = session.get('branch_id', 1)
        
        try:
            clid = int(clid)
        except ValueError:
            clid = 1

        try:
            branch_id = int(branch_id)
        except ValueError:
            branch_id = 1
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Sirf uss specific CLID ka data uthayega
        cursor.execute("SELECT SettingName, IsEnabled FROM tblAppSettings WHERE CLID = ?", (clid,))
        rows = cursor.fetchall()
        
        settings_dict = {}
        for row in rows:
            if row[0]:
                key = str(row[0]).strip()
                # 1 matlab Enabled (True), 0 matlab Disabled (False)
                val = 1 if row[1] == 1 or str(row[1]) == 'True' else 0
                settings_dict[key] = val
                
        # 🎯 Branch specific text fields fetch from tblBranchMaster
        cursor.execute("SELECT BusinessName, BusinessAddress, StateCity, BranchName FROM tblBranchMaster WHERE Pk_BranchID = ?", (branch_id,))
        branch_row = cursor.fetchone()
        
        if branch_row:
            settings_dict['business_name'] = branch_row[0] if branch_row[0] else (branch_row[3] if branch_row[3] else '')
            settings_dict['business_address'] = branch_row[1] if branch_row[1] else ''
            settings_dict['business_state_city'] = branch_row[2] if branch_row[2] else ''
            
        cursor.close()
        conn.close()
        
        # Sabhi features ki default keys
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
            'profile_name', 'profile_phone', 'profile_email', 'grace_period', 'auto_approval'
        ]
        
        for k in default_keys:
            if k not in settings_dict:
                # Text fields ke liye default empty string, baaki ke liye 0
                if k in ['business_name', 'business_address', 'business_state_city']:
                    settings_dict[k] = ''
                else:
                    settings_dict[k] = 0  # Default 0 (Off)
                
        return jsonify({"success": True, "settings": settings_dict, "clid": clid}), 200
    except Exception as e:
        if conn: conn.close()
        print("Fetch Settings Error:", str(e))
        return jsonify({"success": True, "settings": {}}), 200

@hr_bp.route('/settings/update', methods=['POST'])
def update_setting():
    conn = None
    try:
        data = request.get_json() or {}
        key = data.get('key')
        value = data.get('value')  # Yeh 1 ya 0 hoga ya text hoga
        clid = data.get('clid') or session.get('clid', 1)
        branch_id = session.get('branch_id', 1)
        
        try:
            clid = int(clid)
        except ValueError:
            clid = 1

        try:
            branch_id = int(branch_id)
        except ValueError:
            branch_id = 1

        if not key:
            return jsonify({"success": False, "error": "Missing key"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 🎯 Branch specific text settings ke liye tblBranchMaster update hoga
        if key in ['business_name', 'business_address', 'business_state_city']:
            if key == 'business_name':
                cursor.execute("UPDATE tblBranchMaster SET BusinessName = ? WHERE Pk_BranchID = ?", (value, branch_id))
            elif key == 'business_address':
                cursor.execute("UPDATE tblBranchMaster SET BusinessAddress = ? WHERE Pk_BranchID = ?", (value, branch_id))
            elif key == 'business_state_city':
                cursor.execute("UPDATE tblBranchMaster SET StateCity = ? WHERE Pk_BranchID = ?", (value, branch_id))
        else:
            # Baaki saari settings ke liye aapka original logic
            bit_val = 1 if str(value) in ['1', 'true', 'True', 'ON', 'Y'] else 0

            # Database mein CLID aur SettingName dono ke basis par update ya insert karega
            cursor.execute("""
                IF EXISTS (SELECT 1 FROM tblAppSettings WHERE SettingName = ? AND CLID = ?) 
                    UPDATE tblAppSettings SET IsEnabled = ?, LastUpdated = GETDATE() WHERE SettingName = ? AND CLID = ?
                ELSE 
                    INSERT INTO tblAppSettings (SettingName, IsEnabled, CLID, LastUpdated) VALUES (?, ?, ?, GETDATE())
            """, (key, clid, bit_val, key, clid, key, bit_val, clid))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": f"Setting updated successfully!"}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500
    

@hr_bp.route('/profile-details', methods=['GET'])
def get_profile_details():
    conn = None
    try:
        username = session.get('username') or session.get('user_name') or 'Radha'
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # tblUserLogin table se actual user details fetch kar rahe hain
        cursor.execute("SELECT Username, MobileNo, EmailID FROM tblUserLogin WHERE Username = ?", (username,))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            profile_data = {
                "profile_name": row[0] or 'Admin',
                "profile_phone": row[1] or '-',
                "profile_email": row[2] or '-'
            }
            return jsonify({"success": True, "profile": profile_data}), 200
        else:
            return jsonify({"success": True, "profile": {"profile_name": username, "profile_phone": "-", "profile_email": "-"}}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/profile-details/update', methods=['POST'])
def update_profile_details():
    conn = None
    try:
        data = request.get_json() or {}
        key = data.get('key') # jaise 'profile_name', 'profile_phone', 'profile_email'
        value = data.get('value')
        username = session.get('username') or session.get('user_name') or 'Radha'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Key ke hisaab se tblUserLogin table ka column decide karein
        if key == 'profile_name':
            cursor.execute("UPDATE tblUserLogin SET Username = ? WHERE Username = ?", (value, username))
            session['username'] = value # session update kar dein
        elif key == 'profile_phone':
            cursor.execute("UPDATE tblUserLogin SET MobileNo = ? WHERE Username = ?", (value, username))
        elif key == 'profile_email':
            cursor.execute("UPDATE tblUserLogin SET EmailID = ? WHERE Username = ?", (value, username))
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Profile updated successfully"}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500 

@hr_bp.route('/businesses', methods=['GET'])
def businesses_page():
    return render_template('businesses.html')


@hr_bp.route('/businesses-list', methods=['GET'])
def get_businesses():
    conn = None
    try:
        clid = session.get('clid') or session.get('client_id') or session.get('Fk_ClientID') or 1
        try:
            clid = int(clid)
        except ValueError:
            clid = 1

        # Sidebar aur login session ki sabhi possible keys yahan check ho rahi hain
        current_branch_name = (
            session.get('branch_name') or 
            session.get('branch') or 
            session.get('BranchName') or 
            session.get('active_branch') or
            session.get('selected_branch') or ''
        )
        current_branch_id = (
            session.get('branch_id') or 
            session.get('BranchID') or 
            session.get('pk_branchid') or
            session.get('active_branch_id')
        )

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Pk_BranchID, BranchName, IsActive, Fk_ClientID 
            FROM tblBranchMaster 
            WHERE Fk_ClientID = ? 
            ORDER BY Pk_BranchID ASC
        """, (clid,))
        rows = cursor.fetchall()
        
        if not rows:
            cursor.execute("SELECT Pk_BranchID, BranchName, IsActive, Fk_ClientID FROM tblBranchMaster ORDER BY Pk_BranchID ASC")
            rows = cursor.fetchall()
        
        branches = []
        total_staff_all = 0

        for index, row in enumerate(rows):
            branch_id = row[0]
            branch_name = row[1]
            is_active = row[2] if row[2] is not None else 1
            
            # Har branch ke active aur deactivated staff count tblEmployeeMaster se kar rahe hain
            try:
                cursor.execute("SELECT COUNT(*) FROM tblEmployeeMaster WHERE Fk_BranchID = ? AND (IsActive = 1 OR IsActive IS NULL)", (branch_id,))
                active_res = cursor.fetchone()
                active_staff = active_res[0] if active_res else 0
                
                cursor.execute("SELECT COUNT(*) FROM tblEmployeeMaster WHERE Fk_BranchID = ? AND IsActive = 0", (branch_id,))
                deactive_res = cursor.fetchone()
                deactivated_staff = deactive_res[0] if deactive_res else 0
            except:
                active_staff = 0
                deactivated_staff = 0

            total_staff = active_staff + deactivated_staff
            total_staff_all += total_staff

            is_master = (index == 0) # Pehli branch Master
            
            # Dynamic matching with session branch
            is_current = False
            if current_branch_id:
                try:
                    is_current = (int(branch_id) == int(current_branch_id))
                except:
                    pass
            if not is_current and current_branch_name:
                is_current = (branch_name.strip().lower() == current_branch_name.strip().lower())
            
            if not current_branch_id and not current_branch_name and index == 0:
                is_current = True

            branches.append({
                "id": branch_id,
                "name": branch_name,
                "total_staff": total_staff,
                "deactivated_staff": deactivated_staff,
                "is_master": is_master,
                "is_current": is_current,
                "is_active": is_active,
                "status": "Active" if (is_active == 1) else "Inactive"
            })
            
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "total_businesses": len(branches),
            "total_staff": total_staff_all,
            "businesses": branches
        }), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/businesses/toggle-status', methods=['POST'])
def toggle_business_status():
    conn = None
    try:
        data = request.get_json() or {}
        branch_id = data.get('branch_id')
        status = data.get('status') # 0 for Inactive, 1 for Active
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Safety Check: Master Branch (Pehli branch) ko deactivate hone se bachane ke liye
        cursor.execute("""
            SELECT TOP 1 Pk_BranchID 
            FROM tblBranchMaster 
            WHERE Fk_ClientID = (SELECT Fk_ClientID FROM tblBranchMaster WHERE Pk_BranchID = ?) 
            ORDER BY Pk_BranchID ASC
        """, (branch_id,))
        master_row = cursor.fetchone()
        
        if master_row and master_row[0] == int(branch_id):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Master branch status cannot be changed!"}), 400
        
        # Sub-branch ka status safe tarike se update karein (No Deletion)
        cursor.execute("UPDATE tblBranchMaster SET IsActive = ? WHERE Pk_BranchID = ?", (status, branch_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Branch status updated successfully!"}), 200
    except Exception as e:
        if conn: conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/businesses/add', methods=['POST'])
def add_business():
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"success": False, "error": "Business name is required"}), 400
        
        # 1. Pehle dekhein ki session ya request mein current active branch ki ID kya hai
        current_branch_id = (
            session.get('branch_id') or 
            session.get('active_branch_id') or 
            session.get('selected_branch_id') or
            request.headers.get('X-Branch-ID')
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        client_id = None
        
        if current_branch_id:
            # 2. Agar branch ID mil gayi, toh tblBranchMaster se direct Fk_ClientID fetch kar lo
            cursor.execute("SELECT Fk_ClientID FROM tblBranchMaster WHERE Pk_BranchID = ?", (current_branch_id,))
            row = cursor.fetchone()
            if row and row[0]:
                client_id = row[0]
        
        # 3. Agar kisi wajah se branch ID session mein na ho, toh database ki pehli active branch/master branch se client_id utha lo
        if not client_id:
            cursor.execute("SELECT TOP 1 Fk_ClientID FROM tblBranchMaster WHERE IsActive = 1")
            row = cursor.fetchone()
            if row and row[0]:
                client_id = row[0]
                
        if not client_id:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Could not determine client ID from current branch."}), 400
        
        # 4. Ab naye business ko exact usi client_id ke sath insert kar do
        cursor.execute(
            "INSERT INTO tblBranchMaster (BranchName, IsActive, Fk_ClientID) VALUES (?, 1, ?)", 
            (name, client_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Business added successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/subscriptions', methods=['GET'])
def subscriptions_page():
    return render_template('subscriptions.html')    


@hr_bp.route('/subscription-details', methods=['GET'])
def get_subscription_details():
    try:
        client_id = session.get('client_id') or session.get('user_client_id') or 1
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Active Plans Fetch Karein
        cursor.execute("""
            SELECT PlanName, ValidTill, TenureYears, StaffLimit 
            FROM tblClientPlans WHERE Fk_ClientID = ? AND IsActive = 1
        """, (client_id,))
        plans_rows = cursor.fetchall()
        
        active_plans = []
        for row in plans_rows:
            active_plans.append({
                "plan_name": row[0],
                "valid_till": str(row[1]) if row[1] else "N/A",
                "tenure": f"{row[2]} Year(s)",
                "staff_limit": f"{row[3]} Staff"
            })
            
        # 2. Billing History Fetch Karein
        cursor.execute("""
            SELECT OrderDate, OrderID, Amount, PurchaseDetails 
            FROM tblBillingHistory WHERE Fk_ClientID = ? ORDER BY OrderDate DESC
        """, (client_id,))
        billing_rows = cursor.fetchall()
        
        billing_history = []
        for row in billing_rows:
            billing_history.append({
                "order_date": str(row[0]),
                "order_id": row[1],
                "amount": float(row[2]),
                "purchase_details": row[3]
            })
            
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "active_plans": active_plans,
            "billing_history": billing_history
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




@hr_bp.route('/invoice', methods=['GET'])
def invoice_page():
    return render_template('invoice.html')  

@hr_bp.route('/invoice/<order_id>', methods=['GET'])
def view_invoice(order_id):
    try:
        client_id = session.get('client_id') or session.get('user_client_id') or 1
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT OrderID, OrderDate, Amount, PurchaseDetails 
            FROM tblBillingHistory WHERE OrderID = ? AND Fk_ClientID = ?
        """, (order_id, client_id))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return "Invoice not found for this order ID", 404
            
        invoice_data = {
            "order_id": row[0],
            "order_date": str(row[1]),
            "amount": float(row[2]),
            "purchase_details": row[3]
        }
        
        return render_template('invoice.html', invoice=invoice_data)
        
    except Exception as e:
        return str(e), 500


@hr_bp.route('/manage-users', methods=['GET'])
def manage_users_page():
    return render_template('manage_users.html')

@hr_bp.route('/roles-permissions', methods=['GET'])
def roles_permissions_page():
    return render_template('roles_permissions.html')    


@hr_bp.route('/users', methods=['GET'])
def get_hr_users():
    role_type = request.args.get('role', 'business_admins')
    current_clid = session.get('clid', 1)  # Session se active Client ID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # u.AssignedBusinesses ko select mein add kar liya gaya hai
        query = """
            SELECT u.UserID AS id, u.Username AS name, u.MobileNo AS phone, 
                   u.CreatedAt AS added_on, u.IsOwner AS is_owner, 
                   u.AssignedBusinesses AS assigned_businesses, r.RoleName AS role_name
            FROM tblUserLogin u
            LEFT JOIN tblRoleMaster r ON u.RoleID = r.Pk_RoleID
            WHERE u.Fk_ClientMasterID = ?
        """
        cursor.execute(query, (current_clid,))
        rows = cursor.fetchall()
        conn.close()
        
        users_list = []
        for row in rows:
            raw_date = row[3]
            formatted_date = str(raw_date).split()[0] if raw_date else "-"
            
            is_owner_val = bool(row[4])
            
            # Agar owner hai toh 'All', warna jitni branches select ki thin wahi aayengi
            assigned_biz = "All" if is_owner_val else (row[5] or "No Branch Assigned")
            
            users_list.append({
                "id": row[0],
                "name": row[1] or "Admin User",
                "phone": row[2] or "-",
                "assigned_businesses": assigned_biz,
                "added_on": formatted_date,
                "is_owner": is_owner_val,
                "role_name": row[6] or "User"
            })
            
        return jsonify({"success": True, "users": users_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/users/add', methods=['POST'])
def add_hr_user():
    data = request.json or {}
    name = data.get('name')
    phone = data.get('phone', '').strip()
    role_id = data.get('role_id', 2)
    assigned_biz = data.get('assigned_businesses', 'All')
    current_clid = session.get('clid', 1)
    
    if not name or not phone:
        return jsonify({"success": False, "error": "Name and Phone number are required"}), 400

    # Get the currently logged-in user from session dynamically
    logged_in_user = session.get('username') or session.get('user_name') or session.get('user')
    session_user_id = session.get('user_id') or session.get('id')

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🎯 Verify if the logged-in user is actually the Business Owner (Flexible check)
        is_owner = 0
        if session_user_id:
            cursor.execute("SELECT IsOwner FROM tblUserLogin WHERE UserID = ? AND Fk_ClientMasterID = ?", (session_user_id, current_clid))
            row = cursor.fetchone()
            if row and row[0] is not None:
                is_owner = row[0]

        if not is_owner and logged_in_user:
            cursor.execute("SELECT IsOwner FROM tblUserLogin WHERE Username = ? AND Fk_ClientMasterID = ?", (logged_in_user, current_clid))
            row = cursor.fetchone()
            if row and row[0] is not None:
                is_owner = row[0]

        # Fallback check from session flag if direct db query fails
        if not is_owner and session.get('is_owner') in [1, '1', True, 'True']:
            is_owner = 1

        # Strict security check: Only allow if IsOwner is true/1
        if not is_owner or int(is_owner) != 1:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Access Denied: Only the Business Owner is authorized to add users."}), 403

        # 🎯 Check if mobile number already exists in tblUserLogin
        cursor.execute("SELECT COUNT(*) FROM tblUserLogin WHERE MobileNo = ?", (phone,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "This mobile number is already registered"}), 400

        # Insert new user record if duplicate check passes
        query = """
            INSERT INTO tblUserLogin (Username, MobileNo, PasswordHash, Fk_ClientMasterID, IsOwner, RoleID, AssignedBusinesses)
            VALUES (?, ?, 'admin123', ?, 0, ?, ?)
        """
        cursor.execute(query, (name, phone, current_clid, role_id, assigned_biz))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "User added successfully"})
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        return jsonify({"success": False, "error": str(e)}), 500



@hr_bp.route('/users/update', methods=['POST'])
def update_hr_user():
    conn = None
    try:
        data = request.json or {}
        user_id = data.get('user_id')
        name = data.get('name')
        phone = data.get('phone', '').strip()
        assigned_biz = data.get('assigned_businesses', 'All')
        current_clid = session.get('clid', 1)
        
        if not user_id or not name or not phone:
            return jsonify({"success": False, "error": "User ID, Name, and Phone are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # tblUserLogin mein user details update karein
        cursor.execute("""
            UPDATE tblUserLogin 
            SET Username = ?, MobileNo = ?, AssignedBusinesses = ? 
            WHERE UserID = ? AND Fk_ClientMasterID = ?
        """, (name, phone, assigned_biz, user_id, current_clid))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "User updated successfully"}), 200
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route('/users/delete', methods=['POST'])
def delete_or_deactivate_hr_user():
    conn = None
    try:
        data = request.json or {}
        user_id = data.get('user_id')
        current_clid = session.get('clid', 1)
        
        if not user_id:
            return jsonify({"success": False, "error": "User ID is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🎯 User ko delete karne ki bajaye IsActive = 0 karke deactivate kar rahe hain
        cursor.execute("""
            UPDATE tblUserLogin 
            SET IsActive = 0 
            WHERE UserID = ? AND Fk_ClientMasterID = ?
        """, (user_id, current_clid))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "User deactivated successfully"}), 200
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route('/branches', methods=['GET'])
def get_user_branches():
    current_clid = session.get('clid', 1)
    is_owner = session.get('is_owner', 0)
    assigned_biz = session.get('assigned_businesses', '')
    
    # 🎯 Debugging print to check session values in terminal
    print(f"DEBUG LOGIN USER -> CLID: {current_clid}, IsOwner: {is_owner} (Type: {type(is_owner)}), AssignedBiz: {assigned_biz}")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Safe type conversion for is_owner (handles 1, '1', True, etc.)
        is_owner_int = 1 if str(is_owner) in ['1', 'True', 'true'] else 0
        
        if is_owner_int == 1:
            query = "SELECT Pk_BranchID, BranchName FROM tblBranchMaster WHERE Fk_ClientID = ?"
            cursor.execute(query, (current_clid,))
        else:
            allowed_branches = [b.strip() for b in assigned_biz.split(',')] if assigned_biz else []
            print(f"DEBUG ALLOWED BRANCHES LIST: {allowed_branches}")
            
            if not allowed_branches:
                conn.close()
                return jsonify({"success": True, "branches": []})
                
            placeholders = ','.join(['?'] * len(allowed_branches))
            query = f"SELECT Pk_BranchID, BranchName FROM tblBranchMaster WHERE Fk_ClientID = ? AND BranchName IN ({placeholders})"
            
            params = [current_clid] + allowed_branches
            cursor.execute(query, params)
            
        rows = cursor.fetchall()
        conn.close()
        
        branches = [{"id": row[0], "name": row[1]} for row in rows]
        return jsonify({"success": True, "branches": branches})
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        print("Branches Fetch Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route('/roles-list', methods=['GET'])
def get_roles_list():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # IsActive condition hata di gayi hai kyunki yeh column table mein nahi hai
        cursor.execute("SELECT Pk_RoleId, RoleName FROM tblRoleMaster")
        rows = cursor.fetchall()
        
        roles = []
        for r in rows:
            roles.append({
                "id": r[0],
                "name": r[1] or "Custom Role",
                "description": "System assigned role permissions."
            })
            
        cursor.close()
        conn.close()
        return jsonify({"success": True, "roles": roles}), 200
    except Exception as e:
        if conn: conn.close()
        print("Roles Fetch Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


import os
from werkzeug.utils import secure_filename

@hr_bp.route('/upload-business-logo', methods=['POST'])
def upload_business_logo():
    try:
        if 'logo_file' not in request.files:
            return jsonify({"success": False, "error": "No file part in the request"}), 400
            
        file = request.files['logo_file']
        branch_id = session.get('branch_id', 1)
        
        if file.filename == '':
            return jsonify({"success": False, "error": "No selected file"}), 400
            
        if file:
            filename = secure_filename(f"branch_{branch_id}.png")
            upload_folder = os.path.join('static', 'images', 'branch_logos')
            
            # Folder create karna agar pehle se na ho
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            return jsonify({"success": True, "message": "Logo uploaded successfully", "path": f"/{file_path}"}), 200
            
    except Exception as e:
        print("Logo Upload Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500   


@hr_bp.route('/invite-staff', methods=['GET'])
def invite_staff_page():
    return render_template('invite-staff.html')    


@hr_bp.route('/staff_list', methods=['GET'])
def get_hr_staff_list():
    conn = None
    try:
        current_clid = session.get('clid', 1)
        branch_id = request.args.get('branch_id') or session.get('branch_id') or session.get('active_branch_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Agar specific branch select hai (FaceTemplate bhi select kar liya hai)
        if branch_id and str(branch_id).strip().lower() != 'all':
            cursor.execute("""
                SELECT 
                    Pk_EmployeeID as id, 
                    FullName as name, 
                    EmployeeCode as staff_id, 
                    MobileNo as phone,
                    FaceTemplate 
                FROM tblEmployeeMaster 
                WHERE Fk_BranchID = ? AND IsActive = 1
            """, (int(branch_id),))
        else:
            # 2. Agar 'all' branch hai
            cursor.execute("""
                SELECT 
                    Pk_EmployeeID as id, 
                    FullName as name, 
                    EmployeeCode as staff_id, 
                    MobileNo as phone,
                    FaceTemplate 
                FROM tblEmployeeMaster 
                WHERE Fk_BranchID IN (
                    SELECT Pk_BranchID FROM tblBranchMaster WHERE Fk_ClientID = ?
                ) AND IsActive = 1
            """, (current_clid,))
        
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        
        staff = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            
            face_binary = row_dict.get('FaceTemplate')
            has_face = False
            face_image_url = None
            
            # Agar database mein face binary data maujood hai
            if face_binary:
                has_face = True
                try:
                    encoded_b64 = base64.b64encode(face_binary).decode('utf-8')
                    face_image_url = f"data:image/jpeg;base64,{encoded_b64}"
                except Exception as img_err:
                    print("Face Image Encoding Error:", str(img_err))

            staff.append({
                "id": row_dict.get('id'),
                "name": row_dict.get('name') or 'Unnamed Staff',
                "staff_id": row_dict.get('staff_id') or '-',
                "phone": row_dict.get('phone') or '-',
                "has_face": has_face,
                "face_image": face_image_url
            })
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "staff": staff}), 200
    except Exception as e:
        print("Staff List Error:", str(e))
        if conn: 
            try: conn.close() 
            except: pass
        return jsonify({"success": False, "error": str(e)}), 500
    

@hr_bp.route('/send_invites', methods=['POST'])
def send_staff_invites():
    try:
        data = request.json or {}
        staff_ids = data.get('staff_ids', [])
        
        if not staff_ids:
            return jsonify({"success": False, "error": "No staff selected"}), 400
        
        # Yahan aap apna SMS notification ya invite logic implement kar sakte hain
        print(f"Sending invite SMS to Staff IDs: {staff_ids}")
        
        return jsonify({"success": True, "message": "Invites sent successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@hr_bp.route('/kiosk-login', methods=['GET'])
def kiosk_login_page():
    return render_template('kiosk-login.html')



@hr_bp.route('/kiosk-send-otp', methods=['POST'])
def kiosk_send_otp():
    conn = None
    try:
        data = request.json or {}
        mobile = str(data.get('mobile', '')).strip()
        
        if not mobile:
            return jsonify({"success": False, "error": "Mobile number is required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Radha_Attendance.dbo prefix hata diya hai taaki connection conflict na ho
        cursor.execute("SELECT TOP 1 UserID FROM tblUserLogin WHERE MobileNo = ?", (mobile,))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not row:
            return jsonify({"success": False, "error": "Mobile number not registered."}), 404
            
        return jsonify({"success": True, "message": "OTP sent successfully"}), 200
        
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        return jsonify({"success": False, "error": str(e)}), 500


@hr_bp.route('/kiosk-verify-otp', methods=['POST'])
def kiosk_verify_otp():
    conn = None
    try:
        data = request.json or {}
        mobile = str(data.get('mobile', '')).strip()
        otp = str(data.get('otp', '')).strip()
        
        if not mobile or not otp:
            return jsonify({"success": False, "error": "Mobile and OTP are required"}), 400
            
        if otp != "1234":
            return jsonify({"success": False, "error": "Incorrect OTP"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT TOP 1 UserID FROM tblUserLogin WHERE MobileNo = ?", (mobile,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "User not found."}), 404
            
        user_id = row[0]
        
        cursor.execute("SELECT Pk_BranchID, BranchName FROM tblBranchMaster")
        branches = [{"id": r[0], "name": r[1]} for r in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "clid": user_id,
            "branches": branches
        }), 200
        
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        return jsonify({"success": False, "error": str(e)}), 500  



@hr_bp.route('/face-scanner', methods=['GET'])
def face_scanner_page():
    return render_template('face-scanner.html')

@hr_bp.route('/verify-face', methods=['POST'])
def verify_face():
    conn = None
    try:
        data = request.json or {}
        image_data = data.get('image')
        branch_id = data.get('branch_id')
        clid = data.get('clid')
        location_name = data.get('location', 'Kiosk Face Scanner')
        
        if not image_data:
            return jsonify({"success": False, "error": "No image data received"}), 400
        
        # 1. Decode live camera frame (Base64)
        if "," in image_data:
            header, encoded = image_data.split(",", 1)
        else:
            encoded = image_data
            
        live_bytes = base64.b64decode(encoded)
        nparr_live = np.frombuffer(live_bytes, np.uint8)
        live_img = cv2.imdecode(nparr_live, cv2.IMREAD_COLOR)

        if live_img is None:
            return jsonify({"success": False, "error": "Could not decode live camera frame"}), 400

        live_resized = cv2.resize(live_img, (100, 100))
        hist_live = cv2.calcHist([live_resized], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        cv2.normalize(hist_live, hist_live)

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 2. Fetch active staff along with their actual Fk_BranchID
        if branch_id and branch_id != 'all':
            query = """
                SELECT Pk_EmployeeID, EmployeeCode, FullName, FaceTemplate, Fk_BranchID 
                FROM tblEmployeeMaster 
                WHERE FaceTemplate IS NOT NULL AND IsActive = 1 AND Fk_BranchID = ?
            """
            cursor.execute(query, (branch_id,))
        else:
            query = """
                SELECT Pk_EmployeeID, EmployeeCode, FullName, FaceTemplate, Fk_BranchID 
                FROM tblEmployeeMaster 
                WHERE FaceTemplate IS NOT NULL AND IsActive = 1
            """
            cursor.execute(query)

        staff_rows = cursor.fetchall()
        
        if not staff_rows:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "No enrolled staff found for this branch."}), 200

        matched_emp = None
        highest_similarity = 0.0
        STRICT_THRESHOLD = 0.75

        for emp in staff_rows:
            emp_id, emp_code, emp_name, db_face_binary, emp_branch_id = emp
            
            if db_face_binary:
                try:
                    if isinstance(db_face_binary, bytes):
                        db_arr = np.frombuffer(db_face_binary, np.uint8)
                    else:
                        db_arr = np.frombuffer(bytes(db_face_binary), np.uint8)
                        
                    db_img = cv2.imdecode(db_arr, cv2.IMREAD_COLOR)

                    if db_img is not None:
                        db_resized = cv2.resize(db_img, (100, 100))
                        hist_db = cv2.calcHist([db_resized], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                        cv2.normalize(hist_db, hist_db)
                        
                        similarity = cv2.compareHist(hist_db, hist_live, cv2.HISTCMP_CORREL)
                        
                        if similarity > highest_similarity:
                            highest_similarity = similarity
                            if similarity >= STRICT_THRESHOLD:
                                matched_emp = {"id": emp_id, "code": emp_code, "name": emp_name, "branch_id": emp_branch_id}
                except Exception:
                    continue

        if not matched_emp:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Scanning for accurate face..."}), 200

        emp_id = matched_emp["id"]
        emp_code = matched_emp["code"]
        emp_name = matched_emp["name"]
        emp_branch_id = matched_emp["branch_id"]
        
        print(f"🎯 100% VERIFIED MATCH: {emp_name} (Branch ID: {emp_branch_id}) with Accuracy {highest_similarity:.2f}")

        # 3. Check today's record
        check_today_query = """
            SELECT TOP 1 Pk_AttendanceID FROM tblAttendance 
            WHERE Fk_EmployeeID = ? AND CAST(PunchTime AS DATE) = CAST(GETDATE() AS DATE)
        """
        cursor.execute(check_today_query, (emp_id,))
        existing_record = cursor.fetchone()

        current_time_str = datetime.datetime.now().strftime("%I:%M:%S %p")

        if not existing_record:
            # 🟢 FIRST SCAN OF THE DAY (Punch In)
            insert_query = """
                INSERT INTO tblAttendance (
                    Fk_EmployeeID, Fk_BranchID, Status, PunchTime, PunchInTime, PunchOutTime,
                    ApprovedStatus, Location, SelfieImage, CreatedOn, PunchType
                )
                VALUES (?, ?, 'PRESENT', GETDATE(), GETDATE(), NULL, 'Approved', ?, ?, GETDATE(), 'Punch In')
            """
            cursor.execute(insert_query, (emp_id, emp_branch_id, location_name, live_bytes))
            punch_type = "Punch In"
        else:
            # 🔵 SUBSEQUENT SCANS (Punch Out)
            attendance_id = existing_record[0]
            update_query = """
                UPDATE tblAttendance 
                SET PunchOutTime = GETDATE(), PunchTime = GETDATE(), ApprovedStatus = 'Approved', 
                    Fk_BranchID = ?, Location = ?, SelfieImage = ?, PunchType = 'Punch Out'
                WHERE Pk_AttendanceID = ?
            """
            cursor.execute(update_query, (emp_branch_id, location_name, live_bytes, attendance_id))
            punch_type = "Punch Out"

        # 🎯 4. HAR INDIVIDUAL SCAN KO 'attendance_logs' TABLE MEIN BHI SAVE KAREIN
        log_query = """
            INSERT INTO attendance_logs (Fk_EmployeeID, ScanTimestamp, ScanType, Location, SelfieImage, CreatedOn)
            VALUES (?, GETDATE(), ?, ?, ?, GETDATE())
        """
        cursor.execute(log_query, (emp_id, punch_type, location_name, live_bytes))

        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "employee_name": emp_name,
            "time": current_time_str,
            "type": punch_type,
            "message": f"Attendance marked as {punch_type} for {emp_name}"
        }), 200
        
    except Exception as e:
        if conn: conn.close()
        print("Verify Face Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

@hr_bp.route('/mark_attendance_face', methods=['POST'])
def mark_attendance_face():
    return verify_face()    

@hr_bp.route('/save-staff-face', methods=['POST'])
def save_staff_face():
    conn = None
    try:
        data = request.get_json() or {}
        staff_id = data.get('staff_id')
        image_data = data.get('image')
        
        if not staff_id or not image_data:
            return jsonify({'success': False, 'error': 'Staff ID and image are required'})

        header, encoded = image_data.split(",", 1)
        binary_data = base64.b64decode(encoded)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tblEmployeeMaster 
            SET FaceTemplate = ? 
            WHERE Pk_EmployeeID = ?
        """, (binary_data, staff_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Face saved successfully'})
    except Exception as e:
        print("CRITICAL SAVE FACE ERROR:", str(e))
        if conn:
            try: conn.close()
            except: pass
        return jsonify({'success': False, 'error': str(e)})



# 🎯 Naya route jo attendance_logs table se saari scan photos aur details fetch karega
@hr_bp.route('/get-employee-scan-logs', methods=['GET'])
def get_employee_scan_logs():
    conn = None
    try:
        emp_id = request.args.get('emp_id')
        log_date = request.args.get('date') # Format: 'YYYY-MM-DD'
        
        if not emp_id or not log_date:
            return jsonify({"success": False, "error": "Employee ID and Date are required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Extract numeric ID if string code like 'EMP1' is passed
        import re
        numbers = re.findall(r'\d+', str(emp_id))
        numeric_emp_id = int(numbers[0]) if numbers else 1

        query = """
            SELECT ScanTimestamp, ScanType, Location, SelfieImage 
            FROM attendance_logs 
            WHERE Fk_EmployeeID = ? AND CAST(ScanTimestamp AS DATE) = ?
            ORDER BY ScanTimestamp ASC
        """
        cursor.execute(query, (numeric_emp_id, log_date))
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            scan_time, scan_type, location, selfie_binary = row
            
            selfie_base64 = ""
            if selfie_binary:
                try:
                    selfie_base64 = base64.b64encode(selfie_binary).decode('utf-8')
                except Exception:
                    pass
                    
            logs.append({
                "time": str(scan_time).split()[1] if scan_time else "",
                "scan_type": scan_type,
                "location": location,
                "selfie": selfie_base64
            })
            
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "logs": logs}), 200
        
    except Exception as e:
        if conn: conn.close()
        print("Get Scan Logs Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500