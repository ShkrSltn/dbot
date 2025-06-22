import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User, GlobalSettings, Framework
import datetime
from .connection import get_database_connection

def init_db():
    """Initialize database tables and default data"""
    db = get_database_connection()
    if not db:
        return False
    
    engine = db["engine"]
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        Session = db["Session"]
        session = Session()
        
        # Check if admin users exist
        admin_count = session.query(User).filter_by(role="admin").count()
        
        if admin_count == 0:
            # Create default admin users
            admin1 = User(username="admin1", role="admin")
            admin1.set_password("admin1pass")
            
            admin2 = User(username="admin2", role="admin")
            admin2.set_password("admin2pass")
            
            # Create default regular users
            user1 = User(username="user1", role="user")
            user1.set_password("user1pass")
            
            user2 = User(username="user2", role="user")
            user2.set_password("user2pass")
            
            # Add all users
            session.add_all([admin1, admin2, user1, user2])
            
            # Create default global settings
            default_settings = GlobalSettings(
                key="user_settings",
                value={
                    "selected_categories": [],
                    "custom_statements": [],
                    "selected_framework_id": None,  # Add framework selection
                    "statement_source": "default"
                }
            )
            session.add(default_settings)
            
            # Commit user changes
            session.commit()
            print("DEBUG: Created default users and settings")
        
        # Check if default frameworks exist
        framework_count = session.query(Framework).filter_by(is_default=True).count()
        
        if framework_count == 0:
            # Create default DigiComp framework
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
            
            digcomp_framework = Framework(
                name="DigiComp 2.1",
                description="Digital Competence Framework for Citizens",
                structure=digcomp_structure,
                is_default=True
            )
            
            session.add(digcomp_framework)
            session.commit()
            print("DEBUG: Created default DigiComp framework")
            
        session.close()
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False 