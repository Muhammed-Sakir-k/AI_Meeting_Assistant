import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginRequest = Body(...)):
    """
    Backend authentication route.
    Validates username and password, returning user role.
    """
    username = payload.username
    password = payload.password
    
    # Preset credentials validation
    if username == "admin" and password == "admin123":
        return {
            "status": "success",
            "username": "admin",
            "role": "admin"
        }
    elif username == "user" and password == "user123":
        return {
            "status": "success",
            "username": "user",
            "role": "user"
        }
        
    raise HTTPException(status_code=401, detail="Invalid username or password.")
