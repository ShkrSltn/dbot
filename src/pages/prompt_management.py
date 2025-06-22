import streamlit as st
from services.db.crud._prompts import delete_prompt, delete_all_user_prompts

def display_prompt_management():
    """Display prompt management component"""
    
    st.subheader("📝 All Your Prompts")
    st.markdown("Manage all your custom prompts in one place.")
    
    # Get custom prompts only
    custom_prompts = {k: v for k, v in st.session_state.prompts.items() 
                     if k not in ['default', 'basic', 'digcomp_few_shot', 'general_few_shot']}
    
    if custom_prompts:
        # Show prompts in an expandable format
        for prompt_name, prompt_content in custom_prompts.items():
            with st.expander(f"{prompt_name}", expanded=False):
                # Show prompt content
                st.text_area(f"Content of '{prompt_name}':", value=prompt_content, height=200, disabled=True, key=f"content_{prompt_name}")
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("Edit", key=f"edit_{prompt_name}", help="Edit this prompt"):
                        st.session_state.current_prompt = prompt_name
                        st.info(f"Selected '{prompt_name}' for editing. Switch to 'Create New Prompt' mode to edit.")
                
                with col2:
                    # Initialize delete confirmation state for management section
                    if f'confirm_delete_mgmt_{prompt_name}' not in st.session_state:
                        st.session_state[f'confirm_delete_mgmt_{prompt_name}'] = False
                    
                    if not st.session_state[f'confirm_delete_mgmt_{prompt_name}']:
                        if st.button("Delete", key=f"delete_mgmt_{prompt_name}", help="Delete this prompt"):
                            st.session_state[f'confirm_delete_mgmt_{prompt_name}'] = True
                            st.rerun()
                    else:
                        if st.button("Cancel Delete", key=f"cancel_mgmt_{prompt_name}"):
                            st.session_state[f'confirm_delete_mgmt_{prompt_name}'] = False
                            st.rerun()
                
                with col3:
                    st.write("")  # Empty space for alignment
                
                # Show confirmation block in a separate row when deletion is being confirmed
                if st.session_state.get(f'confirm_delete_mgmt_{prompt_name}', False):
                    st.error(f"Delete '{prompt_name}'?")
                    if st.button("CONFIRM DELETE", key=f"confirm_mgmt_{prompt_name}", type="primary"):
                        if delete_prompt(st.session_state.user["id"], prompt_name):
                            del st.session_state.prompts[prompt_name]
                            if st.session_state.current_prompt == prompt_name:
                                st.session_state.current_prompt = 'default'
                            st.session_state[f'confirm_delete_mgmt_{prompt_name}'] = False
                            st.success(f"Prompt '{prompt_name}' deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete prompt.")
                            st.session_state[f'confirm_delete_mgmt_{prompt_name}'] = False
        
        # Summary
        st.info(f"You have **{len(custom_prompts)}** custom prompt(s)")
        
        # Bulk actions
        if len(custom_prompts) > 1:
            st.markdown("### Bulk Actions")
            
            if st.button("Delete All Custom Prompts", help="Delete all your custom prompts"):
                if 'confirm_delete_all' not in st.session_state:
                    st.session_state.confirm_delete_all = False
                
                if not st.session_state.confirm_delete_all:
                    st.session_state.confirm_delete_all = True
                    st.rerun()
            
            if st.session_state.get('confirm_delete_all', False):
                st.error("Are you sure you want to delete ALL your custom prompts? This action cannot be undone!")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("YES, DELETE ALL", type="primary"):
                        deleted_count = delete_all_user_prompts(st.session_state.user["id"])
                        
                        # Remove all custom prompts from session state
                        for prompt_name in list(custom_prompts.keys()):
                            if prompt_name in st.session_state.prompts:
                                del st.session_state.prompts[prompt_name]
                        
                        st.session_state.current_prompt = 'default'
                        st.session_state.confirm_delete_all = False
                        st.success(f"Deleted {deleted_count} custom prompt(s) successfully!")
                        st.rerun()
                
                with col2:
                    if st.button("Cancel"):
                        st.session_state.confirm_delete_all = False
                        st.rerun()
    else:
        st.info("No custom prompts yet. Create your first prompt using the form above!")
        st.markdown("💡 **Tips for creating effective prompts:**")
        st.markdown("- Use clear, specific instructions")
        st.markdown("- Include context variables: `{context}`, `{original_statement}`, `{length}`")
        st.markdown("- Test different approaches and compare results")
        st.markdown("- Check the testing history to see what works best") 