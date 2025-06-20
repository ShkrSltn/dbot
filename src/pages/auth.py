import streamlit as st
from services.db.crud._users import authenticate_user, create_anonymous_user
from services.db.connection import generate_session_token
from services.cookie_utils import set_session_cookie, clear_session_cookie, store_session_in_state
import uuid


def get_version_info():
    """
    Returns version information about the DigiBot application.
    Can be used across the application to display version info.
    
    Returns:
        dict: Dictionary with version details
    """
    return {
        "version": "2.0.1",
        "name": "DigiBot",
        "description": "Tool for personalizing digital competency statements"
    }


def display_auth():
    st.title("🔐 DigiBot Authorization")
    
    version_info = get_version_info()
    st.write(f"DigiBot v{version_info['version']}")
    st.write("---")

    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_role = None
    
    if not st.session_state.authenticated:
        # Create a nice layout with columns
        st.markdown("""
        Welcome to DigiBot - a tool for personalizing digital competency statements.
        Please log in to continue or try the demo version.
        """)
        
        # Add some spacing
        st.write("")
        
        # Create two columns for login and demo
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        auth_result = authenticate_user(username, password)
                        if auth_result["success"]:
                            # Generate session token
                            session_token = generate_session_token(auth_result["user"]["id"])
                            
                            # Set session state first
                            st.session_state.authenticated = True
                            st.session_state.user = auth_result["user"]
                            st.session_state.current_role = auth_result["user"]["role"]
                            
                            # Store session data in secure cookie and session state
                            set_session_cookie(auth_result["user"]["id"], session_token, expires_days=7)
                            store_session_in_state(auth_result["user"]["id"], session_token)
                            
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
        
        with col2:
            st.subheader("Quick Access")
            st.markdown("No account? Try the demo version:")
            
            # Add some spacing
            st.write("")
            st.write("")
            
            if st.button("Try Demo", use_container_width=True):
                # Generate a unique anonymous username
                anonymous_username = f"demo_{uuid.uuid4().hex[:8]}"
                
                # Create anonymous user
                anon_result = create_anonymous_user(anonymous_username)
                
                if anon_result["success"]:
                    # Generate session token for anonymous user
                    session_token = generate_session_token(anon_result["user"]["id"])
                    
                    # Set session state first
                    st.session_state.authenticated = True
                    st.session_state.user = anon_result["user"]
                    st.session_state.current_role = "user"
                    
                    # Store session data in secure cookie and session state
                    set_session_cookie(anon_result["user"]["id"], session_token, expires_days=1)
                    store_session_in_state(anon_result["user"]["id"], session_token)
                    
                    st.success(f"Demo account created: {anonymous_username}")
                    st.rerun()
                else:
                    st.error(f"Failed to create demo account: {anon_result.get('error', 'Unknown error')}")
            
    else:
        # Show logged in state
        st.success(f"Logged in as {st.session_state.user['username']} ({st.session_state.current_role})")
        
        # Add some information about the app
        st.markdown("""
        ### Welcome to DigiBot
        
        You are now logged in and can access the application. Use the sidebar to navigate.
        """)
        
        if st.button("Logout", use_container_width=True):
            # Clear session cookie
            clear_session_cookie()
            
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Clear query params (if any)
            st.query_params.clear()
            
            st.rerun()