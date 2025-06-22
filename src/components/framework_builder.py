import streamlit as st
import json
from services.db.crud._frameworks import save_framework, update_framework, delete_framework

def display_framework_builder():
    """Display interactive framework builder component"""
    
    st.markdown("#### Create Custom Framework")
    
    # Initialize session state for framework builder
    if 'framework_builder' not in st.session_state:
        st.session_state.framework_builder = {
            'name': '',
            'description': '',
            'categories': {}
        }
    
    # Step 1: Framework Basic Information
    st.markdown("**Step 1: Framework Information**")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        framework_name = st.text_input(
            "Framework Name", 
            value=st.session_state.framework_builder['name'],
            key="framework_name_input",
            placeholder="e.g., 'IT Skills Framework'"
        )
        st.session_state.framework_builder['name'] = framework_name
    
    with col2:
        # Empty space for alignment
        st.empty()
    
    framework_description = st.text_area(
        "Framework Description", 
        value=st.session_state.framework_builder['description'],
        key="framework_description_input",
        placeholder="Brief description of what this framework covers",
        height=100
    )
    st.session_state.framework_builder['description'] = framework_description
    
    if not framework_name:
        st.warning("Please enter a framework name to continue.")
        return
    
    st.markdown("---")
    
    # Step 2: Categories Management
    st.markdown("**Step 2: Create Categories**")
    
    # Add new category section
    new_category = st.text_input(
        "Category Name", 
        key="new_category_input", 
        placeholder="e.g., Technical Skills"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        add_category_btn = st.button("Add Category", key="add_category_btn", use_container_width=True)
    with col2:
        if st.session_state.framework_builder['categories']:
            if st.button("Clear All", key="clear_categories_btn", use_container_width=True):
                st.session_state.framework_builder['categories'] = {}
                st.rerun()
    
    # Handle category addition
    if add_category_btn and new_category:
        if new_category not in st.session_state.framework_builder['categories']:
            st.session_state.framework_builder['categories'][new_category] = {}
            # Clear the input field
            if "new_category_input" in st.session_state:
                del st.session_state["new_category_input"]
            st.success(f"Category '{new_category}' added!")
            st.rerun()
        else:
            st.error("Category already exists!")
    
    # Display existing categories
    categories = st.session_state.framework_builder['categories']
    
    if not categories:
        st.info("No categories created yet. Add your first category above.")
        return
    
    st.markdown("---")
    
    # Step 3: Manage Categories and Subcategories
    st.markdown("**Step 3: Manage Categories & Subcategories**")
    
    # Category selector
    selected_category = st.selectbox(
        "Select Category to Edit:",
        options=list(categories.keys()),
        key="category_selector"
    )
    
    if selected_category:
        # Category management section
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Rename Category", key="rename_category_btn", use_container_width=True):
                st.session_state[f"editing_cat_{selected_category}"] = True
        with col2:
            if st.button("Delete Category", key="delete_category_btn", use_container_width=True):
                del st.session_state.framework_builder['categories'][selected_category]
                st.success(f"Category '{selected_category}' deleted!")
                st.rerun()
        
        # Category renaming
        if st.session_state.get(f"editing_cat_{selected_category}", False):
            new_name = st.text_input(
                "New category name:", 
                value=selected_category, 
                key=f"rename_input_{selected_category}"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Save", key=f"save_rename_{selected_category}", use_container_width=True):
                    if new_name and new_name != selected_category:
                        categories[new_name] = categories.pop(selected_category)
                        del st.session_state[f"editing_cat_{selected_category}"]
                        st.success("Category renamed!")
                        st.rerun()
            with col2:
                if st.button("Cancel", key=f"cancel_rename_{selected_category}", use_container_width=True):
                    del st.session_state[f"editing_cat_{selected_category}"]
                    st.rerun()
        
        st.markdown("**Subcategories:**")
        
        # Add new subcategory section
        new_subcategory = st.text_input(
            "Subcategory Name", 
            key=f"new_subcat_{selected_category}",
            placeholder="e.g., Programming Languages"
        )
        
        add_subcat_btn = st.button("Add Subcategory", key=f"add_subcat_{selected_category}")
        
        # Handle subcategory addition
        if add_subcat_btn and new_subcategory:
            if new_subcategory not in categories[selected_category]:
                categories[selected_category][new_subcategory] = []
                # Clear the input field
                if f"new_subcat_{selected_category}" in st.session_state:
                    del st.session_state[f"new_subcat_{selected_category}"]
                st.success(f"Subcategory '{new_subcategory}' added!")
                st.rerun()
            else:
                st.error("Subcategory already exists!")
        
        # Display subcategories
        subcategories = categories[selected_category]
        
        if subcategories:
            for subcat_name in list(subcategories.keys()):
                st.markdown(f"**{subcat_name}**")
                
                # Subcategory actions
                statements_count = len(subcategories[subcat_name])
                st.text(f"Statements: {statements_count}")
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("Rename", key=f"rename_subcat_{selected_category}_{subcat_name}", use_container_width=True):
                        st.session_state[f"editing_subcat_{selected_category}_{subcat_name}"] = True
                with col2:
                    if st.button("Delete", key=f"delete_subcat_{selected_category}_{subcat_name}", use_container_width=True):
                        del categories[selected_category][subcat_name]
                        st.success(f"Subcategory '{subcat_name}' deleted!")
                        st.rerun()
                with col3:        
                    if st.button("Edit Statements", key=f"edit_statements_{selected_category}_{subcat_name}", use_container_width=True):
                        st.session_state[f"managing_statements_{selected_category}_{subcat_name}"] = True
                
                # Subcategory renaming
                if st.session_state.get(f"editing_subcat_{selected_category}_{subcat_name}", False):
                    new_subcat_name = st.text_input(
                        "New subcategory name:", 
                        value=subcat_name, 
                        key=f"rename_subcat_input_{selected_category}_{subcat_name}"
                    )
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("Save", key=f"save_subcat_rename_{selected_category}_{subcat_name}", use_container_width=True):
                            if new_subcat_name and new_subcat_name != subcat_name:
                                categories[selected_category][new_subcat_name] = categories[selected_category].pop(subcat_name)
                                del st.session_state[f"editing_subcat_{selected_category}_{subcat_name}"]
                                st.success("Subcategory renamed!")
                                st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_subcat_rename_{selected_category}_{subcat_name}", use_container_width=True):
                            del st.session_state[f"editing_subcat_{selected_category}_{subcat_name}"]
                            st.rerun()
                
                # Statement management
                if st.session_state.get(f"managing_statements_{selected_category}_{subcat_name}", False):
                    st.markdown(f"*Managing statements for {subcat_name}:*")
                    
                    # Add new statement
                    new_statement = st.text_input(
                        "New Statement", 
                        key=f"new_stmt_{selected_category}_{subcat_name}",
                        placeholder="e.g., I can write basic code in Python"
                    )
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("Add Statement", key=f"add_stmt_{selected_category}_{subcat_name}", use_container_width=True):
                            if new_statement and new_statement not in categories[selected_category][subcat_name]:
                                categories[selected_category][subcat_name].append(new_statement)
                                # Clear the input field
                                if f"new_stmt_{selected_category}_{subcat_name}" in st.session_state:
                                    del st.session_state[f"new_stmt_{selected_category}_{subcat_name}"]
                                st.success("Statement added!")
                                st.rerun()
                            elif new_statement in categories[selected_category][subcat_name]:
                                st.error("Statement already exists!")
                    with col2:
                        if st.button("Done", key=f"done_statements_{selected_category}_{subcat_name}", use_container_width=True):
                            del st.session_state[f"managing_statements_{selected_category}_{subcat_name}"]
                            st.rerun()
                    
                    # Display statements
                    statements = categories[selected_category][subcat_name]
                    if statements:
                        for i, statement in enumerate(statements):
                            # Check if editing this statement
                            if st.session_state.get(f"editing_stmt_{selected_category}_{subcat_name}_{i}", False):
                                new_stmt_text = st.text_input(
                                    f"Edit statement {i+1}:",
                                    value=statement,
                                    key=f"edit_stmt_input_{selected_category}_{subcat_name}_{i}"
                                )
                                
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    if st.button("Save", key=f"save_stmt_{selected_category}_{subcat_name}_{i}", use_container_width=True):
                                        if new_stmt_text:
                                            categories[selected_category][subcat_name][i] = new_stmt_text
                                            del st.session_state[f"editing_stmt_{selected_category}_{subcat_name}_{i}"]
                                            st.success("Statement updated!")
                                            st.rerun()
                                with col2:        
                                    if st.button("Cancel", key=f"cancel_stmt_{selected_category}_{subcat_name}_{i}", use_container_width=True):
                                        del st.session_state[f"editing_stmt_{selected_category}_{subcat_name}_{i}"]
                                        st.rerun()
                            else:
                                st.text(f"{i+1}. {statement}")
                                
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    if st.button("Edit", key=f"edit_stmt_{selected_category}_{subcat_name}_{i}", use_container_width=True):
                                        st.session_state[f"editing_stmt_{selected_category}_{subcat_name}_{i}"] = True
                                        st.rerun()
                                with col2:        
                                    if st.button("Delete", key=f"delete_stmt_{selected_category}_{subcat_name}_{i}", use_container_width=True):
                                        categories[selected_category][subcat_name].pop(i)
                                        st.success("Statement deleted!")
                                        st.rerun()
                    else:
                        st.info("No statements added yet.")
                
                st.markdown("---")
        else:
            st.info("No subcategories created yet. Add your first subcategory above.")
    
    st.markdown("---")
    
    # Final Actions
    st.markdown("**Step 4: Save Framework**")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Clear All", key="clear_framework_builder", use_container_width=True):
            st.session_state.framework_builder = {
                'name': '',
                'description': '',
                'categories': {}
            }
            # Clear any editing states
            keys_to_clear = [key for key in st.session_state.keys() if key.startswith('editing_') or key.startswith('managing_')]
            for key in keys_to_clear:
                del st.session_state[key]
            st.success("Framework cleared!")
            st.rerun()
    with col2:
        if st.button("Preview JSON", key="preview_framework_json", use_container_width=True):
            if st.session_state.framework_builder['categories']:
                with st.expander("Framework JSON Preview", expanded=True):
                    st.code(json.dumps(st.session_state.framework_builder['categories'], indent=2, ensure_ascii=False))
            else:
                st.warning("No framework structure to preview.")
    
    # Framework validation
    is_valid = True
    validation_message = ""
    
    if not st.session_state.framework_builder['name']:
        is_valid = False
        validation_message = "Framework name required"
    elif not st.session_state.framework_builder['categories']:
        is_valid = False
        validation_message = "Add at least one category"
    else:
        for cat_name, subcats in st.session_state.framework_builder['categories'].items():
            if not subcats:
                is_valid = False
                validation_message = f"Category '{cat_name}' needs subcategories"
                break
            for subcat_name, statements in subcats.items():
                if not statements:
                    is_valid = False
                    validation_message = f"Subcategory '{subcat_name}' needs statements"
                    break
            if not is_valid:
                break
    
    if not is_valid:
        st.button(f"Cannot Save: {validation_message}", disabled=True)
    else:
        st.button("Framework Complete", disabled=True)
    
    if st.button("Save Framework", key="save_framework_builder", type="primary"):
            if not st.session_state.framework_builder['name']:
                st.error("Please enter a framework name.")
            elif not st.session_state.framework_builder['categories']:
                st.error("Please add at least one category with subcategories and statements.")
            else:
                # Validate framework structure
                valid = True
                for cat_name, subcats in st.session_state.framework_builder['categories'].items():
                    if not subcats:
                        st.error(f"Category '{cat_name}' must have at least one subcategory.")
                        valid = False
                        break
                    for subcat_name, statements in subcats.items():
                        if not statements:
                            st.error(f"Subcategory '{subcat_name}' must have at least one statement.")
                            valid = False
                            break
                
                if valid:
                    # Save to database
                    framework_id = save_framework(
                        name=st.session_state.framework_builder['name'],
                        description=st.session_state.framework_builder['description'],
                        structure=st.session_state.framework_builder['categories'],
                        is_default=False,
                        created_by=st.session_state.user.get("id") if "user" in st.session_state else None
                    )
                    
                    if framework_id:
                        st.success(f"Framework '{st.session_state.framework_builder['name']}' created successfully!")
                        # Clear builder
                        st.session_state.framework_builder = {
                            'name': '',
                            'description': '',
                            'categories': {}
                        }
                        # Clear any editing states  
                        keys_to_clear = [key for key in st.session_state.keys() if key.startswith('editing_') or key.startswith('managing_')]
                        for key in keys_to_clear:
                            del st.session_state[key]
                        st.rerun()
                    else:
                        st.error("Failed to create framework. Please try again.")

def load_framework_to_builder(framework):
    """Load an existing framework into the builder for editing"""
    st.session_state.framework_builder = {
        'name': f"{framework['name']} (Copy)",
        'description': framework.get('description', ''),
        'categories': framework.get('structure', {})
    }

def clear_framework_builder():
    """Clear the framework builder"""
    st.session_state.framework_builder = {
        'name': '',
        'description': '',
        'categories': {}
    }

def display_framework_list(available_frameworks):
    """Display list of existing frameworks with management options"""
    
    st.markdown("#### Manage Existing Frameworks")
    
    custom_frameworks = [fw for fw in available_frameworks if not fw.get("is_default")]
    
    if custom_frameworks:
        for framework in custom_frameworks:
            with st.expander(f"{framework['name']}", expanded=False):
                st.markdown(f"**Description:** {framework.get('description', 'No description')}")
                st.markdown(f"**Created:** {framework.get('created_at', 'Unknown')}")
                
                # Show structure preview
                structure = framework.get('structure', {})
                if structure:
                    st.markdown("**Structure:**")
                    for category in structure.keys():
                        subcategory_count = len(structure[category])
                        total_statements = sum(len(statements) for statements in structure[category].values())
                        st.markdown(f"- {category}: {subcategory_count} subcategories, {total_statements} statements")
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("Load to Builder", key=f"load_{framework['id']}", use_container_width=True):
                        load_framework_to_builder(framework)
                        st.success("Framework loaded to builder!")
                        st.rerun()
                with col2:
                    if st.button("Edit Info", key=f"edit_{framework['id']}", use_container_width=True):
                        st.session_state[f"editing_framework_{framework['id']}"] = True
                        st.rerun()
                with col3:
                    if st.button("Delete", key=f"delete_{framework['id']}", use_container_width=True):
                        if delete_framework(framework['id']):
                            st.success(f"Framework '{framework['name']}' deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete framework.")
                
                # Edit form (simplified - just name and description)
                if st.session_state.get(f"editing_framework_{framework['id']}", False):
                    st.markdown("**Edit Framework Info:**")
                    
                    new_name = st.text_input("Name", value=framework['name'], key=f"edit_name_{framework['id']}")
                    new_description = st.text_area("Description", value=framework.get('description', ''), key=f"edit_desc_{framework['id']}")
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("Save Changes", key=f"save_changes_{framework['id']}", use_container_width=True):
                            if update_framework(framework['id'], new_name, new_description, None):
                                # Clear the input fields
                                if f"edit_name_{framework['id']}" in st.session_state:
                                    del st.session_state[f"edit_name_{framework['id']}"]
                                if f"edit_desc_{framework['id']}" in st.session_state:
                                    del st.session_state[f"edit_desc_{framework['id']}"]
                                del st.session_state[f"editing_framework_{framework['id']}"]
                                st.success("Framework updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update framework.")
                    with col2:
                        if st.button("Load to Builder", key=f"load_edit_{framework['id']}", use_container_width=True):
                            st.session_state.framework_builder = {
                                'name': new_name,
                                'description': new_description,
                                'categories': framework.get('structure', {})
                            }
                            del st.session_state[f"editing_framework_{framework['id']}"]
                            st.success("Framework loaded to builder for editing!")
                            st.rerun()
                    with col3:
                        if st.button("Cancel", key=f"cancel_edit_{framework['id']}", use_container_width=True):
                            del st.session_state[f"editing_framework_{framework['id']}"]
                            st.rerun()
    else:
        st.info("No custom frameworks created yet. Create your first framework above!") 