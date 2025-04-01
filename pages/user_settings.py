import streamlit as st
import pandas as pd
from services.statement_service import get_all_statements
from services.db.crud._settings import get_global_settings, save_global_settings

def display_user_settings():
    st.title("⚙️ Global Settings")
    
    st.markdown("""
    Customize the global experience by selecting which statements you want to include in assessments.
    These settings will affect which statements are shown in the quiz and user journey for all users.
    """)
    
    # Get global settings
    global_settings = get_global_settings("user_settings")
    
    if not global_settings:
        st.error("Failed to load global settings. Please try again later.")
        return
    
    # Get all available statements
    statements = get_all_statements()
    
    # Create tabs for different settings
    settings_tabs = st.tabs(["Select Statements", "Custom Statements", "Quiz Settings"])
    
    # Tab 1: Statement Selection
    with settings_tabs[0]:
        st.subheader("Select Statements")
        st.markdown("""
        Choose which statements you want to include in assessments.
        """)
        
        # Get selected statements
        selected_statements = global_settings.get("selected_statements", [])
        
        # Create checkboxes for each statement
        for i, statement in enumerate(statements):
            is_selected = st.checkbox(
                statement,
                value=i in selected_statements,
                key=f"statement_{i}"
            )
            
            if is_selected and i not in selected_statements:
                selected_statements.append(i)
            elif not is_selected and i in selected_statements:
                selected_statements.remove(i)
        
        # Save selected statements
        global_settings["selected_statements"] = selected_statements
        
        # Show selected statements
        if selected_statements:
            st.subheader("Selected Statements")
            
            # Display as a dataframe
            selected_texts = [statements[i] for i in selected_statements]
            df = pd.DataFrame({"Statement": selected_texts})
            st.dataframe(df, use_container_width=True)
            
            st.info(f"Total statements selected: {len(selected_statements)}")
            
            # Функция для очистки всех выбранных утверждений
            def clear_all_statements():
                # Очищаем список выбранных утверждений
                global_settings = get_global_settings("user_settings")
                global_settings["selected_statements"] = []
                save_global_settings("user_settings", global_settings)

            # Clear selection button
            if st.button("Clear All Statements", key="clear_all_btn", on_click=clear_all_statements):
                # Кнопка автоматически вызовет функцию clear_all_statements при нажатии
                # и затем выполнит перезагрузку страницы
                pass
        else:
            st.warning("No statements selected. Please select at least one statement.")
    
    # Tab 2: Custom Statements
    with settings_tabs[1]:
        st.subheader("Add Custom Statements")
        st.markdown("""
        Add custom statements that will be included in assessments.
        These statements will be added to any selected from the categories.
        """)
        
        # Display existing custom statements
        custom_statements = global_settings.get("custom_statements", [])
        
        # Add new statement input
        new_statement = st.text_input("Add a new statement:", key="new_custom_statement")
        if st.button("Add Statement") and new_statement:
            if new_statement not in custom_statements:
                custom_statements.append(new_statement)
                st.success(f"Added: {new_statement}")
                global_settings["custom_statements"] = custom_statements
                save_global_settings("user_settings", global_settings)
                st.rerun()
            else:
                st.error("This statement already exists in your custom list.")
        
        # Display and manage existing custom statements
        if custom_statements:
            st.subheader("Custom Statements")
            
            for i, statement in enumerate(custom_statements):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(statement)
                with col2:
                    if st.button("Remove", key=f"remove_custom_{i}"):
                        custom_statements.pop(i)
                        global_settings["custom_statements"] = custom_statements
                        save_global_settings("user_settings", global_settings)
                        st.rerun()
            
            # Clear all button
            if st.button("Clear All Custom Statements"):
                global_settings["custom_statements"] = []
                save_global_settings("user_settings", global_settings)
                st.rerun()
        else:
            st.info("No custom statements added yet.")
    
    # Tab 3: Quiz Settings
    with settings_tabs[2]:
        st.subheader("Quiz Settings")
        
        # Maximum statements per quiz
        max_statements = st.slider(
            "Maximum statements per quiz session:",
            min_value=1,
            max_value=10,
            value=global_settings.get("max_statements_per_quiz", 5),
            step=1
        )
        global_settings["max_statements_per_quiz"] = max_statements
        
        # Display current settings summary
        st.subheader("Current Settings Summary")
        
        # Calculate total statements
        total_statements = len(global_settings.get("selected_statements", [])) + len(global_settings.get("custom_statements", []))
        
        # Create summary dataframe
        summary_data = {
            "Setting": [
                "Selected Statements", 
                "Custom Statements", 
                "Total Available Statements",
                "Max Statements Per Quiz"
            ],
            "Value": [
                len(global_settings.get("selected_statements", [])),
                len(global_settings.get("custom_statements", [])),
                total_statements,
                global_settings.get("max_statements_per_quiz", 5)
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Warning if no statements selected
        if total_statements == 0:
            st.warning("No statements available. Please select statements or add custom statements.")
        
        # Display selected statements
        if global_settings.get("selected_statements", []):
            st.subheader("Selected Statements")
            selected_texts = [statements[i] for i in global_settings.get("selected_statements", [])]
            selected_df = pd.DataFrame({"Statement": selected_texts})
            st.dataframe(selected_df, use_container_width=True, hide_index=True)
        
        # Display custom statements
        if global_settings.get("custom_statements", []):
            st.subheader("Custom Statements")
            custom_df = pd.DataFrame({"Statement": global_settings.get("custom_statements", [])})
            st.dataframe(custom_df, use_container_width=True, hide_index=True)
        
        # Save button
        if st.button("Save All Settings"):
            if save_global_settings("user_settings", global_settings):
                st.success("Settings saved successfully!")
            else:
                st.error("Failed to save settings. Please try again.") 