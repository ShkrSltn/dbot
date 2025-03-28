import streamlit as st
from services.db.crud._settings import get_global_settings

# All available statements
STATEMENTS = [
    "I can use digital technologies to collaborate with others.",
    "I can share documents and resources through digital tools.",
    "I can use online meeting tools effectively for team collaboration.",
    "I know how to protect my personal data online.",
    "I can identify potential security risks when using digital services.",
    "I understand how to create and manage strong passwords.",
    "I can identify and solve technical problems when using digital devices.",
    "I can find solutions to technical issues using online resources.",
    "I know how to evaluate and select digital tools for specific tasks.",
    "I can create digital content in different formats.",
    "I know how to edit and improve content created by others.",
    "I can apply copyright and licenses to digital content I create.",
    "I can evaluate the reliability of digital information sources.",
    "I know how to search for and filter data, information, and content.",
    "I can organize and store digital information efficiently."
]

def get_sample_statements():
    """Returns a subset of statements for demo"""
    return STATEMENTS[:10]

def get_statements_from_settings():
    """Returns statements based on global settings"""
    global_settings = get_global_settings("user_settings")
    
    if not global_settings:
        return get_sample_statements()
    
    selected_statements = []
    
    # Get selected statements
    selected_indices = global_settings.get("selected_statements", [])
    for index in selected_indices:
        if 0 <= index < len(STATEMENTS):
            selected_statements.append(STATEMENTS[index])
    
    # Add custom statements
    if "custom_statements" in global_settings:
        selected_statements.extend(global_settings["custom_statements"])
    
    # If no statements selected, return sample statements
    if not selected_statements:
        return get_sample_statements()
    
    return selected_statements

def get_all_statements():
    """Returns all available statements"""
    return STATEMENTS
