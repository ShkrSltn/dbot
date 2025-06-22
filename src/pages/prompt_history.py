import streamlit as st
from services.db.crud._prompt_history import (
    get_user_prompt_history, 
    clear_user_prompt_history,
    get_prompt_history_stats,
    get_best_performing_prompts,
    delete_prompt_history_entry
)

def display_prompt_history():
    """Display prompt testing history component"""
    
    # Prompt History Section
    st.markdown("---")
    st.subheader("📊 Prompt Testing History")
    st.markdown("Track and compare the performance of different prompts across various tests.")
    
    # Get history statistics
    history_stats = get_prompt_history_stats(st.session_state.user["id"])
    
    if history_stats.get("total_entries", 0) > 0:
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tests", history_stats.get("total_entries", 0))
        with col2:
            st.metric("Unique Prompts", history_stats.get("unique_prompts_tested", 0))
        with col3:
            # Clear history button
            if st.button("🗑️ Clear History", help="Delete all prompt testing history"):
                if 'confirm_clear_history' not in st.session_state:
                    st.session_state.confirm_clear_history = False
                st.session_state.confirm_clear_history = True
        
        # Handle clear history confirmation
        if st.session_state.get('confirm_clear_history', False):
            st.error("⚠️ Are you sure you want to delete ALL prompt testing history? This action cannot be undone!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("YES, CLEAR ALL HISTORY", type="primary"):
                    deleted_count = clear_user_prompt_history(st.session_state.user["id"])
                    st.session_state.confirm_clear_history = False
                    st.success(f"✅ Cleared {deleted_count} history entries!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_clear_history = False
                    st.rerun()
        
        # Display history tabs
        tab1, tab2, tab3 = st.tabs(["Recent History", "Best Performers", "All History"])
        
        with tab1:
            _display_recent_history()
        
        with tab2:
            _display_best_performers()
        
        with tab3:
            _display_all_history()
    
    else:
        st.info("🔍 No prompt testing history yet. Test some prompts above to build your history!")
        st.markdown("Your testing history will help you:")
        st.markdown("- 📈 Track which prompts work best")
        st.markdown("- 🔄 Compare different approaches")
        st.markdown("- 📊 Analyze performance metrics")
        st.markdown("- 🎯 Optimize your prompt engineering process")

def _display_recent_history():
    """Display recent testing history tab"""
    st.markdown("### 🕐 Recent Testing History")
    recent_history = get_user_prompt_history(st.session_state.user["id"], limit=10)
    
    if recent_history:
        for i, entry in enumerate(recent_history):
            with st.expander(f"Test #{i+1}: {entry['prompt_name']} - {entry['created_at'].strftime('%Y-%m-%d %H:%M')}", expanded=False):
                # Display basic info
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**Original Statement:**")
                    st.info(entry['original_statement'])
                    
                    st.markdown("**Settings:**")
                    settings = entry.get('settings', {})
                    st.write(f"• Length: {settings.get('statement_length', 'N/A')} chars")
                    st.write(f"• Profile: {settings.get('profile_type', 'N/A')}")
                    st.write(f"• Evaluation: {'Yes' if settings.get('evaluation_enabled', False) else 'No'}")
                    st.write(f"• Attempts: {entry.get('attempts', 1)}")
                
                with col2:
                    st.markdown("**Enriched Result:**")
                    st.success(entry['enriched_statement'])
                    
                    if entry.get('metrics'):
                        st.markdown("**Quality Metrics:**")
                        metrics = entry['metrics']
                        metrics_cols = st.columns(3)
                        with metrics_cols[0]:
                            st.metric("TF-IDF", f"{metrics.get('cosine_tfidf', 0):.3f}")
                        with metrics_cols[1]:
                            st.metric("Embedding", f"{metrics.get('cosine_embedding', 0):.3f}")
                        with metrics_cols[2]:
                            reading_ease = metrics.get('readability', {}).get('estimated_reading_ease', 0)
                            st.metric("Reading Ease", f"{reading_ease:.1f}")
                
                # Show evaluation if available
                if entry.get('evaluation_result'):
                    st.markdown("**AI Evaluation:**")
                    st.markdown(entry['evaluation_result'])
                
                # Delete button for individual entries
                if st.button(f"Delete Entry", key=f"delete_entry_{entry['id']}"):
                    if delete_prompt_history_entry(st.session_state.user["id"], entry['id']):
                        st.success("Entry deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete entry.")
    else:
        st.info("No recent history available.")

def _display_best_performers():
    """Display best performing prompts tab"""
    st.markdown("### 🏆 Best Performing Prompts")
    
    # Metric selector
    metric_options = {
        "cosine_embedding": "Embedding Similarity",
        "cosine_tfidf": "TF-IDF Similarity",
        "estimated_reading_ease": "Reading Ease"
    }
    
    selected_metric = st.selectbox(
        "Sort by metric:",
        options=list(metric_options.keys()),
        format_func=lambda x: metric_options[x],
        index=0
    )
    
    best_prompts = get_best_performing_prompts(
        st.session_state.user["id"], 
        metric_key=selected_metric if selected_metric in ["cosine_embedding", "cosine_tfidf"] else f"readability.{selected_metric}",
        limit=5
    )
    
    if best_prompts:
        for i, entry in enumerate(best_prompts):
            metric_value = entry.get('metric_value', 0)
            st.markdown(f"**#{i+1} - {entry['prompt_name']}** (Score: {metric_value:.3f})")
            
            with st.expander(f"Details - {entry['created_at'].strftime('%Y-%m-%d %H:%M')}", expanded=False):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**Original:**")
                    st.text_area("", value=entry['original_statement'], height=100, disabled=True, key=f"best_orig_{i}")
                
                with col2:
                    st.markdown("**Enriched:**")
                    st.text_area("", value=entry['enriched_statement'], height=100, disabled=True, key=f"best_enr_{i}")
                
                # Show prompt content
                st.markdown("**Prompt Used:**")
                st.code(entry['prompt_content'], language="text")
    else:
        st.info("No performance data available yet.")

def _display_all_history():
    """Display complete history tab"""
    st.markdown("### 📋 Complete History")
    
    all_history = get_user_prompt_history(st.session_state.user["id"])
    
    if all_history:
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            unique_prompts = list(set([entry['prompt_name'] for entry in all_history]))
            prompt_filter = st.multiselect("Filter by prompt:", unique_prompts, default=unique_prompts)
        
        with col2:
            # Date range filter could be added here
            pass
        
        # Filter history
        filtered_history = [entry for entry in all_history if entry['prompt_name'] in prompt_filter]
        
        st.write(f"Showing {len(filtered_history)} out of {len(all_history)} entries")
        
        # Display in a more compact format
        for entry in filtered_history:
            cols = st.columns([2, 2, 1, 1, 1, 1])
            
            with cols[0]:
                st.write(f"**{entry['prompt_name']}**")
                st.caption(entry['created_at'].strftime('%Y-%m-%d %H:%M'))
            
            with cols[1]:
                st.write(entry['original_statement'][:50] + "..." if len(entry['original_statement']) > 50 else entry['original_statement'])
            
            with cols[2]:
                if entry.get('metrics'):
                    st.write(f"{entry['metrics'].get('cosine_embedding', 0):.3f}")
                else:
                    st.write("N/A")
            
            with cols[3]:
                if entry.get('metrics'):
                    st.write(f"{entry['metrics'].get('cosine_tfidf', 0):.3f}")
                else:
                    st.write("N/A")
            
            with cols[4]:
                st.write(f"{entry.get('attempts', 1)}")
            
            with cols[5]:
                if st.button("View", key=f"view_{entry['id']}"):
                    # Store entry for viewing
                    st.session_state[f"viewing_entry_{entry['id']}"] = True
                    st.rerun()
            
            # Show detailed view if requested
            if st.session_state.get(f"viewing_entry_{entry['id']}", False):
                with st.expander(f"Detailed View - {entry['prompt_name']}", expanded=True):
                    st.markdown("**Original Statement:**")
                    st.info(entry['original_statement'])
                    st.markdown("**Enriched Statement:**")
                    st.success(entry['enriched_statement'])
                    
                    if entry.get('evaluation_result'):
                        st.markdown("**AI Evaluation:**")
                        st.markdown(entry['evaluation_result'])
                    
                    if st.button("Close", key=f"close_{entry['id']}"):
                        st.session_state[f"viewing_entry_{entry['id']}"] = False
                        st.rerun()
            
            st.divider()
    else:
        st.info("No history available.") 