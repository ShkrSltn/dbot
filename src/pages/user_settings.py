import streamlit as st
import pandas as pd
from services.statement_service import get_all_statements, get_all_categories, get_statements_by_category, get_all_digcomp_statements, get_subcategories, get_statements_by_subcategory, CURRENT_STATEMENTS, get_category_for_statement
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
    settings_tabs = st.tabs(["Statement Selection", "Custom Statements", "Quiz Settings", "AI Features", "Prompt Settings"])
    
    # Tab 1: Combined Statement Selection (Groups + Individual Statements)
    with settings_tabs[0]:
        st.subheader("Select Statements")
        st.markdown("""
        Choose which statements you want to include in assessments.
        You can select by categories or individual statements.
        """)
        
        # Statement source selection
        st.markdown("### Statement Source")
        statement_source = st.radio(
            "Choose the source of statements:",
            ["Default Statements", "DigiComp Framework"],
            index=0 if global_settings.get("statement_source", "default") == "default" else 1
        )
        
        # Save statement source selection
        global_settings["statement_source"] = "default" if statement_source == "Default Statements" else "digcomp"
        
        # Create columns for selection methods
        col1, col2 = st.columns(2)
        
        # Get selected categories and subcategories
        selected_categories = global_settings.get("selected_categories", [])
        selected_subcategories = global_settings.get("selected_subcategories", {})
        
        # Get selected statements
        selected_statements = global_settings.get("selected_statements", [])
        
        # Determine which statements to show based on the selected source
        if global_settings.get("statement_source", "default") == "digcomp":
            # Show all DigiComp statements
            all_available_statements = get_all_digcomp_statements()
            
            with col1:
                st.markdown("### Select by Category")
                categories = get_all_categories()
                
                # Create an expander for each category
                for i, category in enumerate(categories):
                    with st.expander(f"{category}", expanded=category in selected_categories):
                        # Checkbox for selecting entire category
                        is_category_selected = st.checkbox(
                            f"Select All - {category}",
                            value=category in selected_categories,
                            key=f"category_{i}"
                        )
                        
                        # Update selected categories
                        if is_category_selected and category not in selected_categories:
                            selected_categories.append(category)
                            
                            # Sync with individual statements
                            category_statements = get_statements_by_category(category)
                            for statement in category_statements:
                                statement_index = all_available_statements.index(statement) if statement in all_available_statements else -1
                                if statement_index >= 0 and statement_index not in selected_statements:
                                    selected_statements.append(statement_index)
                                    
                        elif not is_category_selected and category in selected_categories:
                            selected_categories.remove(category)
                            
                            # Remove statements from this category in selected_statements
                            category_statements = get_statements_by_category(category)
                            for statement in category_statements:
                                statement_index = all_available_statements.index(statement) if statement in all_available_statements else -1
                                if statement_index >= 0 and statement_index in selected_statements:
                                    # Only remove if not selected in a subcategory
                                    remove_statement = True
                                    for cat, subcats in selected_subcategories.items():
                                        if cat != category:  # Skip current category
                                            for subcat in subcats:
                                                subcat_statements = get_statements_by_subcategory(cat, subcat)
                                                if statement in subcat_statements:
                                                    remove_statement = False
                                                    break
                                        if not remove_statement:
                                            break
                                    
                                    if remove_statement:
                                        selected_statements.remove(statement_index)
                        
                        # Get subcategories for this category
                        subcategories = get_subcategories(category)
                        
                        # Initialize dictionary for this category if not exists
                        if category not in selected_subcategories:
                            selected_subcategories[category] = []
                        
                        # Create checkboxes for subcategories
                        for subcategory in subcategories:
                            is_subcategory_selected = st.checkbox(
                                subcategory,
                                value=subcategory in selected_subcategories.get(category, []),
                                key=f"subcategory_{category}_{subcategory.replace(' ', '_')}"
                            )
                            
                            # Update selected subcategories
                            if is_subcategory_selected and subcategory not in selected_subcategories[category]:
                                selected_subcategories[category].append(subcategory)
                                
                                # Sync with individual statements
                                subcat_statements = get_statements_by_subcategory(category, subcategory)
                                for statement in subcat_statements:
                                    statement_index = all_available_statements.index(statement) if statement in all_available_statements else -1
                                    if statement_index >= 0 and statement_index not in selected_statements:
                                        selected_statements.append(statement_index)
                                        
                            elif not is_subcategory_selected and subcategory in selected_subcategories[category]:
                                selected_subcategories[category].remove(subcategory)
                                
                                # Remove statements from this subcategory in selected_statements
                                # Only if not part of a selected category
                                if category not in selected_categories:
                                    subcat_statements = get_statements_by_subcategory(category, subcategory)
                                    for statement in subcat_statements:
                                        statement_index = all_available_statements.index(statement) if statement in all_available_statements else -1
                                        if statement_index >= 0 and statement_index in selected_statements:
                                            # Check if statement is in another selected subcategory
                                            remove_statement = True
                                            for cat, subcats in selected_subcategories.items():
                                                if cat == category and subcategory in subcats:
                                                    continue  # Skip current subcategory
                                                
                                                for subcat in subcats:
                                                    subcat_statements = get_statements_by_subcategory(cat, subcat)
                                                    if statement in subcat_statements:
                                                        remove_statement = False
                                                        break
                                                
                                                if not remove_statement:
                                                    break
                                            
                                            if remove_statement:
                                                if statement_index in selected_statements:
                                                    selected_statements.remove(statement_index)
                
                # Save selected categories and subcategories
                global_settings["selected_categories"] = selected_categories
                global_settings["selected_subcategories"] = selected_subcategories
            
            with col2:
                st.markdown("### Select Individual Statements")
                
                # Create a filter input
                statement_filter = st.text_input("Filter statements:", key="statement_filter")
                
                # Create checkboxes for each statement, with filtering
                for i, statement in enumerate(all_available_statements):
                    # Apply filter if present
                    if statement_filter and statement_filter.lower() not in statement.lower():
                        continue
                    
                    # Get category and subcategory for this statement
                    category, subcategory = get_category_for_statement(statement)
                    
                    # Check if statement is already selected via category or subcategory
                    is_selected_by_category = category in selected_categories
                    is_selected_by_subcategory = category in selected_subcategories and subcategory in selected_subcategories[category]
                    
                    # If statement is already selected by category/subcategory, disable the checkbox
                    disabled = is_selected_by_category or is_selected_by_subcategory
                    
                    if disabled:
                        st.checkbox(
                            statement,
                            value=True,
                            key=f"statement_disabled_{i}",
                            disabled=True,
                            help=f"This statement is selected via the category: {category}" if is_selected_by_category else f"This statement is selected via the subcategory: {subcategory}"
                        )
                    else:
                        is_selected = st.checkbox(
                            statement,
                            value=i in selected_statements,
                            key=f"statement_{i}"
                        )
                        
                        if is_selected and i not in selected_statements:
                            selected_statements.append(i)
                        elif not is_selected and i in selected_statements:
                            selected_statements.remove(i)
                
        else:
            # Default statements
            all_available_statements = CURRENT_STATEMENTS
            
            with col1:
                st.info("The default statement set does not have categories. Please select individual statements.")
            
            with col2:
                st.markdown("### Select Individual Statements")
                
                # Create a filter input
                statement_filter = st.text_input("Filter statements:", key="statement_filter")
                
                # Create checkboxes for each statement, with filtering
                for i, statement in enumerate(all_available_statements):
                    # Apply filter if present
                    if statement_filter and statement_filter.lower() not in statement.lower():
                        continue
                    
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
        
        # Show selected statements summary
        st.subheader("Selected Statements Summary")
        
        # Calculate selected statements from various sources
        category_statements = []
        subcategory_statements = []
        individual_statements = []
        
        if global_settings.get("statement_source", "default") == "digcomp":
            # Get statements from categories
            for category in selected_categories:
                category_statements.extend(get_statements_by_category(category))
            
            # Get statements from subcategories
            for category, subcategories in selected_subcategories.items():
                if category not in selected_categories:  # Skip if entire category is already selected
                    for subcategory in subcategories:
                        subcategory_statements.extend(get_statements_by_subcategory(category, subcategory))
            
            # Get statements from individual selection
            for index in selected_statements:
                if index < len(all_available_statements):
                    statement = all_available_statements[index]
                    # Only add if not already in categories or subcategories
                    if statement not in category_statements and statement not in subcategory_statements:
                        individual_statements.append(statement)
        else:
            # Get statements from individual selection
            for index in selected_statements:
                if index < len(all_available_statements):
                    individual_statements.append(all_available_statements[index])
        
        # Remove duplicates
        all_selected = list(set(category_statements + subcategory_statements + individual_statements))
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Categories", len(selected_categories))
        with col2:
            subcategory_count = sum(len(subcats) for subcats in selected_subcategories.values())
            st.metric("Subcategories", subcategory_count)
        with col3:
            st.metric("Total Statements", len(all_selected))
        
        # Display selected statements
        if all_selected:
            df = pd.DataFrame({"Statement": all_selected})
            st.dataframe(df, use_container_width=True)
            
            # Функция для очистки всех выбранных утверждений
            def clear_all_selections():
                global_settings = get_global_settings("user_settings")
                global_settings["selected_statements"] = []
                global_settings["selected_categories"] = []
                global_settings["selected_subcategories"] = {}
                save_global_settings("user_settings", global_settings)

            # Clear selection button
            if st.button("Clear All Selections", key="clear_all_selections_btn", on_click=clear_all_selections):
                pass
        else:
            st.warning("No statements selected. Please select at least one statement, category, or subcategory.")
    
    # Tab 2: Custom Statements
    with settings_tabs[1]:
        st.subheader("Add Custom Statements")
        st.markdown("""
        Add custom statements that will be included in assessments.
        These statements will be added to any selected from the categories or individual selections.
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
            max_value=30,
            value=global_settings.get("max_statements_per_quiz", 5),
            step=1
        )
        global_settings["max_statements_per_quiz"] = max_statements
        
        # Display current settings summary
        st.subheader("Current Settings Summary")
        
        # Calculate total statements
        total_statements = len(all_selected) if 'all_selected' in locals() else 0
        if "custom_statements" in global_settings:
            total_statements += len(global_settings["custom_statements"])
        
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

        # Toggle for competency questions
        st.markdown("### Quiz Features")
        competency_questions_enabled = st.toggle(
            "Enable Competency Assessment Questions", 
            value=global_settings.get("competency_questions_enabled", True),
            help="When enabled, users will be asked to assess their competency level for each statement in the quiz."
        )

        # Update global settings
        global_settings["competency_questions_enabled"] = competency_questions_enabled

        # Explanation
        if competency_questions_enabled:
            st.info("Users will be asked to rate their competency level for each statement. Results will be shown in the Competency Assessment tab.")
        else:
            st.info("Competency assessment questions will be hidden. The Competency Assessment tab will not be shown in results.")
    
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
                "Selected Categories",
                "Selected Subcategories",
                "Custom Statements",
                "Total Statements",
                "Statements Per Quiz",
                "Profile Evaluation",
                "Statement Generation",
                "Max Generation Attempts"
            ],
            "Value": [
                str(len(global_settings.get("selected_categories", []))),
                str(sum(len(subcats) for subcats in global_settings.get("selected_subcategories", {}).values())),
                str(len(global_settings.get("custom_statements", []))),
                str(total_statements),
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
        
        # Display selected categories and subcategories
        if global_settings.get("selected_categories", []):
            st.subheader("Selected Categories")
            categories_df = pd.DataFrame({"Category": global_settings.get("selected_categories", [])})
            st.dataframe(categories_df, use_container_width=True, hide_index=True)
        
        # Display selected subcategories
        selected_subcategories = global_settings.get("selected_subcategories", {})
        if any(selected_subcategories.values()):
            st.subheader("Selected Subcategories")
            subcategories_data = []
            for category, subcats in selected_subcategories.items():
                for subcat in subcats:
                    subcategories_data.append({"Category": category, "Subcategory": subcat})
            if subcategories_data:
                subcategories_df = pd.DataFrame(subcategories_data)
                st.dataframe(subcategories_df, use_container_width=True, hide_index=True)
        
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