#!/usr/bin/env python3
"""
Migration script to add frameworks table and initialize default data.
Run this script once to add the new frameworks functionality.
"""

import sys
import os
sys.path.append('src')

from services.db.connection import get_database_connection
from services.db.models import Base, Framework
from services.db.crud._frameworks import save_framework, get_framework_by_name

def create_frameworks_table():
    """Create the frameworks table if it doesn't exist"""
    db = get_database_connection()
    if not db:
        print("Error: Could not connect to database")
        return False
    
    engine = db["engine"]
    
    try:
        # Create frameworks table
        Base.metadata.create_all(engine, tables=[Framework.__table__])
        print("✅ Frameworks table created successfully")
        return True
    except Exception as e:
        print(f"Error creating frameworks table: {str(e)}")
        return False

def initialize_default_framework():
    """Initialize the default DigiComp framework"""
    
    # Check if DigiComp framework already exists
    existing_framework = get_framework_by_name("DigiComp 2.1")
    if existing_framework:
        print("✅ DigiComp 2.1 framework already exists")
        return True
    
    # DigiComp framework structure
    digcomp_structure = {
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
    
    # Save the framework
    framework_id = save_framework(
        name="DigiComp 2.1",
        description="Digital Competence Framework for Citizens",
        structure=digcomp_structure,
        is_default=True
    )
    
    if framework_id:
        print("✅ DigiComp 2.1 framework initialized successfully")
        return True
    else:
        print("❌ Failed to initialize DigiComp 2.1 framework")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting frameworks migration...")
    
    # Step 1: Create frameworks table
    if not create_frameworks_table():
        print("❌ Migration failed: Could not create frameworks table")
        return False
    
    # Step 2: Initialize default framework
    if not initialize_default_framework():
        print("❌ Migration failed: Could not initialize default framework")
        return False
    
    print("✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Go to Global Settings → Framework Management")
    print("2. Create your custom frameworks")
    print("3. Select a framework in Statement Configuration")
    
    return True

if __name__ == "__main__":
    main() 