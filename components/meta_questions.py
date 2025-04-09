import streamlit as st
from services.statement_service import get_category_for_statement

def display_meta_questions(statement_idx, quiz_iteration_key, criteria, first_is_original=True, statement=None, show_competency=True):
    """
    Display meta questions for a statement pair with configurable criteria.
    
    Args:
        statement_idx (int): Index of the current statement pair
        quiz_iteration_key (str): Unique key for the current quiz iteration
        criteria (dict): Dictionary of criteria questions
        first_is_original (bool): Whether the first statement is the original one
        statement (str, optional): The statement text for competency assessment
        show_competency (bool): Whether to show competency assessment questions
    """
    # Сначала добавляем оценку компетенции, если есть statement и show_competency=True
    responses = {}
    
    if statement and show_competency:
        # Get category and subcategory for the statement (скрыто от пользователя)
        category, subcategory = get_category_for_statement(statement)
        
        if category and subcategory:
            # Store category and subcategory in session state для этого statement
            cat_key = f"statement_category_{statement_idx}"
            subcat_key = f"statement_subcategory_{statement_idx}"
            st.session_state[cat_key] = category
            st.session_state[subcat_key] = subcategory
            
            st.markdown("Answer according to your selection above:")
            
            # Add competency self-assessment using radio buttons like in the screenshot
            competency_key = f"competency_{statement_idx}_{quiz_iteration_key}"
            current_comp_value = st.session_state.get(competency_key)
            
            competency_options = [
                "I have no knowledge of this / I never heard of this",
                "I have only a limited understanding of this and need more explanations",
                "I have a good understanding of this",
                "I fully master this topic/issue and I could explain it to others"
            ]
            
            competency = st.radio(
                "Select your competency level",
                options=competency_options,
                key=competency_key,
                index=None if current_comp_value is None else competency_options.index(current_comp_value) if current_comp_value in competency_options else None
            )
            
            # Store competency response
            responses["competency"] = competency
    
    # Добавляем разделительную линию без отступов
    divider_html = """
    <div style="margin: 0; padding: 0;">
        <hr style="margin: 0 0 10px 0; padding: 0; border: 0; height: 1px; background-color: #333333;">
    </div>
    """
    st.markdown(divider_html, unsafe_allow_html=True)
    
    # Затем показываем вопросы про критерии
    # st.markdown('<div class="meta-questions-header">Meta Questions</div>', unsafe_allow_html=True)

    # Desktop headers
    desktop_header_html = """
    <div class="desktop-header">
        <div class="header-cols">
            <div class="header-cols-items">  
                <div class="header-left-left">Completely Prefer A</div>
                <div class="header-left">Somewhat Prefer A</div>
                <div class="header-center">Neither</div>
                <div class="header-right">Somewhat Prefer B</div>
                <div class="header-right-right">Completely Prefer B</div>
            </div>
        </div>
    </div>
    """

    st.markdown(desktop_header_html, unsafe_allow_html=True)

    # Mobile headers
    mobile_header_html = """
    <div class='mobile-header'>
        <div class='mobile-header-item'>
            <span>Completely Prefer A</span>
        </div>
        <div class='mobile-header-item'>
            <span>Somewhat Prefer A</span>
        </div>
        <div class='mobile-header-item'>
            <span>Neither</span>
        </div>
        <div class='mobile-header-item'>
            <span>Somewhat Prefer B</span>
        </div>
        <div class='mobile-header-item'>
            <span>Completely Prefer B</span>
        </div>
    </div>
    """
    st.markdown(mobile_header_html, unsafe_allow_html=True)

    # For each meta question, display the question and its compact radio widget
    criteria_keys = list(criteria.keys())
    for i, key in enumerate(criteria_keys):
        question = criteria[key]
        radio_key = f"radio_{key}_{statement_idx}_{quiz_iteration_key}"
        
        # Увеличим ширину колонки с текстом вопроса для отображения в одну строку
        row_cols = st.columns([2, 3])  # Изменено с [1, 5] на [2, 3]
        
        with row_cols[0]:
            # Добавляем класс для стилизации
            st.markdown(f'<div class="criteria-text">{question}</div>', unsafe_allow_html=True)
        with row_cols[1]:
            # Get the current value from session state if it exists
            current_value = st.session_state.get(radio_key)
            
            # Create the radio widget
            response = st.radio(
                label=question,
                options=["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"],
                key=radio_key,
                horizontal=True,
                index=None if current_value is None else ["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"].index(current_value),
                label_visibility="collapsed",
                format_func=lambda x: ""
            )
            
            # Store the response in our local dictionary
            responses[key] = response
        
        # Добавляем тонкую разделительную линию между вопросами (кроме последнего)
        if i < len(criteria_keys) - 1:
            meta_divider_html = """
            <div style="margin: 0; padding: 0;">
                <hr style="margin: 0; padding: 0; border: 0; height: 1px; background-color: #222222; opacity: 0.2;">
            </div>
            """
            st.markdown(meta_divider_html, unsafe_allow_html=True)
    
    return responses

def get_default_criteria():
    """
    Returns the default criteria for meta questions.
    """
    return {
        "understand": "Which statement is easier to understand?",
        "read": "Which statement is easier to read?",
        "detail": "Which statement offers greater detail?",
        "profession": "Which statement fits your profession?",
        "assessment": "Which statement is helpful for a self-assessment?"
    }

def get_competency_criteria():
    """
    Returns the criteria for competency assessment.
    """
    return {
        "competency": "How would you rate your competency in this area?"
    }

def get_meta_questions_styles():
    """
    Returns the CSS styles for meta questions.
    """
    return """
    <style>
        /* Background стиль для соответствия скриншоту */
        div.stRadio > div {
            background-color: #252633;
            border-radius: 3px;
            padding: 1px 0;
        }
        
        div[data-testid="stRadio"] {
            border-radius: 5px;
            width: 100%;
        }
        div[data-testid="stRadio"] > div {
            display: flex;
            justify-content: space-between;
            width: 100%;
        }
        div[data-testid="stRadio"] > div > label {
            padding: 0;
            margin: 0;
        }

        /* Styling for header columns */
        .header-left-left {
            text-align: left;
        }
        .header-center {
            text-align: center;
        }
        .header-right-right {
            text-align: right;
        }
        .header-right {
            text-align: right;
        }
        
        /* Настраиваем заголовок Meta Questions */
        .meta-questions-header {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        /* Стили для заголовка критериев */
        .criteria-header {
            width: 40%; /* Увеличиваем ширину заголовка */
            font-weight: bold;
        }
        
        /* Стили для текста критериев - чтобы строки не переносились */
        .criteria-text {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding-right: 10px;
            font-size: 1rem;
            line-height: 1.5;
        }

        .st-emotion-cache-ocqkz7 {
            display: flex;
            flex-direction: row;
            justify-content: space-between;
        }
        
        /* Hide mobile header on desktop and show desktop header by default */
        .mobile-header {
            display: none;
        }

        .desktop-header .header-cols-items {
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            text-align: center;
            margin-left: 40%; /* Увеличено для соответствия ширине блока критериев */
            width: 60%; /* Установлена ширина блока с радиокнопками */
        }
        
        /* Competency assessment radio buttons styling */
        div[data-testid="stRadio"].competency-radio > div {
            flex-direction: column;
            align-items: flex-start;
        }
        
        div[data-testid="stRadio"].competency-radio > div > label {
            margin-bottom: 10px;
            width: 100%;
            background-color: #1e1e1e;
            border-radius: 5px;
            padding: 10px !important;
        }
        
        div[data-testid="stRadio"].competency-radio > div > label:hover {
            background-color: #2a2a2a;
        }
        
        /* Remove spacing around divider */
        hr {
            margin: 0 !important;
            padding: 0 !important;
            opacity: 0.2;
        }
        
        /* Style для разделительных линий между мета-вопросами */
        .meta-divider {
            height: 1px;
            background-color: #222222;
            border: none;
            margin: 0;
            padding: 0;
            opacity: 0.2;
        }
        
        /* Стили для экранов меньше 1000px */
        @media (max-width: 1000px) {
            /* Уменьшаем заголовок */
            .meta-questions-header {
                font-size: 1rem;
            }
            
            /* Уменьшаем размер заголовков в шапке */
            .desktop-header {
                font-size: 0.8rem;
            }
            
            /* Уменьшаем заголовок критериев */
            .criteria-header {
                font-size: 0.8rem;
            }
            
            /* Уменьшаем размер текста критериев */
            .criteria-text {
                font-size: 0.85rem;
            }
            
            
            /* Делаем заголовки колонок меньше */
            .header-left-left, .header-left, .header-center, .header-right, .header-right-right {
                font-size: 0.75rem;
            }
        }
        
        /* Mobile responsiveness */
        @media (max-width: 640px) {
            /* Hide desktop header on mobile */
            .desktop-header {
                display: none;
            }
            /* Display mobile header on mobile */
            .mobile-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                margin-bottom: 10px;
                font-size: 0.8rem;
            }

            .mobile-header-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                width: 20%;
                font-size: 0.7rem;
            }

            .mobile-header-item img {
                width: 20px;
                height: 20px;
                margin-bottom: 4px;
            }

            /* Styling radio buttons for mobile */
            div[data-testid="stRadio"] > div {
                display: flex;
                justify-content: space-between;
                gap: 5px !important;
            }

            div[data-testid="stRadio"] > div > label {
                flex: 1;
                min-width: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 8px 4px !important;
                border-radius: 4px;
                transform: scale(1); /* Сбрасываем масштаб на мобильных */
            }

            /* Критерии текст на мобильных - разрешаем перенос */
            .criteria-text {
                white-space: normal;
                font-size: 0.8rem !important;
                margin-bottom: 8px !important;
                font-weight: 500;
            }
        }
    </style>
    """

def get_custom_styles():
    return """
    <style>
        .custom-text {
            max-height: 100px;
            overflow-y: auto;
        }
    </style>
    """

