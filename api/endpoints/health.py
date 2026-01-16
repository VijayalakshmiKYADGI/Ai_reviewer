import time
from fastapi import APIRouter
from api.models import HealthResponse
from data.database import get_db_connection

router = APIRouter()
start_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    # Check DB
    db_status = "disconnected"
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except:
        db_status = "error"
        
    status = "healthy" if db_status == "connected" else "degraded"
    
    return HealthResponse(
        status=status,
        database=db_status,
        uptime=time.time() - start_time
    )
