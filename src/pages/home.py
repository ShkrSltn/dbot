import streamlit as st
import pandas as pd

def display_home_page():
    st.title("🏠 Welcome to DigiBot Demo")
    
    st.markdown("""
    ## Digital Skills Personalization Platform
    
    DigiBot helps personalize digital skills statements and provides tailored guidance based on your professional profile.
    
    ### Features:
    
    - **Profile Builder**: Create your digital skills profile
    - **Enrichment Demo**: See how statements are personalized for your profile
    - **Batch Enrichment**: Process multiple statements at once
    - **Quiz**: Compare original and personalized statements
    - **Chatbot**: Get personalized guidance on digital skills
    - **Analytics**: View detailed metrics and visualizations
    
    ### Getting Started:
    
    1. Create your profile in the Profile Builder section
    2. Try the Enrichment Demo to see how statements are personalized
    3. Take the quiz to compare original and personalized statements
    4. Chat with DigiBot for personalized guidance
    
    Use the navigation menu on the left to explore the different features.
    """)
    

    # Display current profile if available
    if st.session_state.profile["job_role"]:
        st.subheader("Your Current Profile")
        profile_df = pd.DataFrame([st.session_state.profile])
        st.dataframe(profile_df) 