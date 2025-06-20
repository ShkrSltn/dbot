# This file makes the services directory a Python package 

from services.embedding_service import load_embedding_model
from services.enrichment_service import enrich_statement_with_llm, DEFAULT_PROMPT
from services.metrics_service import calculate_quality_metrics
from services.db.crud._prompts import get_user_prompts, get_all_prompts

# Экспортируем функции для удобного импорта
__all__ = [
    'load_embedding_model',
    'enrich_statement_with_llm',
    'calculate_quality_metrics',
    'get_user_prompts',
    'get_all_prompts',
    'DEFAULT_PROMPT'
] 