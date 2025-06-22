import streamlit as st
from services.db.crud._users import authenticate_user, create_anonymous_user, register_user, validate_password_strength
from services.db.connection import generate_session_token
from services.cookie_utils import (
    set_session_data, 
    clear_session_data, 
    store_session_in_state,
    ensure_session_persistence,
    # Legacy aliases for compatibility
    set_session_cookie, 
    clear_session_cookie
)
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
        # Create a nice layout with description
        st.markdown("""
        Welcome to DigiBot - a tool for personalizing digital competency statements.
        Please log in, create a new account, or try the demo version.
        """)
        
        # Add some spacing
        st.write("")
        
        # Create tabs for Login and Register
        tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Register", "🚀 Demo"])
        
        with tab1:
            st.markdown("### Login to your account")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                remember_me = st.checkbox("Remember me", value=True, help="Keep me logged in for 7 days")
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
                            
                            # Store session data in session state and query params
                            set_session_data(auth_result["user"]["id"], session_token)
                            store_session_in_state(auth_result["user"]["id"], session_token)
                            
                            # Ensure persistence is set up
                            ensure_session_persistence()
                            
                            st.success("Logged in successfully!")
                            print(f"DEBUG: User {username} logged in successfully")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
        
        with tab2:
            st.markdown("### Create a new account")
            
            with st.form("register_form"):
                reg_username = st.text_input("Username", help="At least 3 characters, letters, numbers, and underscores only")
                reg_password = st.text_input("Password", type="password", help="At least 6 characters")
                
                # Show password strength if password is entered
                if reg_password:
                    password_check = validate_password_strength(reg_password)
                    
                    # Color code the strength indicator
                    if password_check["strength"] == "Strong":
                        st.success(f"Password strength: {password_check['strength']}")
                    elif password_check["strength"] == "Medium":
                        st.warning(f"Password strength: {password_check['strength']}")
                    else:
                        st.error(f"Password strength: {password_check['strength']}")
                    
                    # Show feedback if available
                    if password_check["feedback"]:
                        with st.expander("💡 Password improvement tips"):
                            for tip in password_check["feedback"]:
                                st.write(f"• {tip}")
                
                reg_confirm_password = st.text_input("Confirm Password", type="password")
                
                # Show password match status
                if reg_password and reg_confirm_password:
                    if reg_password == reg_confirm_password:
                        st.success("✅ Passwords match")
                    else:
                        st.error("❌ Passwords do not match")
                
                # Add terms and conditions checkbox
                terms_accepted = st.checkbox("I agree to the terms and conditions", help="By checking this box, you agree to our terms of service")
                
                register_submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if register_submitted:
                    if not terms_accepted:
                        st.error("Please accept the terms and conditions to create an account")
                    elif not reg_username or not reg_password or not reg_confirm_password:
                        st.error("Please fill in all fields")
                    else:
                        with st.spinner("Creating your account..."):
                            register_result = register_user(reg_username, reg_password, reg_confirm_password)
                            if register_result["success"]:
                                # Generate session token for new user
                                session_token = generate_session_token(register_result["user"]["id"])
                                
                                # Set session state
                                st.session_state.authenticated = True
                                st.session_state.user = register_result["user"]
                                st.session_state.current_role = register_result["user"]["role"]
                                
                                # Store session data
                                set_session_data(register_result["user"]["id"], session_token)
                                store_session_in_state(register_result["user"]["id"], session_token)
                                
                                # Ensure persistence is set up
                                ensure_session_persistence()
                                
                                st.success(f"Account created successfully! Welcome, {reg_username}!")
                                st.balloons()
                                print(f"DEBUG: New user {reg_username} registered successfully")
                                st.rerun()
                            else:
                                st.error(register_result["error"])
        
        with tab3:
            st.markdown("### Try DigiBot without registration")
            st.markdown("No account needed - create a temporary demo account to explore the features:")
            
            # Add some spacing
            st.write("")
            
            if st.button("Start Demo", use_container_width=True, type="primary"):
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
                    
                    # Store session data in session state and query params
                    set_session_data(anon_result["user"]["id"], session_token)
                    store_session_in_state(anon_result["user"]["id"], session_token)
                    
                    # Ensure persistence is set up
                    ensure_session_persistence()
                    
                    st.success(f"Demo account created: {anonymous_username}")
                    print(f"DEBUG: Demo user {anonymous_username} created successfully")
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
            # Clear session data using new functions
            clear_session_data()
            
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Clear query params (if any)
            st.query_params.clear()
            
            print("DEBUG: User logged out successfully")
            st.rerun()