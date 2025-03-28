import streamlit as st
from services.db.crud._profiles import save_profile, get_profile

def display_profile_builder():
    st.title("👤 Profile Builder")
    st.markdown("""
    Create your digital skills profile to personalize the DigiBot experience.
    This information will be used to tailor statements and chatbot responses to your specific context.
    """)
    
    # Get user profile from database
    if 'profile' not in st.session_state or not st.session_state.profile.get("job_role"):
        user_profile = get_profile(st.session_state.user["id"])
        if user_profile:
            st.session_state.profile = user_profile

    with st.form("profile_form"):
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

        submit_button = st.form_submit_button("Save Profile")

        if submit_button:
            profile_data = {
                "job_role": job_role,
                "job_domain": job_domain,
                "years_experience": years_experience,
                "digital_proficiency": digital_proficiency,
                "primary_tasks": primary_tasks
            }
            
            # Save to session state
            st.session_state.profile = profile_data
            
            # Save to database
            if save_profile(st.session_state.user["id"], profile_data):
                st.success("Profile saved successfully!")
                st.balloons()
            else:
                st.error("Failed to save profile. Please try again.") 