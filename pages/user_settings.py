import streamlit as st
import pandas as pd
from service import get_sample_statements, get_statement_categories

def display_user_settings():
    st.title("⚙️ User Settings")
    
    st.markdown("""
    Customize your experience by selecting which statements you want to include in your assessment.
    These settings will affect which statements are shown in the quiz and user journey.
    """)
    
    # Initialize settings in session state if not exists
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = {
            "selected_statements": [],
            "custom_statements": [],
            "max_statements_per_quiz": 5
        }
    
    # Get statement categories from service
    categories = get_statement_categories()
    
    # Create tabs for different settings
    settings_tabs = st.tabs(["Select Statements", "Custom Statements", "Quiz Settings"])
    
    # Tab 1: Statement Selection
    with settings_tabs[0]:
        st.subheader("Select Individual Statements")
        st.markdown("""
        Choose which statements you want to include in your assessment.
        You can select statements from different categories.
        """)
        
        # Create an expander for each category
        selected_statements = st.session_state.user_settings.get("selected_statements", [])
        
        for category, statements in categories.items():
            with st.expander(f"{category} ({len(statements)} statements)"):
                for statement in statements:
                    is_selected = st.checkbox(
                        statement,
                        value=statement in selected_statements,
                        key=f"statement_{statement}"
                    )
                    
                    if is_selected and statement not in selected_statements:
                        selected_statements.append(statement)
                    elif not is_selected and statement in selected_statements:
                        selected_statements.remove(statement)
        
        # Save selected statements
        st.session_state.user_settings["selected_statements"] = selected_statements
        
        # Show selected statements
        if selected_statements:
            st.subheader("Your Selected Statements")
            
            # Display as a dataframe
            df = pd.DataFrame({"Statement": selected_statements})
            st.dataframe(df, use_container_width=True)
            
            st.info(f"Total statements selected: {len(selected_statements)}")
            
            # Clear selection button
            if st.button("Clear All Selections"):
                st.session_state.user_settings["selected_statements"] = []
                st.rerun()
        else:
            st.warning("No statements selected. Please select at least one statement.")
    
    # Tab 2: Custom Statements
    with settings_tabs[1]:
        st.subheader("Add Custom Statements")
        st.markdown("""
        Add your own custom statements that will be included in the assessment.
        These statements will be added to any selected from the categories.
        """)
        
        # Display existing custom statements
        custom_statements = st.session_state.user_settings["custom_statements"]
        
        # Add new statement input
        new_statement = st.text_input("Add a new statement:", key="new_custom_statement")
        if st.button("Add Statement") and new_statement:
            if new_statement not in custom_statements:
                custom_statements.append(new_statement)
                st.success(f"Added: {new_statement}")
                st.session_state.user_settings["custom_statements"] = custom_statements
                st.rerun()
            else:
                st.error("This statement already exists in your custom list.")
        
        # Display and manage existing custom statements
        if custom_statements:
            st.subheader("Your Custom Statements")
            
            for i, statement in enumerate(custom_statements):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(statement)
                with col2:
                    if st.button("Remove", key=f"remove_custom_{i}"):
                        custom_statements.pop(i)
                        st.session_state.user_settings["custom_statements"] = custom_statements
                        st.rerun()
            
            # Clear all button
            if st.button("Clear All Custom Statements"):
                st.session_state.user_settings["custom_statements"] = []
                st.rerun()
        else:
            st.info("You haven't added any custom statements yet.")
    
    # Tab 3: Quiz Settings
    with settings_tabs[2]:
        st.subheader("Quiz Settings")
        
        # Maximum statements per quiz
        max_statements = st.slider(
            "Maximum statements per quiz session:",
            min_value=1,
            max_value=10,
            value=st.session_state.user_settings["max_statements_per_quiz"],
            step=1
        )
        st.session_state.user_settings["max_statements_per_quiz"] = max_statements
        
        # Display current settings summary
        st.subheader("Current Settings Summary")
        
        # Calculate total statements
        total_statements = len(st.session_state.user_settings["selected_statements"]) + len(st.session_state.user_settings["custom_statements"])
        
        # Create summary dataframe
        summary_data = {
            "Setting": [
                "Selected Statements", 
                "Custom Statements", 
                "Total Available Statements",
                "Max Statements Per Quiz"
            ],
            "Value": [
                len(st.session_state.user_settings["selected_statements"]),
                len(st.session_state.user_settings["custom_statements"]),
                total_statements,
                st.session_state.user_settings["max_statements_per_quiz"]
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Warning if no statements selected
        if total_statements == 0:
            st.warning("You haven't selected any statements. Please select statements or add custom statements.") 