# फ़ाइल का नाम: patient_care_api.py
# सेव करने का फ़ोल्डर: D:\Radha\Attendance\Backend_Server\
# काम: Patient Care Module - Excel/Form Data Entry & Fetch API

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from db_config import get_db_connection

router = APIRouter(prefix="/api/v1/patient-care", tags=["Patient Care"])

# Pydantic Model for Patient Entry (कोई भी डिफ़ॉल्ट वैल्यू नहीं)
class PatientModel(BaseModel):
    client_id: int
    patient_name: str
    mobile_no: str
    medicine_detail: str
    reminder_time: str
    language_pref: str  # हिंदी, भोजपुरी, आदि (Dynamic)
    call_status: str    # Pending, Scheduled, Call Cut आदि (Dynamic)

# 1. पेशेंट डेटा सेव करने का API
@router.post("/add-patients")
def add_patients(patients: List[PatientModel]):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO dbo.tblPatientCare 
            (ClientID, PatientName, MobileNo, MedicineDetail, ReminderTime, LanguagePref, CallStatus)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        for p in patients:
            cursor.execute(
                query, 
                (p.client_id, p.patient_name, p.mobile_no, p.medicine_detail, p.reminder_time, p.language_pref, p.call_status)
            )
            
        conn.commit()
        return {"status": "success", "message": f"{len(patients)} पेशेंट का रिकॉर्ड सफलता से दर्ज हो गया!"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# 2. पेशेंट लिस्ट फ़ेच करने का API
@router.get("/get-list/{client_id}")
def get_patient_list(client_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT PatientID, PatientName, MobileNo, MedicineDetail, ReminderTime, LanguagePref, CallStatus FROM dbo.tblPatientCare WHERE ClientID = ? ORDER BY PatientID DESC",
            (client_id,)
        )
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            result.append({
                "patient_id": r[0],
                "patient_name": r[1],
                "mobile_no": r[2],
                "medicine_detail": r[3],
                "reminder_time": r[4],
                "language_pref": r[5],
                "call_status": r[6]
            })
            
        return {"status": "success", "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        # =====================================================================
# 3. AI CALL DISCONNECTION, RETRY & CRITICAL ALERT LOGIC (सबसे नीचे)
# =====================================================================

class CallLogUpdateRequest(BaseModel):
    patient_id: int
    call_status: str     # 'Completed', 'Call Cut', 'Disconnected', 'Critical Alert'
    call_notes: str      # पेशेंट ने क्या जवाब दिया या समस्या क्या थी
    retry_required: bool

@router.post("/update-call-log")
def update_patient_call_log(data: CallLogUpdateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # अगर नेटवर्क दिक्कत या कॉल कट हुई है तो री-ट्राई लॉजिक
        new_status = data.call_status
        if data.call_status in ["Call Cut", "Disconnected"] and data.retry_required:
            new_status = "Retry Scheduled"

        # SQL टेबल में स्टेटस और नोट्स अपडेट करना
        query = """
            UPDATE dbo.tblPatientCare 
            SET CallStatus = ?, 
                MedicineDetail = MedicineDetail + ' | Note: ' + ?
            WHERE PatientID = ?
        """
        cursor.execute(query, (new_status, data.call_notes, data.patient_id))
        conn.commit()

        # अगर क्रिटिकल अलर्ट (इमरजेंसी) है तो डॉक्टर को तुरंत अलर्ट का संदेश
        if data.call_status == "Critical Alert":
            return {
                "status": "EMERGENCY_ALERT",
                "message": f"पेशेंट ID {data.patient_id} की तबीयत ख़राब है! डॉक्टर डैशबोर्ड पर अलर्ट भेज दिया गया है।",
                "patient_id": data.patient_id
            }

        return {
            "status": "success", 
            "updated_status": new_status,
            "message": "कॉल रिकॉर्ड और री-ट्राई स्टेटस सफलता से अपडेट हो गया!"
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()