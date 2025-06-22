import streamlit as st
import pandas as pd
import copy
from services.statement_service import get_all_statements, get_all_categories, get_statements_by_category, get_all_digcomp_statements, get_subcategories, get_statements_by_subcategory, CURRENT_STATEMENTS, get_category_for_statement
from services.db.crud._settings import get_global_settings, save_global_settings
from services.db.crud._prompts import get_user_prompts, get_all_prompts
from services.enrichment_service import DEFAULT_PROMPT, BASIC_PROMPT, DIGCOMP_FEW_SHOT_PROMPT, GENERAL_FEW_SHOT_PROMPT

def display_user_settings():
    st.title("Global Settings")
    
    st.markdown("""
    Configure the global assessment experience. These settings affect all users and determine 
    which statements are included in assessments and how the system behaves.
    """)
    
    # Get global settings
    global_settings = get_global_settings("user_settings")
    
    if not global_settings:
        st.error("Failed to load global settings. Please try again later.")
        return
    
    # Store original settings for change detection using deep copy
    if "original_settings" not in st.session_state:
        st.session_state.original_settings = copy.deepcopy(global_settings)
    
    # Current Configuration Overview
    st.markdown("---")
    
    # Calculate summary data for the overview
    total_categories = len(global_settings.get("selected_categories", []))
    total_subcategories = sum(len(subcats) for subcats in global_settings.get("selected_subcategories", {}).values())
    total_custom = len(global_settings.get("custom_statements", []))
    total_individual = len(global_settings.get("selected_statements", []))
    
    st.markdown("### Current Configuration")
    overview_text = f"**{total_categories}** categories, **{total_subcategories}** subcategories, **{total_individual}** individual statements, **{total_custom}** custom statements"
    st.markdown(overview_text)
    
    st.markdown("---")
    
    # Main configuration tabs
    config_tabs = st.tabs([
        "Statement Configuration", 
        "AI Configuration", 
        "System Configuration",
        "Settings Summary"
    ])
    
    # Tab 1: Statement Configuration
    with config_tabs[0]:
        display_statement_configuration(global_settings)
    
    # Tab 2: AI Configuration  
    with config_tabs[1]:
        display_ai_configuration(global_settings)
    
    # Tab 3: System Configuration
    with config_tabs[2]:
        display_system_configuration(global_settings)
    
    # Tab 4: Settings Summary
    with config_tabs[3]:
        display_settings_overview(global_settings)

def display_settings_overview(global_settings):
    """Display detailed settings overview"""
    st.subheader("Settings Overview")
    
    # Create overview columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Categories", 
            len(global_settings.get("selected_categories", []))
        )
    
    with col2:
        subcategory_count = sum(len(subcats) for subcats in global_settings.get("selected_subcategories", {}).values())
        st.metric("Subcategories", subcategory_count)
    
    with col3:
        st.metric(
            "Individual Statements", 
            len(global_settings.get("selected_statements", []))
        )
    
    with col4:
        st.metric(
            "Custom Statements", 
            len(global_settings.get("custom_statements", []))
        )
    
    # System settings overview
    st.markdown("### System Configuration")
    
    system_col1, system_col2 = st.columns(2)
    
    with system_col1:
        source = "DigiComp Framework" if global_settings.get("statement_source", "default") == "digcomp" else "Default Statements"
        st.markdown(f"**Statement Source:** {source}")
        
        profile_eval = "Enabled" if global_settings.get("profile_evaluation_enabled", True) else "Disabled"
        st.markdown(f"**Profile Evaluation:** {profile_eval}")
    
    with system_col2:
        evaluation_mode = "Multiple Attempts" if global_settings.get("evaluation_enabled", True) else "Single Attempt"
        st.markdown(f"**Statement Generation:** {evaluation_mode}")
        
        competency = "Enabled" if global_settings.get("competency_questions_enabled", True) else "Disabled"
        st.markdown(f"**Competency Questions:** {competency}")
    
    # Selected items details
    if global_settings.get("selected_categories", []):
        st.markdown("### Selected Categories")
        categories_df = pd.DataFrame({
            "Category": global_settings.get("selected_categories", [])
        })
        st.dataframe(categories_df, use_container_width=True, hide_index=True)
    
    # Selected subcategories
    selected_subcategories = global_settings.get("selected_subcategories", {})
    if any(selected_subcategories.values()):
        st.markdown("### Selected Subcategories")
        subcategories_data = []
        for category, subcats in selected_subcategories.items():
            for subcat in subcats:
                subcategories_data.append({"Category": category, "Subcategory": subcat})
        if subcategories_data:
            subcategories_df = pd.DataFrame(subcategories_data)
            st.dataframe(subcategories_df, use_container_width=True, hide_index=True)
    
    # Custom statements
    if global_settings.get("custom_statements", []):
        st.markdown("### Custom Statements")
        custom_df = pd.DataFrame({
            "Statement": global_settings.get("custom_statements", [])
        })
        st.dataframe(custom_df, use_container_width=True, hide_index=True)

def display_statement_configuration(global_settings):
    """Display statement configuration section"""
    st.subheader("Statement Configuration")
    st.markdown("Configure which statements are included in assessments.")
    
    # Statement source selection
    st.markdown("#### Statement Source")
    statement_source = st.radio(
        "Choose the source of statements:",
        ["Default Statements", "DigiComp Framework"],
        index=0 if global_settings.get("statement_source", "default") == "default" else 1,
        horizontal=True
    )
    
    global_settings["statement_source"] = "default" if statement_source == "Default Statements" else "digcomp"
    
    st.markdown("---")
    
    # Statement selection based on source
    if global_settings.get("statement_source", "default") == "digcomp":
        display_digcomp_selection(global_settings)
    else:
        display_default_selection(global_settings)
    
    st.markdown("---")
    
    # Custom statements section
    st.markdown("#### Custom Statements")
    st.markdown("Add custom statements that will be included in all assessments.")
    
    display_custom_statements(global_settings)
    
    # Save button for statement configuration
    st.markdown("---")
    
    # Check if there are unsaved changes (moved to bottom after all UI interactions)
    original_statements = st.session_state.original_settings.get("selected_statements", [])
    original_categories = st.session_state.original_settings.get("selected_categories", [])
    original_subcategories = st.session_state.original_settings.get("selected_subcategories", {})
    original_custom = st.session_state.original_settings.get("custom_statements", [])
    original_source = st.session_state.original_settings.get("statement_source", "default")
    
    # Current settings
    current_statements = global_settings.get("selected_statements", [])
    current_categories = global_settings.get("selected_categories", [])
    current_subcategories = global_settings.get("selected_subcategories", {})
    current_custom = global_settings.get("custom_statements", [])
    current_source = global_settings.get("statement_source", "default")
    
    statements_changed = (
        set(original_statements) != set(current_statements) or
        set(original_categories) != set(current_categories) or
        original_subcategories != current_subcategories or
        original_custom != current_custom or
        original_source != current_source
    )
    
    if statements_changed:
        st.warning("⚠️ You have unsaved changes in statement configuration.")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Save Statement Settings", key="save_statement_settings", type="primary"):
            if save_global_settings("user_settings", global_settings):
                # Update original settings for this section
                st.session_state.original_settings["selected_statements"] = copy.deepcopy(global_settings.get("selected_statements", []))
                st.session_state.original_settings["selected_categories"] = copy.deepcopy(global_settings.get("selected_categories", []))
                st.session_state.original_settings["selected_subcategories"] = copy.deepcopy(global_settings.get("selected_subcategories", {}))
                st.session_state.original_settings["custom_statements"] = copy.deepcopy(global_settings.get("custom_statements", []))
                st.session_state.original_settings["statement_source"] = global_settings.get("statement_source", "default")
                st.success("Statement settings saved successfully!")
                st.rerun()
            else:
                st.error("Failed to save statement settings. Please try again.")

def display_digcomp_selection(global_settings):
    """Display DigiComp statement selection interface"""
    all_available_statements = get_all_digcomp_statements()
    selected_categories = global_settings.get("selected_categories", [])
    selected_subcategories = global_settings.get("selected_subcategories", {})
    selected_statements = global_settings.get("selected_statements", [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Select by Category")
        categories = get_all_categories()
        
        for i, category in enumerate(categories):
            st.markdown(f"**{category}**")
            
            # Category selection checkbox
            is_category_selected = st.checkbox(
                f"Select All - {category}",
                value=category in selected_categories,
                key=f"category_{i}"
            )
            
            # Update category selection
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
                # Remove statements from this category
                category_statements = get_statements_by_category(category)
                for statement in category_statements:
                    statement_index = all_available_statements.index(statement) if statement in all_available_statements else -1
                    if statement_index >= 0 and statement_index in selected_statements:
                        remove_statement = True
                        for cat, subcats in selected_subcategories.items():
                            if cat != category:
                                for subcat in subcats:
                                    subcat_statements = get_statements_by_subcategory(cat, subcat)
                                    if statement in subcat_statements:
                                        remove_statement = False
                                        break
                                if not remove_statement:
                                    break
                        
                        if remove_statement:
                            selected_statements.remove(statement_index)
            
            # Subcategory selection
            subcategories = get_subcategories(category)
            if category not in selected_subcategories:
                selected_subcategories[category] = []
            
            for subcategory in subcategories:
                is_subcategory_selected = st.checkbox(
                    subcategory,
                    value=subcategory in selected_subcategories.get(category, []),
                    key=f"subcategory_{category}_{subcategory.replace(' ', '_')}"
                )
                
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
                    # Remove statements from this subcategory
                    if category not in selected_categories:
                        subcat_statements = get_statements_by_subcategory(category, subcategory)
                        for statement in subcat_statements:
                            statement_index = all_available_statements.index(statement) if statement in all_available_statements else -1
                            if statement_index >= 0 and statement_index in selected_statements:
                                remove_statement = True
                                for cat, subcats in selected_subcategories.items():
                                    if cat == category and subcategory in subcats:
                                        continue
                                    
                                    for subcat in subcats:
                                        subcat_statements = get_statements_by_subcategory(cat, subcat)
                                        if statement in subcat_statements:
                                            remove_statement = False
                                            break
                                    
                                    if not remove_statement:
                                        break
                                
                                if remove_statement and statement_index in selected_statements:
                                    selected_statements.remove(statement_index)
            
            # Add separator between categories
            st.markdown("---")
    
    global_settings["selected_categories"] = selected_categories
    global_settings["selected_subcategories"] = selected_subcategories
    
    with col2:
        st.markdown("#### Select Individual Statements")
        
        statement_filter = st.text_input("Filter statements:", key="statement_filter")
        
        for i, statement in enumerate(all_available_statements):
            if statement_filter and statement_filter.lower() not in statement.lower():
                continue
            
            category, subcategory = get_category_for_statement(statement)
            is_selected_by_category = category in selected_categories
            is_selected_by_subcategory = category in selected_subcategories and subcategory in selected_subcategories[category]
            
            disabled = is_selected_by_category or is_selected_by_subcategory
            
            if disabled:
                st.checkbox(
                    statement,
                    value=True,
                    key=f"statement_disabled_{i}",
                    disabled=True,
                    help=f"Selected via: {category}" if is_selected_by_category else f"Selected via: {subcategory}"
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
    
    global_settings["selected_statements"] = selected_statements
    
    # Clear selections button
    if st.button("Clear All Selections", key="clear_all_selections_btn"):
        global_settings["selected_statements"] = []
        global_settings["selected_categories"] = []
        global_settings["selected_subcategories"] = {}
        save_global_settings("user_settings", global_settings)
        st.rerun()

def display_default_selection(global_settings):
    """Display default statement selection interface"""
    all_available_statements = CURRENT_STATEMENTS
    selected_statements = global_settings.get("selected_statements", [])
    
    st.info("The default statement set does not have categories. Select individual statements below.")
    
    st.markdown("#### Select Individual Statements")
    statement_filter = st.text_input("Filter statements:", key="statement_filter")
    
    for i, statement in enumerate(all_available_statements):
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
    
    global_settings["selected_statements"] = selected_statements

def display_custom_statements(global_settings):
    """Display custom statements management"""
    custom_statements = global_settings.get("custom_statements", [])
    
    # Add new statement
    new_statement = st.text_input("Add a new statement:", key="new_custom_statement")
    if st.button("Add Statement", key="add_custom_statement_btn") and new_statement:
        if new_statement not in custom_statements:
            custom_statements.append(new_statement)
            global_settings["custom_statements"] = custom_statements
            save_global_settings("user_settings", global_settings)
            st.success(f"Added: {new_statement}")
            st.rerun()
        else:
            st.error("This statement already exists in your custom list.")
    
    # Display existing custom statements
    if custom_statements:
        st.markdown("**Current Custom Statements:**")
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
        
        if st.button("Clear All Custom Statements", key="clear_all_custom_statements_btn"):
            global_settings["custom_statements"] = []
            save_global_settings("user_settings", global_settings)
            st.rerun()
    else:
        st.info("No custom statements added yet.")

def display_ai_configuration(global_settings):
    """Display AI configuration section"""
    st.subheader("AI Configuration")
    st.markdown("Configure AI-powered features and evaluation settings.")
    
    # Profile evaluation
    st.markdown("#### Profile Evaluation")
    profile_evaluation_enabled = st.toggle(
        "Enable AI Profile Evaluation", 
        value=global_settings.get("profile_evaluation_enabled", True),
        help="AI will evaluate user profiles and provide improvement suggestions."
    )
    global_settings["profile_evaluation_enabled"] = profile_evaluation_enabled
    
    st.markdown("---")
    
    # Statement generation
    st.markdown("#### Statement Generation")
    evaluation_enabled = st.toggle(
        "Enable Multiple Attempts (Threshold-based Generation)", 
        value=global_settings.get("evaluation_enabled", True),
        help="Generate multiple versions and select the best one based on quality thresholds."
    )
    global_settings["evaluation_enabled"] = evaluation_enabled
    
    if evaluation_enabled:
        max_attempts = st.slider(
            "Maximum Generation Attempts", 
            min_value=1, 
            max_value=10, 
            value=global_settings.get("evaluation_max_attempts", 5),
            help="Maximum attempts to generate a statement that meets quality thresholds."
        )
        global_settings["evaluation_max_attempts"] = max_attempts
        st.info("The system will generate multiple versions and select the best one.")
    else:
        global_settings["evaluation_max_attempts"] = 1
        st.info("The system will generate a single version without evaluation.")
    
    st.markdown("---")

    # Assessment features
    st.markdown("#### Assessment Features")
    competency_questions_enabled = st.toggle(
        "Enable Competency Assessment Questions", 
        value=global_settings.get("competency_questions_enabled", True),
        help="Users will assess their competency level for each statement."
    )
    global_settings["competency_questions_enabled"] = competency_questions_enabled

    if competency_questions_enabled:
        st.info("Users will rate their competency levels. Results shown in Competency Assessment tab.")
    else:
        st.info("Competency assessment questions will be hidden.")
    
    # Save button for AI configuration
    st.markdown("---")
    
    # Check if there are unsaved changes (moved to bottom after all UI interactions)
    original_profile_eval = st.session_state.original_settings.get("profile_evaluation_enabled", True)
    original_evaluation = st.session_state.original_settings.get("evaluation_enabled", True)
    original_max_attempts = st.session_state.original_settings.get("evaluation_max_attempts", 5)
    original_competency = st.session_state.original_settings.get("competency_questions_enabled", True)
    
    # Current settings
    current_profile_eval = global_settings.get("profile_evaluation_enabled", True)
    current_evaluation = global_settings.get("evaluation_enabled", True)
    current_max_attempts = global_settings.get("evaluation_max_attempts", 5)
    current_competency = global_settings.get("competency_questions_enabled", True)
    
    ai_changed = (
        original_profile_eval != current_profile_eval or
        original_evaluation != current_evaluation or
        original_max_attempts != current_max_attempts or
        original_competency != current_competency
    )
    
    if ai_changed:
        st.warning("⚠️ You have unsaved changes in AI configuration.")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Save AI Settings", key="save_ai_settings", type="primary"):
            if save_global_settings("user_settings", global_settings):
                # Update original settings for this section
                st.session_state.original_settings["profile_evaluation_enabled"] = global_settings.get("profile_evaluation_enabled", True)
                st.session_state.original_settings["evaluation_enabled"] = global_settings.get("evaluation_enabled", True)
                st.session_state.original_settings["evaluation_max_attempts"] = global_settings.get("evaluation_max_attempts", 5)
                st.session_state.original_settings["competency_questions_enabled"] = global_settings.get("competency_questions_enabled", True)
                st.success("AI settings saved successfully!")
                st.rerun()
            else:
                st.error("Failed to save AI settings. Please try again.")

def display_system_configuration(global_settings):
    """Display system configuration section"""
    st.subheader("System Configuration")
    st.markdown("Configure system-wide prompt templates and behavior.")
    
    # Prompt settings
    st.markdown("#### Prompt Template Selection")
    st.markdown("Select the prompt template used for statement enrichment.")
    
    # Get all prompts
    all_prompts = get_all_prompts()
    
    if not all_prompts:
        all_prompts = []
    
    # Add default prompts
    default_prompts = [
        {"id": 0, "name": "Default", "content": DEFAULT_PROMPT},
        {"id": -1, "name": "Basic", "content": BASIC_PROMPT},
        {"id": -2, "name": "DigComp Few-Shot", "content": DIGCOMP_FEW_SHOT_PROMPT},
        {"id": -3, "name": "General Few-Shot", "content": GENERAL_FEW_SHOT_PROMPT}
    ]
    
    all_prompts = default_prompts + all_prompts
    
    # Create prompt selection
    prompt_options = {p["name"]: p["id"] for p in all_prompts}
    current_prompt_id = global_settings.get("selected_prompt_id", 0)
    
    # Find current prompt name
    current_prompt_name = "Default"
    for p in all_prompts:
        if p["id"] == current_prompt_id:
            current_prompt_name = p["name"]
            break
    
    selected_prompt_name = st.selectbox(
        "Select Prompt Template:",
        options=list(prompt_options.keys()),
        index=list(prompt_options.keys()).index(current_prompt_name) if current_prompt_name in prompt_options else 0
    )
    
    selected_prompt_id = prompt_options[selected_prompt_name]
    
    # Display prompt content
    selected_prompt_content = ""
    for p in all_prompts:
        if p["id"] == selected_prompt_id:
            selected_prompt_content = p["content"]
            break
    
    st.text_area(
        "Prompt Content:", 
        value=selected_prompt_content, 
        height=300, 
        disabled=True,
        help="Preview of the selected prompt template"
    )
    
    # Update settings
    global_settings["selected_prompt_id"] = selected_prompt_id
    
    # Save button for system configuration
    st.markdown("---")
    
    # Check if there are unsaved changes (moved to bottom after all UI interactions)
    original_prompt_id = st.session_state.original_settings.get("selected_prompt_id", 0)
    current_prompt_id = global_settings.get("selected_prompt_id", 0)
    
    system_changed = original_prompt_id != current_prompt_id
    
    if system_changed:
        st.warning("⚠️ You have unsaved changes in system configuration.")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Save System Settings", key="save_system_settings", type="primary"):
            if save_global_settings("user_settings", global_settings):
                # Update original settings for this section
                st.session_state.original_settings["selected_prompt_id"] = global_settings.get("selected_prompt_id", 0)
                st.success("System settings saved successfully!")
                st.rerun()
            else:
                st.error("Failed to save system settings. Please try again.") 