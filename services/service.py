import streamlit as st

# Import functions from service modules
from services.chat_service import (
    load_llm,
    generate_chat_response
)

from services.statement_service import (
    get_sample_statements,
    get_statements_from_settings,
    get_all_statements
)

# Импортируем функции из разделенных сервисов
from services.embedding_service import load_embedding_model
from services.enrichment_service import enrich_statement_with_llm
from services.metrics_service import calculate_quality_metrics

# Import database functions
from services.db.crud._users import (
    save_user,
    get_user_by_id,
    authenticate_user,
    create_anonymous_user
)

from services.db.crud._statements import (
    save_statement,
    get_user_statements
)

from services.db.crud._quiz import (
    save_quiz_results,
    get_quiz_results,
    get_quiz_results_all_users
)
from services.db.crud._profiles import (
    save_profile,
    get_profile
)

from services.db.crud._settings import (
    get_global_settings,
    save_global_settings,
    get_user_settings,
    save_user_settings
)

from services.db.crud._chat import (
    save_chat_message,
    get_chat_history
)

from services.db.crud._prompts import (
    save_prompt,
    get_user_prompts,
    delete_prompt
)

# Import session management functions
from services.db.connection import (
    generate_session_token,
    verify_session_token
)

# Re-export all imported functions for backward compatibility
# This ensures that existing code that imports from service.py
# will continue to work without changes