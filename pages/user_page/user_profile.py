import streamlit as st
from services.db.crud._profiles import save_profile

def display_profile_step():
    st.subheader("Step 1: Create Your Profile")
    st.markdown("""
    First, let's create your digital skills profile. This information will be used to personalize
    statements and provide tailored feedback.
    """)
    
    # Use the existing profile builder with a custom submit handler
    with st.form("flow_profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            job_role = st.text_input("Job Role", value=st.session_state.profile.get("job_role", ""))
            job_domain = st.text_input("Job Domain", value=st.session_state.profile.get("job_domain", ""))
            years_experience = st.number_input("Years of Experience", min_value=0, max_value=50,
                                               value=st.session_state.profile.get("years_experience", 0))

        with col2:
            digital_proficiency = st.select_slider(
                "Digital Proficiency",
                options=["Beginner", "Intermediate", "Advanced", "Expert"],
                value=st.session_state.profile.get("digital_proficiency", "Intermediate")
            )
            primary_tasks = st.text_area("Primary Tasks", value=st.session_state.profile.get("primary_tasks", ""))

        submit_button = st.form_submit_button("Save Profile & Continue")

        if submit_button:
            handle_profile_submission(job_role, job_domain, years_experience, digital_proficiency, primary_tasks)

def handle_profile_submission(job_role, job_domain, years_experience, digital_proficiency, primary_tasks):
    # Validate that required fields are filled
    if not job_role or not job_domain or not primary_tasks:
        st.error("Please fill in all required fields.")
    else:
        # Create profile data dictionary
        profile_data = {
            "job_role": job_role,
            "job_domain": job_domain,
            "years_experience": years_experience,
            "digital_proficiency": digital_proficiency,
            "primary_tasks": primary_tasks
        }
        
        # Save to database
        if save_profile(st.session_state.user["id"], profile_data):
            st.session_state.profile = profile_data
            st.session_state.flow_step = 2
            st.rerun()
        else:
            st.error("Failed to save profile to database. Please try again.")
