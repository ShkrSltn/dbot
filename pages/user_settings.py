import streamlit as st
import pandas as pd
from services.statement_service import get_all_statements
from services.db.crud._settings import get_global_settings, save_global_settings
from services.db.crud._prompts import get_user_prompts, get_all_prompts
from services.enrichment_service import DEFAULT_PROMPT, BASIC_PROMPT, DIGCOMP_FEW_SHOT_PROMPT, GENERAL_FEW_SHOT_PROMPT

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
    settings_tabs = st.tabs(["Select Statements", "Custom Statements", "Quiz Settings", "AI Features", "Prompt Settings"])
    
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
            if st.button("Clear All Statements", key="clear_all_statements_btn", on_click=clear_all_statements):
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
        if st.button("Add Statement", key="add_custom_statement_btn") and new_statement:
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
            if st.button("Clear All Custom Statements", key="clear_all_custom_statements_btn"):
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
    
    # Tab 4: AI Features
    with settings_tabs[3]:
        st.subheader("AI Features")
        st.markdown("""
        Configure AI-powered features and evaluation settings.
        """)
        
        # Profile evaluation settings
        st.markdown("### Profile Evaluation")
        profile_evaluation_enabled = st.toggle(
            "Enable AI Profile Evaluation", 
            value=global_settings.get("profile_evaluation_enabled", True),
            help="When enabled, AI will evaluate user profiles and provide suggestions for improvement."
        )
        
        # Update global settings
        global_settings["profile_evaluation_enabled"] = profile_evaluation_enabled
        
        # Statement generation settings
        st.markdown("### Statement Generation")
        
        # Toggle for evaluation mode
        evaluation_enabled = st.toggle(
            "Enable Multiple Attempts (Threshold-based Generation)", 
            value=global_settings.get("evaluation_enabled", True),
            help="When enabled, the system will generate multiple versions of statements and select the best one based on quality thresholds."
        )
        
        # Update global settings
        global_settings["evaluation_enabled"] = evaluation_enabled
        
        # Explanation
        if evaluation_enabled:
            st.info("The system will generate multiple versions of statements and select the best one based on quality thresholds.")
        else:
            st.info("The system will generate a single version of statements without evaluation.")
        
        # Slider for max attempts (only shown if evaluation is enabled)
        if evaluation_enabled:
            max_attempts = st.slider(
                "Maximum Generation Attempts", 
                min_value=1, 
                max_value=10, 
                value=global_settings.get("evaluation_max_attempts", 5),
                help="Maximum number of attempts to generate a statement that meets quality thresholds."
            )
            
            # Update global settings
            global_settings["evaluation_max_attempts"] = max_attempts
        else:
            # Set a default value when disabled
            global_settings["evaluation_max_attempts"] = 1
    
    # Tab 5: Prompt Settings
    with settings_tabs[4]:
        st.subheader("Prompt Settings")
        st.markdown("""
        Select which prompt template to use for statement enrichment.
        The selected prompt will be used for all statement enrichments.
        """)
        
        # Get all prompts
        all_prompts = get_all_prompts()
        
        if not all_prompts:
            st.warning("No custom prompts found. Using default prompt.")
            # Add default prompts to the list
            all_prompts = [
                {
                    "id": 0,
                    "user_id": None,
                    "name": "Default",
                    "content": DEFAULT_PROMPT, 
                    "created_at": None
                },
                {
                    "id": -1,
                    "user_id": None,
                    "name": "Basic",
                    "content": BASIC_PROMPT,
                    "created_at": None
                },
                {
                    "id": -2,
                    "user_id": None,
                    "name": "DigComp Few-Shot",
                    "content": DIGCOMP_FEW_SHOT_PROMPT,
                    "created_at": None
                },
                {
                    "id": -3,
                    "user_id": None,
                    "name": "General Few-Shot",
                    "content": GENERAL_FEW_SHOT_PROMPT,
                    "created_at": None
                }
            ]
        else:
            # Add default prompts to the beginning of the list
            all_prompts.insert(0, {
                "id": 0,
                "user_id": None,
                "name": "Default",
                "content": DEFAULT_PROMPT,
                "created_at": None
            })
            all_prompts.insert(1, {
                "id": -1,
                "user_id": None,
                "name": "Basic",
                "content": BASIC_PROMPT,
                "created_at": None
            })
            all_prompts.insert(2, {
                "id": -2,
                "user_id": None,
                "name": "DigComp Few-Shot",
                "content": DIGCOMP_FEW_SHOT_PROMPT,
                "created_at": None
            })
            all_prompts.insert(3, {
                "id": -3,
                "user_id": None,
                "name": "General Few-Shot",
                "content": GENERAL_FEW_SHOT_PROMPT,
                "created_at": None
            })

        # Create a dictionary of prompt names to IDs for the selectbox
        prompt_options = {p["name"]: p["id"] for p in all_prompts}
        
        # Get currently selected prompt ID from settings
        current_prompt_id = global_settings.get("selected_prompt_id", 0)
        
        # Find the name of the current prompt
        current_prompt_name = "Default"
        for p in all_prompts:
            if p["id"] == current_prompt_id:
                current_prompt_name = p["name"]
                break
        
        # Create selectbox for prompt selection
        selected_prompt_name = st.selectbox(
            "Select Prompt Template:",
            options=list(prompt_options.keys()),
            index=list(prompt_options.keys()).index(current_prompt_name) if current_prompt_name in prompt_options else 0
        )
        
        # Get the ID of the selected prompt
        selected_prompt_id = prompt_options[selected_prompt_name]
        
        # Display the content of the selected prompt
        selected_prompt_content = ""
        for p in all_prompts:
            if p["id"] == selected_prompt_id:
                selected_prompt_content = p["content"]
                break
        
        st.text_area("Prompt Content:", value=selected_prompt_content, height=300, disabled=True)
        
        # Update the global settings with the selected prompt ID
        if selected_prompt_id != current_prompt_id:
            global_settings["selected_prompt_id"] = selected_prompt_id
            st.info(f"Prompt '{selected_prompt_name}' selected. Click 'Save All Settings' to apply changes.")
    
    # Summary section
    with st.expander("Settings Summary", expanded=False):
        # Add profile evaluation to summary
        summary_data = {
            "Setting": [
                "Selected Statements",
                "Custom Statements",
                "Total Statements",
                "Statements Per Quiz",
                "Profile Evaluation",
                "Statement Generation",
                "Max Generation Attempts"
            ],
            "Value": [
                str(len(global_settings.get("selected_statements", []))),
                str(len(global_settings.get("custom_statements", []))),
                str(len(global_settings.get("selected_statements", [])) + 
                len(global_settings.get("custom_statements", []))),
                str(global_settings.get("max_statements_per_quiz", 5)),
                "Enabled" if global_settings.get("profile_evaluation_enabled", True) else "Disabled",
                "Multiple Attempts" if global_settings.get("evaluation_enabled", True) else "Single Attempt",
                str(global_settings.get("evaluation_max_attempts", 5))
            ]
        }
        
        # Явно преобразуем все значения в строки
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
    
    # Единственная кнопка Save All Settings в конце страницы
    if st.button("Save All Settings", key="save_all_settings_main"):
        if save_global_settings("user_settings", global_settings):
            st.success("Settings saved successfully!")
        else:
            st.error("Failed to save settings. Please try again.") 