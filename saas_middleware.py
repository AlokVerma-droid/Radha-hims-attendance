
from db_config import get_db_connection
from fastapi import HTTPException

def check_client_subscription_limit(client_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Stored Procedure dbo.sp_CheckClientValidity से क्लाइंट की स्थिति जानना
        cursor.execute("{CALL dbo.sp_CheckClientValidity (?)}", (client_id,))
        client_status = cursor.fetchone()
        
        # 2. कुल सक्रिय एम्प्लॉई की संख्या गिनना
        cursor.execute("SELECT COUNT(*) FROM dbo.tblEmployeeMaster WHERE ClientID = ? AND IsActive = 1", (client_id,))
        total_employees = cursor.fetchone()[0]

        plan_type = client_status[0] if client_status else "FREE"  # FREE or PAID

        # 3. Free Plan Rule: अधिकतम 10 एम्प्लॉई की अनुमति
        if plan_type == "FREE" and total_employees >= 10:
            raise HTTPException(
                status_code=403, 
                detail="फ्री वर्ज़न में अधिकतम 10 एम्प्लॉई की ही अनुमति है। नए एम्प्लॉई जोड़ने के लिए प्रो/पेड प्लान में अपग्रेड करें।"
            )

        return {"status": "ALLOWED", "total_employees": total_employees, "plan": plan_type}

    finally:
        conn.close()