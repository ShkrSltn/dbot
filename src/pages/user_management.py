import streamlit as st
import pandas as pd
from services.db.crud._users import get_user_statistics, get_all_users
from datetime import datetime

def display_user_management():
    """
    Display user management interface for administrators
    """
    
    # Check if user is admin
    if st.session_state.get('current_role') != 'admin':
        st.error("🚫 Access denied. This page is only available to administrators.")
        return
    
    st.title("👥 User Management")
    st.markdown("### Manage registered users and view statistics")
    
    # Get user statistics
    stats = get_user_statistics()
    
    if stats:
        # Display statistics
        st.subheader("📊 User Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", stats["total_users"])
        
        with col2:
            st.metric("Administrators", stats["admin_count"])
        
        with col3:
            st.metric("Regular Users", stats["user_count"])
        
        with col4:
            st.metric("New This Week", stats["recent_registrations"])
        
        st.markdown("---")
        
        # User list
        st.subheader("👤 User List")
        
        # Controls
        show_limit = st.selectbox("Show users:", [10, 25, 50, 100, "All"], index=0)
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        # Get user list
        limit = None if show_limit == "All" else show_limit
        users = get_all_users(limit=limit)
        
        if users:
            # Convert to DataFrame for better display
            df = pd.DataFrame(users)
            
            # Format the created_at column
            if 'created_at' in df.columns:
                df['Registration Date'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                df = df.drop('created_at', axis=1)
            
            # Rename columns for better display
            df = df.rename(columns={
                'id': 'ID',
                'username': 'Username',
                'role': 'Role'
            })
            
            # Display the table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download functionality
            st.markdown("---")
            st.subheader("📥 Export Data")
            
            if st.button("Download User List (CSV)", use_container_width=True, type="primary"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"digibot_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        else:
            st.info("No users found in the database.")
    
    else:
        st.error("Failed to load user statistics. Please check the database connection.") 