from get_db_connection import get_db_connection
from flask import Blueprint, request, jsonify

asset_bp = Blueprint('asset_bp', __name__)

# 1. Naya Asset add karne ke liye
@asset_bp.route('/add', methods=['POST'])
def add_asset():
    data = request.get_json()

    # Required fields validation
    required_fields = ['asset_id', 'asset_name', 'category', 'department_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Dynamic mapping for tblAssetsmaster
        query = """
            INSERT INTO tblAssetsmaster (PK_Asset_id, Asset_name, Category, Department_id, Cost, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            str(data.get('asset_id')),
            str(data.get('asset_name')),
            str(data.get('category')),
            str(data.get('department_id')),
            float(data.get('cost', 0.0)),
            str(data.get('status', 'In Use'))
        )

        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Asset successfully registered!",
            "asset_id": data.get('asset_id')
        }), 201

    except Exception as e:
        error_msg = str(e)
        if "FOREIGN KEY" in error_msg:
            return jsonify({"error": f"Department ID '{data.get('department_id')}' database mein nahi mila."}), 400
        return jsonify({"error": error_msg}), 500


# 2. Saare Assets ki list dekhne ke liye
@asset_bp.route('/', methods=['GET'])
def get_all_assets():
    status_filter = request.args.get('status')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if status_filter:
            query = "SELECT PK_Asset_id, Asset_name, Category, Department_id, Cost, status FROM tblAssetsmaster WHERE status = ?"
            cursor.execute(query, (status_filter,))
        else:
            query = "SELECT PK_Asset_id, Asset_name, Category, Department_id, Cost, status FROM tblAssetsmaster"
            cursor.execute(query)
            
        rows = cursor.fetchall()

        assets = []
        for row in rows:
            assets.append({
                "asset_id": row.PK_Asset_id,
                "asset_name": row.Asset_name,
                "category": row.Category,
                "department_id": row.Department_id,
                "cost": float(row.Cost) if row.Cost else 0.0,
                "status": row.status
            })

        cursor.close()
        conn.close()

        return jsonify({"count": len(assets), "assets": assets}), 200
        
    except Exception as e:
         return jsonify({"error": str(e)}), 500


# 3. Particular Asset detail ID se search karne ke liye
@asset_bp.route('/<string:asset_id>', methods=['GET'])
def get_asset_by_id(asset_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT PK_Asset_id, Asset_name, Category, Department_id, Cost, status FROM tblAssetsmaster WHERE PK_Asset_id = ?"
        cursor.execute(query, (asset_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Asset not found"}), 404

        asset = {
            "asset_id": row.PK_Asset_id,
            "asset_name": row.Asset_name,
            "category": row.Category,
            "department_id": row.Department_id,
            "cost": float(row.Cost) if row.Cost else 0.0,
            "status": row.status
        }
        
        cursor.close()
        conn.close()

        return jsonify({"asset": asset}), 200

    except Exception as e:
         return jsonify({"error": str(e)}), 500


# 4. Asset ka status update karne ke liye
@asset_bp.route('/update_status/<string:asset_id>', methods=['PUT'])
def update_asset_status(asset_id):
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({"error": "Please provide new status"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if asset exists
        cursor.execute("SELECT PK_Asset_id FROM tblAssetsmaster WHERE PK_Asset_id = ?", (asset_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Asset not found"}), 404

        # Update status
        update_query = "UPDATE tblAssetsmaster SET status = ? WHERE PK_Asset_id = ?"
        cursor.execute(update_query, (new_status, asset_id))
        conn.commit()
        
        cursor.close()
        conn.close()

        return jsonify({
            "message": f"Asset {asset_id} status updated to '{new_status}'"
        }), 200

    except Exception as e:
         return jsonify({"error": str(e)}), 500


# 5. Asset ko Maintenance me dalna (No changes needed)
@asset_bp.route('/maintenance/log', methods=['POST'])
def log_maintenance():
    # ... (Aapka existing code bilkul sahi hai) ...
    pass # Yahan aapna code hi rakhein


# 6. Asset Transfer (No changes needed)
@asset_bp.route('/transfer', methods=['PUT'])
def transfer_asset():
    # ... (Aapka existing code bilkul sahi hai) ...
    pass # Yahan aapna code hi rakhein


# 7. Dashboard Metrics Summary (No changes needed)
@asset_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    # ... (Aapka existing code bilkul sahi hai) ...
    pass # Yahan aapna code hi rakhein