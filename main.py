import streamlit as st
import sys
import traceback

# Добавляем отладочную информацию
print("DEBUG: Starting main.py execution")
print(f"DEBUG: Python version: {sys.version}")
print(f"DEBUG: Streamlit version: {st.__version__}")

try:
    # Make sure there are no blank lines or spaces before this call
    print("DEBUG: About to call set_page_config")
    st.set_page_config(
        page_title="DigiBot Demo",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    print("DEBUG: set_page_config called successfully")
except Exception as e:
    print(f"DEBUG: Error in set_page_config: {str(e)}")
    print(traceback.format_exc())

try:
    print("DEBUG: About to import run_app from app")
    from app import run_app
    print("DEBUG: run_app imported successfully")
except Exception as e:
    print(f"DEBUG: Error importing run_app: {str(e)}")
    print(traceback.format_exc())
    st.error(f"Error importing run_app: {str(e)}")

if __name__ == "__main__":
    try:
        print("DEBUG: About to call run_app()")
        run_app()
        print("DEBUG: run_app() completed")
    except Exception as e:
        print(f"DEBUG: Error in run_app: {str(e)}")
        print(traceback.format_exc())
        st.error(f"Error in application: {str(e)}")