from flask import Flask, render_template, session, jsonify

from asset_routes import asset_bp
from master_routes import master_bp
from hr_routes import hr_bp  # <-- HR Blueprint Import


app = Flask(__name__)

# 🔐 Session Security Key (OTP Session Tracking Ke Liye Zaruri Hai)
app.secret_key = 'radha_hims_secret_key_2026'

# Register Blueprints
app.register_blueprint(asset_bp, url_prefix='/api/assets')
app.register_blueprint(master_bp, url_prefix='/api/masters')
app.register_blueprint(hr_bp, url_prefix='/api/hr')  # <-- HR API Route Register


# 1. Main Landing Portal
@app.route('/')
def home():
    return render_template('index.html')


# 2. Dedicated PagarBook Style Login Page (Naya Add Kiya Hai)
@app.route('/login')
def login_page():
    return render_template('login.html')


# 3. Active Session User Check API (Logged-in User Name Header Ke Liye)
@app.route('/api/get-session-user', methods=['GET'])
def get_session_user():
    if 'user_name' in session:
        return jsonify({
            "is_logged_in": True,
            "user_name": session['user_name']
        }), 200
    return jsonify({"is_logged_in": False, "user_name": None}), 200


# 4. HR Module Dashboard Page
@app.route('/hr')
def hr_dashboard():
    return render_template('hr_dashboard.html')

# 5. Add Staff Dedicated Page (Naya Add Kiya)
@app.route('/hr/add-staff')
def add_staff_page():
    return render_template('add_staff.html')

@app.route('/hr/approve-punches')
def approve_punches_page():
    return render_template('approve_punches.html')

# Celebrations Page Route
@app.route('/hr/celebrations')
def celebrations_page():
    return render_template('celebrations.html')

@app.route('/hr/attendance-portal')
def attendance_portal_direct():
    return render_template('attendance_summary.html')

# Roster Management Page Route
@app.route('/hr/roster')
def roster_management_page():
    return render_template('roster_management.html')

# Direct fallback route for Geo page without /api prefix
@app.route('/hr/geo', methods=['GET'])
def direct_hr_geo():
    return render_template('geo.html')


@app.route('/hr/taskman')
def taskman_page():
    return render_template('taskman.html')

    # Page Route
@app.route('/hr/reports', methods=['GET'])
def reports_page():
    return render_template('reports.html')

from flask import render_template

@app.route('/hr/settings')
def hr_settings_page():
    return render_template('settings.html')





if __name__ == '__main__':
    app.run(debug=True, port=5000)

