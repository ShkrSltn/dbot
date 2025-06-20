import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Optional, Dict, Any
import uuid
import base64

def set_cookie(name: str, value: str, expires_days: int = 7):
    """Set a cookie using JavaScript"""
    # Escape special characters in value and encode to base64 for safety
    encoded_value = base64.b64encode(value.encode('utf-8')).decode('utf-8')
    
    cookie_script = f"""
    <script>
        const expires = new Date();
        expires.setTime(expires.getTime() + ({expires_days} * 24 * 60 * 60 * 1000));
        document.cookie = "{name}={encoded_value}; expires=" + expires.toUTCString() + "; path=/; SameSite=Lax; Secure";
        
        // Also store in localStorage as backup
        try {{
            localStorage.setItem('st_{name}', '{encoded_value}');
        }} catch(e) {{
            console.log('localStorage not available');
        }}
    </script>
    """
    components.html(cookie_script, height=0)

def get_cookie(name: str) -> Optional[str]:
    """Get a cookie value using JavaScript with localStorage fallback"""
    
    # Use session state to cache the result
    cache_key = f"cached_cookie_{name}"
    
    # Check if we already have the cookie value in session state
    if cache_key in st.session_state and st.session_state[cache_key] is not None:
        return st.session_state[cache_key]
    
    # Use a unique component key
    component_key = f"cookie_getter_{name}_{uuid.uuid4().hex[:8]}"
    
    cookie_script = f"""
    <script>
        function getCookie(name) {{
            const value = "; " + document.cookie;
            const parts = value.split("; " + name + "=");
            if (parts.length === 2) {{
                const cookieValue = parts.pop().split(";").shift();
                if (cookieValue) {{
                    try {{
                        return atob(cookieValue); // Decode base64
                    }} catch(e) {{
                        return cookieValue; // Fallback for non-encoded values
                    }}
                }}
            }}
            return null;
        }}
        
        function getFromLocalStorage(name) {{
            try {{
                const value = localStorage.getItem('st_' + name);
                if (value) {{
                    return atob(value); // Decode base64
                }}
            }} catch(e) {{
                console.log('Error reading from localStorage');
            }}
            return null;
        }}
        
        let cookieValue = getCookie("{name}");
        
        // If cookie not found, try localStorage
        if (!cookieValue) {{
            cookieValue = getFromLocalStorage("{name}");
        }}
        
        // Store result in a hidden div that we can read
        if (cookieValue) {{
            const resultDiv = document.getElementById('cookie-result-{component_key}');
            if (resultDiv) {{
                resultDiv.textContent = cookieValue;
                resultDiv.style.display = 'block';
            }}
        }}
        
        // Try to communicate with parent if possible
        if (cookieValue && window.parent && window.parent.postMessage) {{
            window.parent.postMessage({{
                type: 'streamlit:cookie',
                name: '{name}',
                value: cookieValue
            }}, '*');
        }}
    </script>
    <div id="cookie-result-{component_key}" style="display: none; opacity: 0; height: 0; overflow: hidden;"></div>
    """
    
    # Execute the JavaScript
    result = components.html(cookie_script, height=0)
    
    return None

def delete_cookie(name: str):
    """Delete a cookie by setting it to expire in the past"""
    cookie_script = f"""
    <script>
        document.cookie = "{name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax";
        
        // Also remove from localStorage
        try {{
            localStorage.removeItem('st_{name}');
        }} catch(e) {{
            console.log('localStorage not available');
        }}
    </script>
    """
    components.html(cookie_script, height=0)

def set_session_data(user_id: int, session_token: str):
    """Store session data in session state and query params"""
    session_data = {
        "user_id": user_id,
        "session_token": session_token
    }
    
    # Store in session state
    st.session_state["auth_session"] = session_data
    
    # Also store in query params for persistence across refreshes
    try:
        session_json = json.dumps(session_data)
        encoded_session = base64.b64encode(session_json.encode()).decode()
        
        # Update query params
        query_params = dict(st.query_params)
        query_params["session"] = encoded_session
        st.query_params.update(query_params)
        
    except Exception as e:
        print(f"Error setting query params: {e}")

def get_session_data() -> Optional[Dict[str, Any]]:
    """Get session data from session state or query params"""
    # First try session state
    if "auth_session" in st.session_state:
        return st.session_state["auth_session"]
    
    # Then try query params
    try:
        if "session" in st.query_params:
            encoded_session = st.query_params["session"]
            session_json = base64.b64decode(encoded_session.encode()).decode()
            session_data = json.loads(session_json)
            
            # Restore to session state
            st.session_state["auth_session"] = session_data
            return session_data
    except Exception as e:
        print(f"Error getting session from query params: {e}")
    
    return None

def clear_session_data():
    """Clear session data from all storage"""
    # Clear from session state
    if "auth_session" in st.session_state:
        del st.session_state["auth_session"]
    
    # Clear from query params
    try:
        query_params = dict(st.query_params)
        if "session" in query_params:
            del query_params["session"]
            st.query_params.clear()
            st.query_params.update(query_params)
    except Exception as e:
        print(f"Error clearing query params: {e}")

def set_current_page(page_name: str):
    """Set current page in session state and query params"""
    st.session_state["current_page"] = page_name
    
    try:
        query_params = dict(st.query_params)
        query_params["page"] = page_name
        st.query_params.update(query_params)
    except Exception as e:
        print(f"Error setting page in query params: {e}")

def get_current_page() -> Optional[str]:
    """Get current page from session state or query params"""
    # First try session state
    if "current_page" in st.session_state:
        return st.session_state["current_page"]
    
    # Then try query params
    try:
        if "page" in st.query_params:
            page_name = st.query_params["page"]
            st.session_state["current_page"] = page_name
            return page_name
    except Exception as e:
        print(f"Error getting page from query params: {e}")
    
    return None

def clear_current_page():
    """Clear current page from all storage"""
    if "current_page" in st.session_state:
        del st.session_state["current_page"]
    
    try:
        query_params = dict(st.query_params)
        if "page" in query_params:
            del query_params["page"]
            st.query_params.update(query_params)
    except Exception as e:
        print(f"Error clearing page from query params: {e}")

def restore_session_on_startup():
    """Try to restore session data on app startup"""
    try:
        print("DEBUG: Attempting to restore session...")
        session_data = get_session_data()
        if session_data:
            print(f"DEBUG: Session restored for user {session_data.get('user_id')}")
            return session_data
        else:
            print("DEBUG: No session data found to restore")
        return None
    except Exception as e:
        print(f"DEBUG: Error restoring session: {e}")
        return None

def ensure_session_persistence():
    """Ensure session data is properly persisted"""
    try:
        if "auth_session" in st.session_state:
            auth_data = st.session_state["auth_session"]
            if "user_id" in auth_data and "session_token" in auth_data:
                set_session_data(auth_data["user_id"], auth_data["session_token"])
    except Exception as e:
        print(f"Error ensuring session persistence: {e}")

# Legacy function aliases for compatibility
def set_session_cookie(user_id: int, session_token: str, expires_days: int = 7):
    """Legacy alias for set_session_data"""
    set_session_data(user_id, session_token)

def get_session_cookie() -> Optional[Dict[str, Any]]:
    """Legacy alias for get_session_data"""
    return get_session_data()

def clear_session_cookie():
    """Legacy alias for clear_session_data"""
    clear_session_data()

def set_current_page_cookie(page_name: str):
    """Legacy alias for set_current_page"""
    set_current_page(page_name)

def get_current_page_cookie() -> Optional[str]:
    """Legacy alias for get_current_page"""
    return get_current_page()

def clear_current_page_cookie():
    """Legacy alias for clear_current_page"""
    clear_current_page()

# Additional helper functions
def store_session_in_state(user_id: int, session_token: str):
    """Store session data directly in session state"""
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