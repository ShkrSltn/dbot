from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import bcrypt

# Create base class for models
Base = declarative_base()

# Timezone-aware datetime function
def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

# Define data models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128))
    role = Column(String(20), default='user')
    created_at = Column(DateTime, default=utc_now)
    
    # Relationships
    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    statements = relationship("Statement", back_populates="user", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password):
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

class Profile(Base):
    __tablename__ = 'profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    job_role = Column(String(100))
    job_domain = Column(String(100))
    years_experience = Column(Integer)
    digital_proficiency = Column(String(50))
    primary_tasks = Column(Text)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    user = relationship("User", back_populates="profiles")

class Statement(Base):
    __tablename__ = 'statements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    original = Column(Text, nullable=False)
    enriched = Column(Text, nullable=False)
    metrics = Column(JSON)
    created_at = Column(DateTime, default=utc_now)
    
    # Relationship
    user = relationship("User", back_populates="statements")

class QuizResult(Base):
    __tablename__ = 'quiz_results'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    original_preference = Column(Integer, default=0)
    enriched_preference = Column(Integer, default=0)
    neither_preference = Column(Integer, default=0)
    detailed_results = Column(JSON, default={})
    competency_results = Column(JSON, default=[])
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)
    
    # Relationship
    user = relationship("User", back_populates="quiz_results")

class GlobalSettings(Base):
    __tablename__ = 'global_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    # Relationship
    user = relationship("User")

# Add new model for user sessions
class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(128), nullable=False, unique=True)
    created_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    expired = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User")

class Prompt(Base):
    __tablename__ = 'prompts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    user = relationship("User")

class Framework(Base):
    __tablename__ = 'frameworks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    structure = Column(JSON, nullable=False)  # JSON field to store the framework structure
    is_default = Column(Boolean, default=False)  # Flag for built-in frameworks
    created_by = Column(Integer, ForeignKey('users.id'))  # Optional: track who created it
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    creator = relationship("User")

class PromptHistory(Base):
    __tablename__ = 'prompt_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    prompt_name = Column(String(100), nullable=False)  # Name of the prompt used
    prompt_content = Column(Text, nullable=False)  # Full prompt template content
    original_statement = Column(Text, nullable=False)  # Original statement that was tested
    enriched_statement = Column(Text, nullable=False)  # Result after enrichment
    settings = Column(JSON, nullable=False)  # Settings used (length, profile, evaluation settings, etc.)
    metrics = Column(JSON)  # Quality metrics and scores
    evaluation_result = Column(Text)  # AI evaluation result if available
    attempts = Column(Integer, default=1)  # Number of attempts made
    created_at = Column(DateTime, default=utc_now)
    
    # Relationship
    user = relationship("User") 