import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def display_analytics():
    st.title("📊 Analytics Dashboard")
    
    if len(st.session_state.enriched_statements) < 1:
        st.warning("No enriched statements available for analysis.")
        st.info("Go to the Enrichment Demo or Batch Enrichment page to create more statements.")
        st.stop()
        
    # Prepare data for visualization
    data = []
    for i, item in enumerate(st.session_state.enriched_statements):
        data.append({
            "id": i + 1,
            "original": item["original"],
            "enriched": item["enriched"],
            "original_length": len(item["original"]),
            "enriched_length": len(item["enriched"]),
            "tfidf_similarity": item["metrics"]["cosine_tfidf"],
            "embedding_similarity": item["metrics"]["cosine_embedding"],
            "reading_ease": item["metrics"]["readability"]["estimated_reading_ease"],
            "word_count": item["metrics"]["readability"]["word_count"],
            "avg_word_length": item["metrics"]["readability"]["avg_word_length"]
        })
    
    df = pd.DataFrame(data)
    
    # Create tabs for different visualizations
    viz_tabs = st.tabs(["Overview", "Statement Comparison", "Quiz Results"])
    
    with viz_tabs[0]:
        # Overview metrics
        st.subheader("Overview Metrics")
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Statements", len(df))
            
        with col2:
            avg_similarity = df["embedding_similarity"].mean()
            st.metric("Avg. Embedding Similarity", f"{avg_similarity:.2f}")
            
        with col3:
            avg_reading_ease = df["reading_ease"].mean()
            st.metric("Avg. Reading Ease", f"{avg_reading_ease:.1f}")
        
        # Create a correlation heatmap
        st.subheader("Correlation Matrix")
        
        # Select numeric columns for correlation
        numeric_cols = ["original_length", "enriched_length", "tfidf_similarity", 
                        "embedding_similarity", "reading_ease", "word_count", "avg_word_length"]
        
        corr_matrix = df[numeric_cols].corr()
        
        # Create a heatmap using Plotly
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Correlation Between Metrics"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Length comparison
        st.subheader("Statement Length Comparison")
        
        # Create a scatter plot
        fig = px.scatter(
            df,
            x="original_length",
            y="enriched_length",
            size="embedding_similarity",
            color="reading_ease",
            hover_name="id",
            labels={
                "original_length": "Original Length (chars)",
                "enriched_length": "Enriched Length (chars)",
                "embedding_similarity": "Embedding Similarity",
                "reading_ease": "Reading Ease"
            },
            title="Original vs. Enriched Statement Length"
        )
        
        # Add a diagonal line for reference
        fig.add_shape(
            type="line",
            x0=min(df["original_length"]),
            y0=min(df["original_length"]),
            x1=max(df["original_length"]),
            y1=max(df["original_length"]),
            line=dict(color="gray", dash="dash")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with viz_tabs[1]:
        # Statement comparison
        st.subheader("Statement Comparison")
        selected_id = st.selectbox("Select a statement to view details:", df["id"].tolist())

        if selected_id:
            idx = selected_id - 1
            selected_item = st.session_state.enriched_statements[idx]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Original Statement")
                st.info(selected_item["original"])

            with col2:
                st.markdown("### Enriched Statement")
                st.success(selected_item["enriched"])

            # Display detailed metrics
            st.markdown("### Detailed Metrics")
            metrics_df = pd.DataFrame([{
                "Metric": key,
                "Value": value
            } for key, value in selected_item["metrics"]["readability"].items()])

            st.dataframe(metrics_df)
            
    with viz_tabs[2]:
        # Quiz results visualization
        st.subheader("Quiz Preference Results")
        
        total_responses = st.session_state.quiz_results["original"] + st.session_state.quiz_results["enriched"]
        
        if total_responses == 0:
            st.info("No quiz results available yet. Take the quiz to see your preferences.")
        else:
            original_percentage = (st.session_state.quiz_results["original"] / total_responses) * 100
            enriched_percentage = (st.session_state.quiz_results["enriched"] / total_responses) * 100
            
            # Create interactive pie chart with Plotly
            labels = ["Original Statements", "Personalized Statements"]
            values = [st.session_state.quiz_results["original"], st.session_state.quiz_results["enriched"]]
            
            # Define colors
            colors = ['#3498db', '#ff7675']
            
            # Create figure
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.4,  # Creates a donut chart
                marker=dict(colors=colors),
                textinfo='label+percent',
                textposition='outside',
                pull=[0.1 if original_percentage > enriched_percentage else 0, 
                      0 if original_percentage > enriched_percentage else 0.1],
                hoverinfo='label+value+percent'
            )])
            
            # Update layout
            fig.update_layout(
                title={
                    'text': "Statement Preference Distribution",
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                height=500,
                margin=dict(t=80, b=80, l=40, r=40),
                annotations=[dict(
                    text=f'Total: {total_responses}',
                    x=0.5, y=0.5,
                    font_size=20,
                    showarrow=False
                )]
            )
            
            st.plotly_chart(fig, use_container_width=True) 