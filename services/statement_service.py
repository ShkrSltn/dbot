import streamlit as st
from services.db.crud._settings import get_global_settings

# All available statements
CURRENT_STATEMENTS = [
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
    all_statements = get_all_digcomp_statements()
    return all_statements

def get_statements_from_settings():
    """Returns statements based on global settings"""
    global_settings = get_global_settings("user_settings")
    
    if not global_settings:
        return get_sample_statements()
    
    selected_statements = []
    statement_source = global_settings.get("statement_source", "default")
    
    if statement_source == "digcomp":
        # Get statements from DigiComp framework based on selected categories and subcategories
        selected_categories = global_settings.get("selected_categories", [])
        selected_subcategories = global_settings.get("selected_subcategories", {})
        
        # Add statements from selected categories
        for category in selected_categories:
            selected_statements.extend(get_statements_by_category(category))
        
        # Add statements from selected subcategories
        for category, subcategories in selected_subcategories.items():
            if category not in selected_categories:  # Skip if entire category is already selected
                for subcategory in subcategories:
                    selected_statements.extend(get_statements_by_subcategory(category, subcategory))
        
        # Remove duplicates
        selected_statements = list(set(selected_statements))
        
        # If no statements selected from categories/subcategories, get statements from individual selection
        if not selected_statements:
            all_digcomp_statements = get_all_digcomp_statements()
            selected_indices = global_settings.get("selected_statements", [])
            for index in selected_indices:
                if 0 <= index < len(all_digcomp_statements):
                    selected_statements.append(all_digcomp_statements[index])
    else:
        # Use default statements
        selected_indices = global_settings.get("selected_statements", [])
        for index in selected_indices:
            if 0 <= index < len(CURRENT_STATEMENTS):
                selected_statements.append(CURRENT_STATEMENTS[index])
    
    # Add custom statements
    if "custom_statements" in global_settings:
        selected_statements.extend(global_settings["custom_statements"])
    
    # If no statements selected, return sample statements
    if not selected_statements:
        return get_sample_statements()
    
    return selected_statements

def get_all_statements():
    """Returns all available statements based on current source"""
    global_settings = get_global_settings("user_settings")
    
    if not global_settings:
        return CURRENT_STATEMENTS
    
    statement_source = global_settings.get("statement_source", "default")
    
    if statement_source == "digcomp":
        return get_all_digcomp_statements()
    else:
        return CURRENT_STATEMENTS

# DigiComp Framework Categories and Competences with Statements

DIGCOMP_FRAMEWORK = {
    "Information and data literacy": {
        "Browsing, searching and filtering data, information and digital content": [
            "I know how to search for and filter data, information, and content.",
            "I know which words to use in order to find what I need quickly.",
            "When I use a search engine, I can take advantage of its advanced features."
        ],
        "Evaluating data, information and digital content": [
            "I can evaluate the reliability of digital information sources.",
            "I critically check if the information I find online is reliable.",
            "I know that different search engines may give different search results, because they are influenced by commercial factors.",
            "I know that some information on the Internet is fake."
        ],
        "Managing data, information and digital content": [
            "I can organize and store digital information efficiently.",
            "I know how to organize digital content using folders or tagging to find them back later.",
            "I know about different storage media (e.g., internal or external hard disk, USB memory, pen drive, memory card)."
        ]
    },
    "Communication and collaboration": {
        "Interacting through digital technologies": [
            "I can use digital technologies to collaborate with others.",
            "I can use online meeting tools effectively for team collaboration."
        ],
        "Sharing through digital technologies": [
            "I can share documents and resources through digital tools."
        ],
        "Engaging in citizenship through digital technologies": [
            "I can participate in online communities and contribute to discussions."
        ],
        "Collaborating through digital technologies": [
            "I can co-create content and collaborate on documents with others online."
        ],
        "Netiquette": [
            "I understand digital etiquette and appropriate behavior in online spaces."
        ],
        "Managing digital identity": [
            "I can manage my digital identity and reputation across multiple platforms."
        ]
    },
    "Digital content creation": {
        "Developing digital content": [
            "I can create digital content in different formats."
        ],
        "Integrating and re-elaborating digital content": [
            "I know how to edit and improve content created by others."
        ],
        "Copyright and licenses": [
            "I can apply copyright and licenses to digital content I create."
        ],
        "Programming": [
            "I understand how algorithms work and can use them to solve problems."
        ]
    },
    "Safety": {
        "Protecting devices": [
            "I can protect my devices from malware and unauthorized access."
        ],
        "Protecting personal data and privacy": [
            "I know how to protect my personal data online.",
            "I understand how to create and manage strong passwords."
        ],
        "Protecting health and well-being": [
            "I can identify and address digital risks to my health and well-being."
        ],
        "Protecting the environment": [
            "I understand the environmental impact of digital technologies."
        ]
    },
    "Problem solving": {
        "Solving technical problems": [
            "I can identify and solve technical problems when using digital devices.",
            "I can find solutions to technical issues using online resources."
        ],
        "Identifying needs and technological responses": [
            "I know how to evaluate and select digital tools for specific tasks."
        ],
        "Creatively using digital technologies": [
            "I can use digital tools in innovative ways to solve problems."
        ],
        "Identifying digital competence gaps": [
            "I can identify areas where I need to improve my digital skills."
        ]
    }
}

# Current DigiBot statements from statement_service.py
CURRENT_STATEMENTS = [
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

def get_all_digcomp_statements():
    """Returns all DigiComp statements from the framework"""
    all_statements = []
    for category in DIGCOMP_FRAMEWORK.values():
        for subcategory in category.values():
            all_statements.extend(subcategory)
    return all_statements

def get_statements_by_category(category_name):
    """Returns statements for a specific category"""
    if category_name in DIGCOMP_FRAMEWORK:
        statements = []
        for subcategory in DIGCOMP_FRAMEWORK[category_name].values():
            statements.extend(subcategory)
        return statements
    return []

def get_statements_by_subcategory(category_name, subcategory_name):
    """Returns statements for a specific subcategory"""
    if category_name in DIGCOMP_FRAMEWORK:
        if subcategory_name in DIGCOMP_FRAMEWORK[category_name]:
            return DIGCOMP_FRAMEWORK[category_name][subcategory_name]
    return []

def get_category_for_statement(statement):
    """Returns the category and subcategory for a given statement"""
    for category_name, category in DIGCOMP_FRAMEWORK.items():
        for subcategory_name, statements in category.items():
            if statement in statements:
                return category_name, subcategory_name
    return None, None

def get_all_categories():
    """Returns all categories"""
    return list(DIGCOMP_FRAMEWORK.keys())

def get_subcategories(category_name):
    """Returns subcategories for a given category"""
    if category_name in DIGCOMP_FRAMEWORK:
        return list(DIGCOMP_FRAMEWORK[category_name].keys())
    return []
