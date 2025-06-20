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
            # Handle digital_proficiency options with proper mapping
            digital_proficiency_options = {
                1: "Beginner",
                2: "Basic", 
                3: "Intermediate",
                4: "Advanced",
                5: "Expert"
            }
            
            # Get current proficiency value and convert if needed
            current_proficiency = st.session_state.profile.get("digital_proficiency", "Intermediate")
            
            # Convert to int if it's a number, or map from string to int
            if isinstance(current_proficiency, (int, float)) or (isinstance(current_proficiency, str) and current_proficiency.isdigit()):
                current_proficiency_value = int(current_proficiency)
            else:
                # Map string values to numbers
                reverse_mapping = {v.lower(): k for k, v in digital_proficiency_options.items()}
                current_proficiency_value = reverse_mapping.get(
                    str(current_proficiency).lower(), 3  # Default to Intermediate (3)
                )
            
            digital_proficiency = st.selectbox(
                "Digital Proficiency",
                options=list(digital_proficiency_options.keys()),
                format_func=lambda x: digital_proficiency_options[x],
                index=current_proficiency_value-1 if 1 <= current_proficiency_value <= 5 else 2
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