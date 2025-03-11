import streamlit as st

def display_profile_builder():
    st.title("👤 Profile Builder")
    st.markdown("""
    Create your digital skills profile to personalize the DigiBot experience.
    This information will be used to tailor statements and chatbot responses to your specific context.
    """)

    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            job_role = st.text_input("Job Role", value=st.session_state.profile["job_role"])
            job_domain = st.text_input("Job Domain", value=st.session_state.profile["job_domain"])
            years_experience = st.number_input("Years of Experience", min_value=0, max_value=50,
                                               value=st.session_state.profile["years_experience"])

        with col2:
            digital_proficiency = st.select_slider(
                "Digital Proficiency",
                options=["Beginner", "Intermediate", "Advanced", "Expert"],
                value=st.session_state.profile["digital_proficiency"]
            )
            primary_tasks = st.text_area("Primary Tasks", value=st.session_state.profile["primary_tasks"])

        submit_button = st.form_submit_button("Save Profile")

        if submit_button:
            st.session_state.profile = {
                "job_role": job_role,
                "job_domain": job_domain,
                "years_experience": years_experience,
                "digital_proficiency": digital_proficiency,
                "primary_tasks": primary_tasks
            }
            st.success("Profile saved successfully!")
            st.balloons() 