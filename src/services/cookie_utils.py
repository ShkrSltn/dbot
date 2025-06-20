import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Optional, Dict, Any
import uuid

def set_cookie(name: str, value: str, expires_days: int = 7):
    """Set a cookie using JavaScript"""
    # Escape special characters in value
    escaped_value = value.replace('"', '\\"').replace("'", "\\'")
    
    cookie_script = f"""
    <script>
        const expires = new Date();
        expires.setTime(expires.getTime() + ({expires_days} * 24 * 60 * 60 * 1000));
        document.cookie = "{name}={escaped_value}; expires=" + expires.toUTCString() + "; path=/; SameSite=Lax";
    </script>
    """
    components.html(cookie_script, height=0)

def get_cookie(name: str) -> Optional[str]:
    """Get a cookie value using a simple approach with session state caching"""
    
    # Use session state to store the result once retrieved
    cookie_key = f"cookie_{name}"
    
    # Check if we already have the cookie value in session state
    if cookie_key in st.session_state:
        return st.session_state[cookie_key]
    
    # Use a unique component key to avoid conflicts
    component_key = f"cookie_getter_{name}_{uuid.uuid4().hex[:8]}"
    
    cookie_script = f"""
    <script>
        function getCookie(name) {{
            const value = "; " + document.cookie;
            const parts = value.split("; " + name + "=");
            if (parts.length === 2) {{
                return parts.pop().split(";").shift();
            }}
            return null;
        }}
        
        const cookieValue = getCookie("{name}");
        
        // Try to communicate with parent if possible
        if (cookieValue && window.parent && window.parent.postMessage) {{
            window.parent.postMessage({{
                type: 'streamlit:cookie',
                name: '{name}',
                value: cookieValue
            }}, '*');
        }}
    </script>
    <div style="display: none;">Cookie reader for {name}</div>
    """
    
    # Execute the JavaScript
    components.html(cookie_script, height=0, key=component_key)
    
    return None

def delete_cookie(name: str):
    """Delete a cookie by setting it to expire in the past"""
    cookie_script = f"""
    <script>
        document.cookie = "{name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax";
    </script>
    """
    components.html(cookie_script, height=0)

def set_session_cookie(user_id: int, session_token: str, expires_days: int = 7):
    """Set session cookie with user authentication data"""
    session_data = {
        "user_id": user_id,
        "session_token": session_token
    }
    
    # Convert to JSON string
    session_json = json.dumps(session_data)
    set_cookie("digibot_session", session_json, expires_days)
    
    # Also store in session state for immediate use
    st.session_state["cookie_digibot_session"] = session_json

def get_session_cookie() -> Optional[Dict[str, Any]]:
    """Get session data from cookie"""
    session_json = get_cookie("digibot_session")
    
    if session_json:
        try:
            session_data = json.loads(session_json)
            # Cache in session state for subsequent calls
            st.session_state["cookie_digibot_session"] = session_json
            return session_data
        except json.JSONDecodeError:
            return None
    
    return None

def clear_session_cookie():
    """Clear the session cookie"""
    delete_cookie("digibot_session")
    
    # Also clear from session state
    if "cookie_digibot_session" in st.session_state:
        del st.session_state["cookie_digibot_session"]

# Alternative approach using only session state for immediate use
def store_session_in_state(user_id: int, session_token: str):
    """Store session data directly in session state as fallback"""
    session_data = {
        "user_id": user_id,
        "session_token": session_token
    }
    st.session_state["auth_session"] = session_data

def get_session_from_state() -> Optional[Dict[str, Any]]:
    """Get session data from session state"""
    return st.session_state.get("auth_session", None)

def clear_session_from_state():
    """Clear session data from session state"""
    if "auth_session" in st.session_state:
        del st.session_state["auth_session"] 