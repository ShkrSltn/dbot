import streamlit as st
from services.db.crud._profiles import save_profile
from services.db.crud._settings import get_global_settings
from services.profile_evaluation_service import evaluate_profile_with_ai

def display_profile_step():
    st.subheader("Step 1: Create Your Profile")
    
    # Back button is not needed for Step 1 as it's the first step
    
    # Initialize suggestion_applied flag if not exists
    if 'suggestion_applied' not in st.session_state:
        st.session_state.suggestion_applied = False
    
    # Initialize profile_submitted flag if not exists
    if 'profile_submitted' not in st.session_state:
        st.session_state.profile_submitted = False
    
    # Get global settings to check if profile evaluation is enabled
    global_settings = get_global_settings("user_settings")
    profile_evaluation_enabled = global_settings.get("profile_evaluation_enabled", True) if global_settings else True
    
    # Get existing profile data from session state if available
    job_role = st.session_state.profile.get("job_role", "")
    job_domain = st.session_state.profile.get("job_domain", "")
    years_experience = st.session_state.profile.get("years_experience", 0)
    digital_proficiency = st.session_state.profile.get("digital_proficiency", 3)
    primary_tasks = st.session_state.profile.get("primary_tasks", "")
    
    # Create form for profile information
    with st.form("profile_form"):
        st.write("Tell us about your professional role:")
        
        job_role = st.text_input("Your Job Title/Role", value=job_role, 
                                help="E.g., Teacher, Marketing Manager, Software Developer")
        
        job_domain = st.text_input("Your Industry/Domain", value=job_domain,
                                 help="E.g., Education, Healthcare, Technology")
        
        # Convert years_experience to int safely
        try:
            years_experience_value = int(years_experience)
        except (ValueError, TypeError):
            years_experience_value = 0
            
        years_experience = st.number_input("Years of Experience", 
                                         min_value=0, max_value=50,
                                         value=years_experience_value)
        
        # Handle digital_proficiency options
        digital_proficiency_options = {
            1: "Beginner",
            2: "Basic",
            3: "Intermediate",
            4: "Advanced",
            5: "Expert"
        }
        
        # Convert digital_proficiency to int if it's a number, or map from string to int
        if isinstance(digital_proficiency, (int, float)) or (isinstance(digital_proficiency, str) and digital_proficiency.isdigit()):
            digital_proficiency_value = int(digital_proficiency)
        else:
            # Map string values to numbers
            reverse_mapping = {v.lower(): k for k, v in digital_proficiency_options.items()}
            digital_proficiency_value = reverse_mapping.get(
                str(digital_proficiency).lower(), 3  # Default to Intermediate (3)
            )
        
        digital_proficiency = st.selectbox(
            "Self-assessed Digital Proficiency",
            options=list(digital_proficiency_options.keys()),
            format_func=lambda x: digital_proficiency_options[x],
            index=digital_proficiency_value-1 if 1 <= digital_proficiency_value <= 5 else 2
        )
        
        primary_tasks = st.text_area("Describe your primary tasks and goals at work", 
                                   value=primary_tasks,
                                   help="Focus on tasks that involve digital tools or skills",
                                   height=150)
        
        # Show different buttons based on state and whether profile evaluation is enabled
        if profile_evaluation_enabled:
            # When AI evaluation is enabled, show Submit first, then Save after evaluation
            if st.session_state.profile_submitted:
                submit_button = st.form_submit_button("Submit")
                save_button = st.form_submit_button("Save Profile")
            else:
                submit_button = st.form_submit_button("Submit")
                save_button = False
        else:
            # When AI evaluation is disabled, show Save Profile directly
            submit_button = False
            save_button = st.form_submit_button("Save Profile")
        
        if submit_button:
            # Validate that required fields are filled
            if not job_role or not job_domain or not primary_tasks:
                st.error("Please fill in all required fields.")
            else:
                # Set profile_submitted flag to true
                st.session_state.profile_submitted = True
                
                # Store current values in session state
                current_profile = {
                    "job_role": job_role,
                    "job_domain": job_domain,
                    "years_experience": years_experience,
                    "digital_proficiency": digital_proficiency,
                    "primary_tasks": primary_tasks
                }
                st.session_state.current_profile = current_profile
                
                # Reset suggestion_applied flag
                st.session_state.suggestion_applied = False
                
                # Clear any previous AI evaluation
                if 'ai_evaluation' in st.session_state:
                    del st.session_state.ai_evaluation
                
                # Trigger AI evaluation only if enabled in settings
                if profile_evaluation_enabled:
                    with st.spinner("AI is analyzing your profile..."):
                        st.session_state.ai_evaluation = evaluate_profile_with_ai(current_profile)
                        
                        # If profile is good, automatically proceed to self-assessment
                        if st.session_state.ai_evaluation.get("is_good", True):
                            handle_profile_submission(job_role, job_domain, years_experience, digital_proficiency, primary_tasks)
                            return
                
                st.rerun()
                
        if save_button:
            handle_profile_submission(job_role, job_domain, years_experience, digital_proficiency, primary_tasks)

    # Display AI feedback if available and profile was submitted
    if st.session_state.profile_submitted and 'ai_evaluation' in st.session_state and profile_evaluation_enabled:
        if not st.session_state.ai_evaluation.get("is_good", True):
            with st.expander("💡 AI Suggestions for Your Profile", expanded=True):
                st.info(st.session_state.ai_evaluation.get("feedback", ""))
                
                suggestion = st.session_state.ai_evaluation.get("suggestion", "")
                if suggestion:
                    st.markdown("**Suggested improvement:**")
                    st.markdown(f"*{suggestion}*")
                    
                    if st.button("Use This Suggestion"):
                        # Update the form with the suggestion
                        st.session_state.profile["primary_tasks"] = suggestion
                        # Set flag to prevent immediate re-evaluation
                        st.session_state.suggestion_applied = True
                        # Clear the evaluation
                        if 'ai_evaluation' in st.session_state:
                            del st.session_state.ai_evaluation
                        st.rerun()
        else:
            st.success("Your profile looks good! Proceeding to self-assessment...")
            # Automatically save and proceed to next step
            handle_profile_submission(job_role, job_domain, years_experience, digital_proficiency, primary_tasks)

def handle_profile_submission(job_role, job_domain, years_experience, digital_proficiency, primary_tasks):
    # Validate that required fields are filled
    if not job_role or not job_domain or not primary_tasks:
        st.error("Please fill in all required fields.")
        return
    
    # Create profile data dictionary
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
    if st.session_state.user and st.session_state.user["id"]:
        if save_profile(st.session_state.user["id"], profile_data):
            st.success("Profile saved successfully!")
            # Clear any previous AI evaluation
            if 'ai_evaluation' in st.session_state:
                del st.session_state.ai_evaluation
            # Reset flags
            st.session_state.suggestion_applied = False
            st.session_state.profile_submitted = False
            # Move to next step
            st.session_state.flow_step = 2
            st.rerun()
        else:
            st.error("Failed to save profile to database. Please try again.")