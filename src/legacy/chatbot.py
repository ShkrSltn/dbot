import streamlit as st
from services.chat_service import generate_chat_response

def display_chatbot():
    st.title("💬 Digital Skills Chatbot")
    
    if not st.session_state.profile["job_role"]:
        st.warning("Please create your profile first in the Profile Builder section.")
        st.stop()
        
    st.markdown("""
    Chat with DigiBot about digital skills, competencies, and learning resources.
    The chatbot is personalized based on your profile.
    """)
    
    # Initialize chat history if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Create a layout with two main areas:
    # 1. Chat history area (messages)
    # 2. Input area (always at bottom)
    
    # Chat history area
    chat_history_container = st.container()
    
    # Settings sidebar
    with st.sidebar:
        st.subheader("Chat Settings")
        use_max_tokens = st.checkbox("Limit response length", value=False)
        max_tokens = None
        if use_max_tokens:
            max_tokens = st.slider("Maximum tokens in response", 50, 500, 200)
    
    # Input area (always at bottom)
    input_container = st.container()
    
    # Handle user input (placed in code before displaying messages)
    with input_container:
        prompt = st.chat_input("Ask about digital skills...")
        
        if prompt:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Generate response
            try:
                response = generate_chat_response(prompt, st.session_state.profile, max_tokens)
                # Add assistant response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})
            
            # Rerun to update the chat interface with the new messages
            st.rerun()
    
    # Display chat messages from history
    with chat_history_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"]) 