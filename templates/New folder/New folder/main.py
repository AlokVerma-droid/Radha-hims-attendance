# फ़ाइल का नाम: main.py
# सेव करने का फ़ोल्डर: D:\Radha\Attendance\Backend_Server\
# काम: Attendance, HR, GRN, Payroll, Gate Face & Patient Care API Engine (Complete Combined File)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Database Connection & SaaS Middleware Import
from db_config import get_db_connection
from saas_middleware import check_client_subscription_limit

# Patient Care Module Router Import
from patient_care_api import router as patient_care_router

app = FastAPI(
    title="Radha ERP & Healthcare SaaS Engine",
    version="1.0.0",
    description="Attendance, HR Payroll, Inventory, Gate Face Kiosk & AI Patient Care Engine"
)

# --- Cyber Security Protection (CORS & Header Security) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# --- Include Patient Care Router ---
app.include_router(patient_care_router)


# =====================================================================
# REQUEST BODY MODELS
# =====================================================================

class PunchRequest(BaseModel):
    employee_id: int
    branch_id: int
    latitude: float
    longitude: float
    punch_type: str  # 'IN' या 'OUT'
    device_info: str

class LeaveApprovalRequest(BaseModel):
    leave_id: int
    approved_by_id: int
    status: str  # 'APPROVED' या 'REJECTED'

class GRNItemRequest(BaseModel):
    item_id: int
    quantity: int
    purchase_price: float
    supplier_id: int
    created_by: int

class PayrollProcessRequest(BaseModel):
    client_id: int
    month: int
    year: int
    processed_by: int

class GateFacePunchRequest(BaseModel):
    employee_id: int
    branch_id: int
    face_match_score: float
    device_id: str


# =====================================================================
# SYSTEM HEALTH & DB TEST
# =====================================================================

@app.get("/")
def health_check():
    return {
        "status": "online",
        "system": "Radha Attendance & Healthcare ERP Server",
        "security": "Encrypted & Active"
    }

@app.get("/api/v1/test-db")
def test_database_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        db_version = cursor.fetchone()[0]
        conn.close()
        return {"status": "connected", "database_version": db_version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Connection Error: {str(e)}")


# =====================================================================
# 1. ATTENDANCE PUNCH IN / OUT API (sp_PunchIn, sp_PunchOut)
# =====================================================================

@app.post("/api/v1/attendance/punch")
def mark_attendance(data: PunchRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if data.punch_type == "IN":
            cursor.execute(
                "{CALL dbo.sp_PunchIn (?, ?, ?, ?, ?)}",
                (data.employee_id, data.branch_id, data.latitude, data.longitude, data.device_info)
            )
        else:
            cursor.execute(
                "{CALL dbo.sp_PunchOut (?, ?, ?, ?, ?)}",
                (data.employee_id, data.branch_id, data.latitude, data.longitude, data.device_info)
            )
            
        conn.commit()
        return {"status": "success", "message": f"Punch {data.punch_type} दर्ज हो गया है।"}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# =====================================================================
# 2. HR LEAVE APPROVAL API (sp_ApproveLeave, sp_RejectLeave)
# =====================================================================

@app.post("/api/v1/hr/approve-leave")
def approve_leave_api(data: LeaveApprovalRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if data.status == "APPROVED":
            cursor.execute(
                "{CALL dbo.sp_ApproveLeave (?, ?)}",
                (data.leave_id, data.approved_by_id)
            )
        else:
            cursor.execute(
                "{CALL dbo.sp_RejectLeave (?, ?)}",
                (data.leave_id, data.approved_by_id)
            )
            
        conn.commit()
        return {"status": "success", "message": f"लीव स्टेटस {data.status} अपडेट कर दिया गया है।"}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# =====================================================================
# 3. INVENTORY & GRN BARCODE API (sp_AddGRNEntry, sp_GetBarcodeForPrint)
# =====================================================================

@app.post("/api/v1/inventory/add-grn")
def add_grn_entry(data: GRNItemRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "{CALL dbo.sp_AddGRNEntry (?, ?, ?, ?, ?)}",
            (data.item_id, data.quantity, data.purchase_price, data.supplier_id, data.created_by)
        )
        conn.commit()

        cursor.execute(
            "{CALL dbo.sp_GetBarcodeForPrint (?)}",
            (data.item_id,)
        )
        row = cursor.fetchone()
        barcode_number = row[0] if row else "BARCODE_GEN_FAILED"

        return {
            "status": "success", 
            "message": "GRN Entry सफलता से जुड़ गई है!",
            "barcode": barcode_number
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# =====================================================================
# 4. PAYROLL, BONUS & GRATUITY API (sp_GeneratePayroll etc.)
# =====================================================================

@app.post("/api/v1/payroll/generate")
def generate_monthly_payroll(data: PayrollProcessRequest):
    check_client_subscription_limit(data.client_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("{CALL dbo.sp_GeneratePayroll (?, ?, ?, ?)}", 
                       (data.client_id, data.month, data.year, data.processed_by))
        
        cursor.execute("{CALL dbo.sp_BonusCalculation (?, ?, ?)}", (data.client_id, data.month, data.year))
        cursor.execute("{CALL dbo.sp_GratuityCalculation (?, ?, ?)}", (data.client_id, data.month, data.year))
        cursor.execute("{CALL dbo.sp_PF_ESIContribution (?, ?, ?)}", (data.client_id, data.month, data.year))

        conn.commit()
        return {"status": "success", "message": "सैलरी, बोनस, ग्रैच्युटी और PF/ESI सफलतापूर्वक कैलकुलेट हो गए हैं!"}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# =====================================================================
# 5. GATE FACE SCAN KIOSK PUNCH API (sp_AttendancePunchSync)
# =====================================================================

@app.post("/api/v1/gate/face-punch")
def gate_face_punch_api(data: GateFacePunchRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if data.face_match_score < 0.80:
            return {"status": "unauthorized", "message": "चेहरा मैच नहीं हुआ! कृपया दोबारा प्रयास करें।"}

        cursor.execute(
            "{CALL dbo.sp_AttendancePunchSync (?, ?, ?, ?)}",
            (data.employee_id, data.branch_id, "Face Scan Gate", data.device_id)
        )
        
        conn.commit()
        return {
            "status": "success", 
            "message": "Face Recognized! Attendance Approved Successfully.",
            "location_logged": "Face Scan Gate"
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()