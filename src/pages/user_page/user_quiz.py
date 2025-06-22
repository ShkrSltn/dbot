import streamlit as st
import numpy as np
from services.statement_service import get_statements_from_settings, get_category_for_statement
from services.enrichment_service import enrich_statement_with_llm
from services.metrics_service import calculate_quality_metrics
from services.db.crud._quiz import save_quiz_results
from components.meta_questions import display_meta_questions, get_default_criteria, get_competency_criteria, get_meta_questions_styles
from services.db.crud._settings import get_competency_questions_enabled
import random  # Добавляем импорт для рандомизации
import datetime

def display_quiz_step():
    st.subheader("Step 2: Statement Preference Self-Assessment")
    
    # Add Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back", help="Go back to Profile step"):
            # Import the navigation function
            from pages.user_page.user_flow import navigate_back_to_step
            navigate_back_to_step(1)
    
    # Check if we have enriched statements
    if len(st.session_state.get('enriched_statements', [])) < 1:
        handle_empty_statements()
    else:
        display_quiz_interface()

def handle_empty_statements():
    # Automatically generate enriched statements when entering this step
    
    # Get statements based on user settings
    sample_statements = get_statements_from_settings()
    
    # Use all statements from settings
    # No limit - take all available statements
    
    # Create context from user profile
    context = ", ".join(
        [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v]
    )
    
    # Get generation settings from global settings
    from services.db.crud._settings import get_global_settings
    global_settings = get_global_settings("user_settings")
    
    evaluation_enabled = global_settings.get("evaluation_enabled", True) if global_settings else True
    max_attempts = global_settings.get("evaluation_max_attempts", 5) if global_settings else 5
    
    # Enrich statements
    with st.spinner("Generating statements for your self-assessment..."):
        for statement in sample_statements:
            # Get category and subcategory for the statement
            category, subcategory = get_category_for_statement(statement)
            
            # Choose generation method based on settings
            if evaluation_enabled:
                # Use threshold-based generation with multiple attempts
                from services.statement_evaluation_service import regenerate_until_threshold
                
                # Get proficiency level from profile or use default
                proficiency = st.session_state.profile.get("digital_proficiency", "Intermediate")
                if isinstance(proficiency, int):
                    # Convert numeric proficiency to string
                    proficiency_map = {
                        1: "Beginner",
                        2: "Basic",
                        3: "Intermediate", 
                        4: "Advanced",
                        5: "Expert"
                    }
                    proficiency = proficiency_map.get(proficiency, "Intermediate")
                
                # Generate with multiple attempts
                _, enriched, _, _, history = regenerate_until_threshold(
                    context=context,
                    original_statement=statement,
                    proficiency=proficiency,
                    statement_length=150,
                    max_attempts=max_attempts
                )
                
                # Get metrics from the best attempt
                metrics = history[-1]["metrics"] if history else calculate_quality_metrics(statement, enriched)
            else:
                # Use simple generation (single attempt)
                enriched = enrich_statement_with_llm(context, statement, 150)
                metrics = calculate_quality_metrics(statement, enriched)
            
            if 'enriched_statements' not in st.session_state:
                st.session_state.enriched_statements = []
            
            st.session_state.enriched_statements.append({
                "original": statement,
                "enriched": enriched,
                "metrics": metrics,
                "category": category,
                "subcategory": subcategory
            })
    
    st.success(f"Generated {len(sample_statements)} statements! You can now take the self-assessment.")
    st.rerun()

# Removed get_max_statements_setting() - no longer needed
# Now using all available statements

def display_quiz_interface():
    # Show all statements at once instead of one by one
    if 'quiz_shown_indices' not in st.session_state:
        st.session_state.quiz_shown_indices = []
    
    # Инициализируем словарь для хранения информации о порядке утверждений, если его еще нет
    if 'statement_order' not in st.session_state:
        st.session_state.statement_order = {}
    
    # Use all available statements - no limit
    total_statements = len(st.session_state.enriched_statements)
    
    # If all statements have been shown, move to results
    if len(st.session_state.quiz_shown_indices) >= total_statements:
        st.session_state.flow_step = 3
        st.rerun()
    
    # Create a unique key for this quiz iteration
    if 'current_quiz_iteration' not in st.session_state:
        st.session_state.current_quiz_iteration = 0
    
    quiz_iteration_key = f"quiz_iteration_{st.session_state.current_quiz_iteration}"
    
    # Get default criteria
    criteria = get_default_criteria()
    
    # Create a form for all statements
    with st.form(key=f"flow_preference_form_{quiz_iteration_key}"):
        st.markdown("### Compare these statements and select your preferences")
        
        # Get available statements that haven't been shown yet
        available_indices = [i for i in range(len(st.session_state.enriched_statements)) 
                             if i not in st.session_state.quiz_shown_indices]
        
        # Select statements to show in this quiz
        statements_to_show = available_indices[:total_statements - len(st.session_state.quiz_shown_indices)]
        
        # Store the statements being shown in this quiz
        if 'current_statements' not in st.session_state:
            st.session_state.current_statements = statements_to_show
        
        # Display each statement pair with its own set of questions
        for i, statement_idx in enumerate(st.session_state.current_statements):
            statement_pair = st.session_state.enriched_statements[statement_idx]
            
            # Randomly determine the order of display (original - A or B)
            order_key = f"order_{statement_idx}_{quiz_iteration_key}"
            if order_key not in st.session_state:
                # Randomly determine if original will be first (A) or second (B)
                first_is_original = random.choice([True, False])
                st.session_state[order_key] = first_is_original
            else:
                first_is_original = st.session_state[order_key]
            
            # Save the order of statements for use in processing results
            st.session_state.statement_order[statement_idx] = first_is_original
            
            # Determine which statement will be first (A), and which second (B)
            if first_is_original:
                first_statement = statement_pair["original"]
                second_statement = statement_pair["enriched"]
            else:
                first_statement = statement_pair["enriched"]
                second_statement = statement_pair["original"]
            
            # Get category and subcategory for the title
            category = statement_pair.get("category", "")
            # subcategory = statement_pair.get("subcategory", "")
            
            st.markdown("---")
            # Display category instead of "Statement Pair"
            st.markdown(f"## {category if category else f'Statement Pair {i+1}'}")
            
            # If there is a subcategory, display it as a subheader
            # if subcategory:
            #     st.markdown(f"### {subcategory}")
            
            # Create CSS for equal height containers
            st.markdown("""
            <style>
            .statement-container {
                display: flex;
                width: 100%;
                margin-bottom: 20px;

            }
            .statement-box {
                flex: 1;
                margin: 0 10px;
                padding: 15px;
                border-radius: 5px;
                background-color: #0c5f97;
            }
            .statement-title {
                font-size: 1.2rem;
                font-weight: bold;
                margin-bottom: 10px;
            }

            @media (max-width: 768px) {
                .statement-container {
                    gap: 10px;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }
                .statement-box {
                    flex: 1;
                    min-height: 150px;
                    width: 100%;
                }
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Display the statements side by side with equal height using HTML
            html_content = f"""
            <div class="statement-container">
                <div class="statement-box">
                    <div class="statement-title">A</div>
                    <div>{first_statement}</div>
                </div>
                <div class="statement-box">
                    <div class="statement-title">B</div>
                    <div>{second_statement}</div>
                </div>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
            
           
            # Apply meta questions styles
            st.markdown(get_meta_questions_styles(), unsafe_allow_html=True)
           
            # Display meta questions using the component
            display_meta_questions(
                statement_idx=statement_idx,
                quiz_iteration_key=quiz_iteration_key,
                criteria=criteria,
                first_is_original=first_is_original,
                statement=statement_pair["original"],  # Всегда передаем оригинальное утверждение для компетенций
                show_competency=get_competency_questions_enabled()
            )
        
        # Progress indicator
        completed = len(st.session_state.quiz_shown_indices)
        progress_percentage = completed / total_statements * 100
        # st.progress(progress_percentage / 100, f"{progress_percentage:.0f}% ({completed}/{total_statements})")
        
        # Submit button for all statements
        submitted = st.form_submit_button("Submit All Responses")
        
    if submitted:
        # Add debugging for checking values
        # st.write("Debug info:")
        all_answered = True
        unanswered_questions = []
        
        # Check all answers
        for statement_idx in st.session_state.current_statements:
            # st.write(f"Checking statement {statement_idx}")
            
            # Check meta questions
            for key in criteria.keys():
                radio_key = f"radio_{key}_{statement_idx}_{quiz_iteration_key}"
                value = st.session_state.get(radio_key)
                # st.write(f"{radio_key}: {value}")
                
                if value is None:
                    all_answered = False
                    unanswered_questions.append(f"Statement {statement_idx}: {criteria[key]}")
            
            # Check competencies only if they are enabled
            competency_enabled = get_competency_questions_enabled()
            if competency_enabled:
                competency_key = f"competency_{statement_idx}_{quiz_iteration_key}"
                comp_value = st.session_state.get(competency_key)
                # st.write(f"{competency_key}: {comp_value}")
                
                if comp_value is None:
                    all_answered = False
                    unanswered_questions.append(f"Statement {statement_idx}: Competency")
        
        # st.write(f"All answered: {all_answered}")
        # st.write(f"Unanswered: {unanswered_questions}")
        
        # Original validation code...
        if not all_answered:
            st.error("Please answer all questions before submitting:")
            for question in unanswered_questions:
                st.warning(question)
            return
            
        # Process all responses
        for statement_idx in st.session_state.current_statements:
            # Collect responses for this statement
            responses = {}
            for key in criteria.keys():
                radio_key = f"radio_{key}_{statement_idx}_{quiz_iteration_key}"
                responses[key] = st.session_state[radio_key]
            
            # Add competency responses only if enabled
            competency_enabled = get_competency_questions_enabled()
            if competency_enabled:
                competency_key = f"competency_{statement_idx}_{quiz_iteration_key}"
                responses["competency"] = st.session_state.get(competency_key)
            
            # Add category and subcategory
            cat_key = f"statement_category_{statement_idx}"
            subcat_key = f"statement_subcategory_{statement_idx}"
            
            responses["category"] = st.session_state.get(cat_key)
            responses["subcategory"] = st.session_state.get(subcat_key)
            
            # Get the order of display for this statement
            first_is_original = st.session_state.statement_order.get(statement_idx, True)
            
            # Handle the submission for this statement
            handle_quiz_submission(statement_idx, responses, first_is_original)
        
        # Reset for next batch of questions if needed
        st.session_state.current_quiz_iteration += 1
        st.session_state.pop('current_statements', None)
        
        # Check if we've completed all statements
        if len(st.session_state.quiz_shown_indices) >= total_statements:
            st.session_state.flow_step = 3
        
        st.rerun()

def handle_quiz_submission(statement_idx, responses, first_is_original):
    # Initialize detailed_quiz_results if not exists
    if 'detailed_quiz_results' not in st.session_state:
        st.session_state.detailed_quiz_results = {
            "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
        }
    
    # Initialize competency results if not exists
    if 'competency_results' not in st.session_state:
        st.session_state.competency_results = []
    
    # Get current quiz iteration
    current_quiz_iteration = st.session_state.current_quiz_iteration
    quiz_iteration_key = f"quiz_iteration_{current_quiz_iteration}"
    
    # Validate responses for completeness
    required_keys = list(get_default_criteria().keys())
    missing_values = [key for key in required_keys if key in responses and (responses[key] is None or responses[key] == "")]
    
    if missing_values:
        st.error(f"Please complete all questions for Statement Pair {statement_idx+1}")
        return False
    
    # Optional check for inconsistent answers
    preference_mapping = {
        "Completely Prefer A": 2 if first_is_original else -2,
        "Somewhat Prefer A": 1 if first_is_original else -1,
        "Neither": 0,
        "Somewhat Prefer B": -1 if first_is_original else 1,
        "Completely Prefer B": -2 if first_is_original else 2
    }
    
    # Only check meta questions for inconsistency, not competency assessments
    meta_keys = list(get_default_criteria().keys())
    preference_scores = [preference_mapping[responses[key]] for key in meta_keys if key in responses]
    
    if preference_scores:
        max_score = max(preference_scores)
        min_score = min(preference_scores)
        if max_score >= 2 and min_score <= -2:
            st.warning(f"Your responses for Statement Pair {statement_idx+1} seem inconsistent. Please review if needed.")
    
    # Update detailed quiz results for meta questions
    for key in get_default_criteria().keys():
        if key in responses:
            response = responses[key]
            if response == "Completely Prefer A":
                if first_is_original:
                    st.session_state.detailed_quiz_results[key]["completely_prefer_original"] += 1
                else:
                    st.session_state.detailed_quiz_results[key]["completely_prefer_enriched"] += 1
            elif response == "Somewhat Prefer A":
                if first_is_original:
                    st.session_state.detailed_quiz_results[key]["somewhat_prefer_original"] += 1
                else:
                    st.session_state.detailed_quiz_results[key]["somewhat_prefer_enriched"] += 1
            elif response == "Neither":
                st.session_state.detailed_quiz_results[key]["neither"] += 1
            elif response == "Somewhat Prefer B":
                if first_is_original:
                    st.session_state.detailed_quiz_results[key]["somewhat_prefer_enriched"] += 1
                else:
                    st.session_state.detailed_quiz_results[key]["somewhat_prefer_original"] += 1
            elif response == "Completely Prefer B":
                if first_is_original:
                    st.session_state.detailed_quiz_results[key]["completely_prefer_enriched"] += 1
                else:
                    st.session_state.detailed_quiz_results[key]["completely_prefer_original"] += 1
    
    # Store competency results with proper structure only if competency exists in responses
    if "competency" in responses and responses["competency"] is not None:
        competency_data = {
            "statement_idx": statement_idx,
            "competency": responses.get("competency"),  # Сохраняем только полный текст ответа
            "category": responses.get("category"),
            "subcategory": responses.get("subcategory"),
            "statement": st.session_state.enriched_statements[statement_idx]["original"]
        }
        
        st.session_state.competency_results.append(competency_data)
    
    # Calculate an overall preference based on the average across all criteria
    meta_keys = list(get_default_criteria().keys())
    preference_scores = [preference_mapping[responses[key]] for key in meta_keys if key in responses]
    average_score = sum(preference_scores) / len(preference_scores) if preference_scores else 0
    
    if 'statement_preferences' not in st.session_state:
        st.session_state.statement_preferences = []
    
    if average_score > 0.1:  # Small threshold to account for floating point arithmetic
        preference = "original"
    elif average_score < -0.1:
        preference = "enriched"
    else:
        preference = "neither"
    
    st.session_state.statement_preferences.append(preference)
    
    # Mark the statement as shown
    if statement_idx not in st.session_state.quiz_shown_indices:
        st.session_state.quiz_shown_indices.append(statement_idx)
    
    is_final = len(st.session_state.quiz_shown_indices) >= len(st.session_state.enriched_statements)
    
    original_count = st.session_state.statement_preferences.count("original")
    enriched_count = st.session_state.statement_preferences.count("enriched")
    neither_count = st.session_state.statement_preferences.count("neither")
    
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = {"original": 0, "enriched": 0, "neither": 0}
    
    st.session_state.quiz_results = {
        "original": original_count,
        "enriched": enriched_count,
        "neither": neither_count
    }
    
    # If this is the final statement, save and move on
    if is_final:
        # Get current datetime for saving results
        current_datetime = datetime.datetime.utcnow()
        
        # Убедимся, что competency_results имеет правильную структуру перед сохранением
        competency_results_to_save = st.session_state.competency_results
        
        save_quiz_results(
            st.session_state.user["id"],
            original_count,
            enriched_count,
            neither_count,
            st.session_state.detailed_quiz_results,
            competency_results=competency_results_to_save,
            is_final=is_final
        )
        from services.db.crud._quiz import get_quiz_results_list
        st.session_state.previous_quiz_results = get_quiz_results_list(st.session_state.user["id"])
        st.session_state.has_previous_results = True
        st.session_state.flow_step = 3
    
    return is_final
