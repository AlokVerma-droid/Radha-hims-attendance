from flask import Blueprint, jsonify
from get_db_connection import get_db_connection# <-- 'db' ko 'db_config' se replace kar diya hai

master_bp = Blueprint('master_bp', __name__)

# 1. Departments List (tblassetdeptmaster)
@master_bp.route('/departments', methods=['GET'])
def get_departments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT PK_Dept_Id, Dept_Name FROM tblassetdeptmaster WHERE Is_Active = 1"
        cursor.execute(query)
        rows = cursor.fetchall()

        departments = []
        for row in rows:
            departments.append({
                "dept_id": row.PK_Dept_Id,
                "dept_name": row.Dept_Name
            })

        cursor.close()
        conn.close()
        return jsonify({"departments": departments}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 2. Status List (tblassetstatusmaster)
@master_bp.route('/statuses', methods=['GET'])
def get_statuses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT PK_Status_Id, Status_Name FROM tblassetstatusmaster WHERE Is_Active = 1"
        cursor.execute(query)
        rows = cursor.fetchall()

        statuses = []
        for row in rows:
            statuses.append({
                "status_id": row.PK_Status_Id,
                "status_name": row.Status_Name
            })

        cursor.close()
        conn.close()
        return jsonify({"statuses": statuses}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500