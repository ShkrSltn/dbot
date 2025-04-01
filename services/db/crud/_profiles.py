from ..connection import get_database_connection
from ..models import Profile

def save_profile(user_id, profile_data):
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        # Проверяем, существует ли профиль
        profile = session.query(Profile).filter_by(user_id=user_id).first()
        
        if profile:
            # Обновляем существующий профиль
            for key, value in profile_data.items():
                setattr(profile, key, value)
        else:
            # Создаем новый профиль
            profile_data['user_id'] = user_id
            profile = Profile(**profile_data)
            session.add(profile)
        
        session.commit()
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_profile(user_id):
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    try:
        profile = session.query(Profile).filter_by(user_id=user_id).first()
        if profile:
            return {
                "job_role": profile.job_role,
                "job_domain": profile.job_domain,
                "years_experience": profile.years_experience,
                "digital_proficiency": profile.digital_proficiency,
                "primary_tasks": profile.primary_tasks
            }
        return None
    except Exception as e:
        print(f"Error getting profile: {e}")
        return None
    finally:
        session.close()

def get_all_profiles():
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    try:
        profiles = session.query(Profile).all()
        result = []
        for profile in profiles:
            result.append({
                "user_id": profile.user_id,
                "job_role": profile.job_role,
                "job_domain": profile.job_domain,
                "years_experience": profile.years_experience,
                "digital_proficiency": profile.digital_proficiency,
                "primary_tasks": profile.primary_tasks
            })
        return result
    except Exception as e:
        print(f"Error getting all profiles: {e}")
        return None
    finally:
        session.close()
    