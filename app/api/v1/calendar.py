from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/calendar", tags=["Google Calendar"])

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def get_client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID or "",
            "client_secret": settings.GOOGLE_CLIENT_SECRET or "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
        }
    }

@router.get("/auth")
def google_calendar_auth(current_user: User = Depends(get_current_user)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return {"success": False, "message": "Google Calendar integration is not configured."}
        
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    response = RedirectResponse(url=auth_url)
    response.set_cookie(key="google_oauth_state", value=state, httponly=True, max_age=600)
    # Also pass user ID in state to know who is connecting? Or rely on session cookie.
    return response

@router.get("/callback")
def google_calendar_callback(
    request: Request, 
    code: str, 
    state: str,
    db: Session = Depends(get_db)
):
    # Retrieve user from cookie (since it's a browser redirect, session_token should be there)
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login?error=Session+expired")
        
    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login?error=Invalid+token")
        
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return RedirectResponse(url="/login?error=User+not+found")

    saved_state = request.cookies.get("google_oauth_state")
    if saved_state != state:
        return RedirectResponse(url="/patient/dashboard?error=Invalid+state")
        
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        state=state,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    # Exchange authorization code for access token
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    user.google_access_token = credentials.token
    user.google_refresh_token = credentials.refresh_token if credentials.refresh_token else user.google_refresh_token
    
    if credentials.expiry:
        # Convert naive datetime to aware if necessary
        expiry = credentials.expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        user.google_token_expires_at = expiry
        
    db.commit()
    
    redirect_dashboard = "/doctor/dashboard" if user.role.value == "DOCTOR" else "/patient/dashboard"
    response = RedirectResponse(url=f"{redirect_dashboard}?success=Calendar+connected")
    response.delete_cookie("google_oauth_state")
    return response
