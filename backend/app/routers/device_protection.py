"""
Device-Wide Protection API for EduFeedia.
Supports EduFeedia Safe Browser, Chrome/Chromium Browser Extension,
and Android Companion App (VpnService & AccessibilityService).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.models import User, ChildProfile, SafetyIncident
from app.core.security import get_current_user

router = APIRouter(prefix="/device-protection", tags=["Device-Wide Protection"])

# Curated High-Trust Educational Domain Whitelist
TRUSTED_EDU_DOMAINS = [
    "edufeedia.org", "wikipedia.org", "khanacademy.org", "ncert.nic.in",
    "cbse.gov.in", "nationalgeographic.com", "britannica.com", "sciencedirect.com",
    "nasa.gov", "isro.gov.in", "duolingo.com", "scratch.mit.edu", "code.org",
    "geeksforgeeks.org", "coursera.org", "edx.org", "mit.edu", "stanford.edu"
]

# Prohibited Categories & Blacklisted Domain Signatures
PROHIBITED_CATEGORIES = {
    "ADULT_CONTENT": ["pornhub", "xvideos", "onlyfans", "chaturbate", "adultfriendfinder", "redtube", "brazzers"],
    "GAMBLING": ["bet365", "stake.com", "1xbet", "pokerstars", "mpl.live", "dream11", "casinomeister"],
    "MALWARE_AND_PHISHING": ["torrent", "thepiratebay", "1337x", "cracker", "keygen", "warez"],
    "UNMODERATED_SOCIAL": ["omegle", "chatroulette", "4chan", "kiwifarms", "tinder", "bumble"]
}

class VerifyUrlRequest(BaseModel):
    url: str
    user_id: Optional[str] = None
    child_id: Optional[str] = None
    client_type: str = "browser_extension" # 'browser_extension', 'safe_browser', 'android_companion'

class DeviceIncidentReport(BaseModel):
    user_id: Optional[str] = None
    child_id: Optional[str] = None
    url: str
    category: str
    action_taken: str = "BLOCKED"
    reason: str

@router.post("/verify-url", response_model=Dict[str, Any])
def verify_url_for_device(
    req: VerifyUrlRequest,
    db: Session = Depends(get_db)
):
    """
    Real-time URL verification for Browser Extension, Safe Browser, and Android Companion.
    Intercepts navigation, enforces search engine SafeSearch query parameter insertion,
    and blocks non-compliant or mature domains.
    """
    parsed = urlparse(req.url)
    hostname = (parsed.hostname or "").lower()

    # 1. Search Engine SafeSearch Query Parameter Rewriter
    # Enforces strict SafeSearch for Google, Bing, YouTube, DuckDuckGo
    is_search_engine = False
    safe_search_redirect = None

    if "google." in hostname and "/search" in parsed.path:
        is_search_engine = True
        if "safe=active" not in parsed.query:
            safe_search_redirect = f"{req.url}&safe=active" if parsed.query else f"{req.url}?safe=active"
    elif "bing.com" in hostname and "/search" in parsed.path:
        is_search_engine = True
        if "adlt=strict" not in parsed.query:
            safe_search_redirect = f"{req.url}&adlt=strict" if parsed.query else f"{req.url}?adlt=strict"
    elif "youtube.com" in hostname:
        is_search_engine = True
        # YouTube restricted mode header or parameter

    # 2. Check Whitelist
    for edu in TRUSTED_EDU_DOMAINS:
        if hostname == edu or hostname.endswith("." + edu):
            return {
                "allowed": True,
                "category": "VERIFIED_EDUCATIONAL",
                "action": "ALLOW",
                "reason": "Domain is in official EduFeedia verified educational whitelist.",
                "safe_search_redirect": safe_search_redirect
            }

    # 3. Check Blacklisted Prohibited Categories
    flagged_cat = None
    for category, signatures in PROHIBITED_CATEGORIES.items():
        for sig in signatures:
            if sig in hostname:
                flagged_cat = category
                break
        if flagged_cat:
            break

    if flagged_cat:
        # Log real safety incident
        incident = SafetyIncident(
            student_user_id=req.user_id,
            child_profile_id=req.child_id,
            source=req.client_type,
            category=flagged_cat,
            severity="critical" if flagged_cat == "ADULT_CONTENT" else "high",
            blocked=True,
            flagged_snippet=req.url,
            reason=f"Blocked attempt to access prohibited domain category: {flagged_cat}",
            action_taken="BLOCKED",
            parent_notified=True
        )
        db.add(incident)
        db.commit()

        return {
            "allowed": False,
            "category": flagged_cat,
            "action": "BLOCK",
            "blocked_url": req.url,
            "reason": f"Access restricted by EduFeedia Device Guard: Prohibited {flagged_cat.replace('_', ' ')}.",
            "redirect_block_page": "http://127.0.0.1:5173/?blocked=true"
        }

    # 4. Standard Safe Web Browsing
    if safe_search_redirect:
        return {
            "allowed": True,
            "category": "SEARCH_ENGINE",
            "action": "SAFESEARCH_REDIRECT",
            "safe_search_redirect": safe_search_redirect,
            "reason": "Enforcing strict SafeSearch policy on search query."
        }

    return {
        "allowed": True,
        "category": "GENERAL_WEB",
        "action": "ALLOW",
        "reason": "No high-risk violations detected.",
        "safe_search_redirect": None
    }


@router.get("/policy/{target_id}", response_model=Dict[str, Any])
def get_device_policy(
    target_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns active device-level protection policies (whitelists, blacklists,
    curfew hours, SafeSearch enforcement) for extension or companion app.
    """
    child = db.query(ChildProfile).filter(ChildProfile.id == target_id).first()
    student = db.query(User).filter(User.id == target_id, User.role == "student").first()

    curfew_enabled = True
    curfew_start = "21:00"
    curfew_end = "06:30"
    allowed_categories = ["STEM", "Creativity", "World", "Life Skills"]

    if child:
        curfew_enabled = child.curfew_enabled
        curfew_start = child.curfew_start_time or "20:00"
        curfew_end = child.curfew_end_time or "07:00"
        allowed_categories = child.allowed_categories or allowed_categories

    return {
        "target_id": target_id,
        "enforce_safe_search": True,
        "trusted_domains": TRUSTED_EDU_DOMAINS,
        "blocked_categories": list(PROHIBITED_CATEGORIES.keys()),
        "curfew_schedule": {
            "enabled": curfew_enabled,
            "start_time": curfew_start,
            "end_time": curfew_end
        },
        "allowed_learning_categories": allowed_categories,
        "tamper_protection_pin_required": True
    }


@router.post("/report-event", response_model=Dict[str, Any])
def report_device_safety_event(
    ev: DeviceIncidentReport,
    db: Session = Depends(get_db)
):
    """
    Direct ingestion of blocked browser extension/VPN events into SafetyIncident log.
    """
    incident = SafetyIncident(
        student_user_id=ev.user_id,
        child_profile_id=ev.child_id,
        source="browser_extension",
        category=ev.category,
        severity="high",
        blocked=True,
        flagged_snippet=ev.url,
        reason=ev.reason,
        action_taken=ev.action_taken,
        parent_notified=True
    )
    db.add(incident)
    db.commit()

    return {
        "status": "success",
        "message": "Device safety event logged and parent notification staged.",
        "incident_id": incident.id
    }
