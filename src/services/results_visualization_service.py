import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from components.meta_questions import get_default_criteria

def create_preference_pie_chart(original_count, enriched_count, neither_count, title_suffix="", chart_key="preference_pie"):
    """Create a pie chart for statement preferences"""
    total_responses = original_count + enriched_count + neither_count
    
    if total_responses == 0:
        return None
    
    original_percentage = (original_count / total_responses) * 100
    enriched_percentage = (enriched_count / total_responses) * 100
    neither_percentage = (neither_count / total_responses) * 100
    
    # Create interactive pie chart with Plotly
    labels = ["Original Statements", "Personalized Statements", "No Preference"]
    values = [original_count, enriched_count, neither_count]
    colors = ['#3498db', '#ff7675', '#95a5a6']
    
    # Create figure
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,  # Creates a donut chart
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='outside',
        pull=[0.1 if original_percentage > max(enriched_percentage, neither_percentage) else 0, 
              0.1 if enriched_percentage > max(original_percentage, neither_percentage) else 0,
              0.1 if neither_percentage > max(original_percentage, neither_percentage) else 0],
        hoverinfo='label+value+percent',
        insidetextorientation='radial'
    )])
    
    # Update layout with improved spacing and positioning
    fig.update_layout(
        title={
            'text': f"Overall Statement Preference{title_suffix}",
            'y':0.99,
            'x':0.15,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=600,
        margin=dict(t=80, b=100, l=80, r=80),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        annotations=[
            dict(
                x=0.5,
                y=-0.1,
                text="",
                showarrow=False,
                xref="paper",
                yref="paper"
            )
        ]
    )
    
    return fig

def create_detailed_criterion_chart(values, criterion_name, chart_key):
    """Create a bar chart for detailed criterion results"""
    total = sum(values)
    if total == 0:
        return None
        
    weighted_sum = (values[0] * -2 + values[1] * -1 + values[2] * 0 + 
                   values[3] * 1 + values[4] * 2)
    tendency = weighted_sum / total
    
    # Create the bar chart
    categories = [
        "Completely prefer orig.", 
        "Somewhat prefer orig.", 
        "Neither", 
        "Somewhat prefer pers.", 
        "Completely prefer pers."
    ]
    
    # Calculate the tendency line position
    tendency_position = (tendency + 2) / 4 * 4  # Map from -2 to 2 range to 0 to 4 range
    
    # Create the bar chart
    detail_fig = go.Figure()
    
    # Add bars with consistent colors for all criteria
    detail_fig.add_trace(go.Bar(
        x=categories,
        y=values,
        text=values,
        textposition='auto',
        marker_color=['#3498db', '#74b9ff', '#e0e0e0', '#ffb8b8', '#ff7675'],
        hoverinfo='y+text'
    ))
    
    # Add tendency line
    detail_fig.add_shape(
        type="line",
        x0=tendency_position,
        y0=0,
        x1=tendency_position,
        y1=max(values) * 1.1 if max(values) > 0 else 10,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        )
    )
    
    # Add annotation for the tendency
    tendency_text = get_tendency_text(tendency)
        
    detail_fig.add_annotation(
        x=tendency_position,
        y=max(values) * 1.05 if max(values) > 0 else 5,
        text=tendency_text,
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40
    )
    
    # Update layout
    detail_fig.update_layout(
        xaxis=dict(
            title="Preference",
            tickangle=-45,
            tickfont=dict(size=9)
        ),
        yaxis=dict(
            title="Number of Responses"
        ),
        height=350,
        margin=dict(t=30, b=100, l=30, r=30),
        font=dict(size=10)
    )
    
    return detail_fig, tendency

def get_tendency_text(tendency):
    """Get tendency description text"""
    if tendency < -1:
        return "Strong preference for original"
    elif tendency < -0.1:
        return "Slight preference for original"
    elif tendency <= 0.1:
        return "No preference"
    elif tendency < 1:
        return "Slight preference for personalized"
    else:
        return "Strong preference for personalized"

def get_overall_interpretation_text(tendency, is_global=False):
    """Get overall interpretation text"""
    prefix = "Overall, users" if is_global else "You"
    
    if tendency < -1:
        emoji = "🔵" if is_global else ""
        text = f"{emoji} {prefix} strongly prefer original statements"
        if is_global:
            text += ". They value clarity and directness."
        else:
            text += " overall."
    elif tendency < -0.1:
        emoji = "🔵" if is_global else ""
        text = f"{emoji} {prefix} somewhat prefer original statements"
        if is_global:
            text += ". They lean towards clearer, more concise language."
        else:
            text += " overall."
    elif tendency <= 0.1:
        emoji = "⚪" if is_global else ""
        text = f"{emoji} {prefix} have no strong preference between original and personalized statements."
    elif tendency < 1:
        emoji = "🔴" if is_global else ""
        text = f"{emoji} {prefix} somewhat prefer personalized statements"
        if is_global:
            text += ". They appreciate context and detail."
        else:
            text += " overall."
    else:
        emoji = "🔴" if is_global else ""
        text = f"{emoji} {prefix} strongly prefer personalized statements"
        if is_global:
            text += ". They value detailed, contextual information."
        else:
            text += " overall."
    
    return text

def aggregate_detailed_results(all_quiz_results):
    """Aggregate detailed results from multiple quiz results"""
    default_criteria = get_default_criteria()
    criteria_keys = list(default_criteria.keys())
    
    aggregated_detailed_results = {
        key: {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, 
              "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0} 
        for key in criteria_keys
    }
    
    for result in all_quiz_results:
        detailed = result.get("detailed_results", {})
        for criterion in criteria_keys:
            if criterion in detailed:
                criterion_data = detailed[criterion]
                for preference in aggregated_detailed_results[criterion]:
                    if preference in criterion_data:
                        aggregated_detailed_results[criterion][preference] += criterion_data[preference]
    
    return aggregated_detailed_results

def create_competency_category_progress_bars(category_scores):
    """Create HTML progress bars for competency categories"""
    # Define colors for each category with better variety
    colors = {
        "Information and data literacy": "#3498db",
        "Communication and collaboration": "#e74c3c",
        "Digital content creation": "#f1c40f",
        "Safety": "#2ecc71",
        "Problem solving": "#e67e22"
    }
    
    for i, row in category_scores.iterrows():
        category = row["Category"]
        percentage = row["score_percentage"]
        
        # Get color for this category, fallback to blue if not found
        color = colors.get(category, "#3498db")
        
        # Create container with background color - removed count display
        container_html = f"""
        <div style="background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 3; font-weight: 500;">{category}</div>
                <div style="flex: 7; background-color: #f0f0f0; height: 30px; border-radius: 15px; position: relative;">
                    <div style="position: absolute; width: {percentage}%; height: 100%; background-color: {color}; border-radius: 15px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">{percentage:.0f}%</span>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(container_html, unsafe_allow_html=True)

def create_competency_subcategory_pie_chart(df, title="Competency by Subcategory", chart_key="subcategory_pie"):
    """Create a pie chart for competency subcategories"""
    # Group by subcategory and calculate average competency
    subcategory_data = df.groupby(["Category", "Subcategory"])["Competency_Value"].agg(["mean", "count"]).reset_index()
    subcategory_data["Percentage"] = (subcategory_data["mean"] / 5) * 100
    
    # Define colors for each category - updated to match progress bars
    color_map = {
        "Information and data literacy": "#3498db",
        "Communication and collaboration": "#e74c3c",
        "Digital content creation": "#f1c40f",
        "Safety": "#2ecc71",
        "Problem solving": "#e67e22"
    }
    
    # Create a list of colors based on the category of each subcategory
    subcategory_colors = []
    for category in subcategory_data["Category"]:
        base_color = color_map.get(category, "#3498db")
        subcategory_colors.append(base_color)
    
    overall_score_percentage = (df["Competency_Value"].mean() / 5) * 100
    
    # Create the pie chart
    fig = go.Figure(data=[go.Pie(
        labels=subcategory_data["Subcategory"],
        values=subcategory_data["Percentage"],
        hole=0.3,
        marker=dict(
            colors=subcategory_colors,
            line=dict(color='#FFFFFF', width=2)
        ),
        textinfo='label+percent',
        textposition='outside',
        insidetextorientation='radial',
        textfont=dict(size=10),
        hoverinfo='label+value+percent',
        hovertemplate='<b>%{label}</b><br>Score: %{value:.1f}%<extra></extra>'
    )])
    
    # Add text in the center
    fig.add_annotation(
        x=0.5, y=0.5,
        text=f"{overall_score_percentage:.0f}%",
        font=dict(size=24, color='#333333'),
        showarrow=False
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=600,
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def process_competency_data(competency_results):
    """Process competency results into a standardized DataFrame"""
    if not competency_results:
        return None
    
    comp_data = []
    for comp in competency_results:
        comp_data.append({
            "Category": comp.get("category", "Unknown"),
            "Subcategory": comp.get("subcategory", "Unknown"),
            "Statement": comp.get("statement", ""),
            "Competency": comp.get("competency", "Intermediate")
        })
    
    if not comp_data:
        return None
    
    df = pd.DataFrame(comp_data)
    
    # Map from responses to levels
    response_to_level = {
        "I have no knowledge of this / I never heard of this": "No knowledge",
        "I have only a limited understanding of this and need more explanations": "Basic",
        "I have a good understanding of this": "Intermediate",
        "I fully master this topic/issue and I could explain it to others": "Advanced",
        # Add short formats for backward compatibility
        "No knowledge": "No knowledge",
        "Basic": "Basic",
        "Intermediate": "Intermediate",
        "Advanced": "Advanced"
    }
    
    # Add numeric mapping for competency for visualization
    competency_map = {
        "No knowledge": 1,
        "Basic": 2,
        "Intermediate": 3,
        "Advanced": 4,
        "Expert": 5
    }
    
    # Convert response text to levels
    df["Competency_Level"] = df["Competency"].map(response_to_level)
    df["Competency_Value"] = df["Competency_Level"].map(competency_map)
    
    return df

def create_competency_level_distribution_chart(df, title="Distribution of Competency Levels", chart_key="competency_distribution"):
    """Create a bar chart showing distribution of competency levels"""
    # Count responses by competency level
    level_counts = df["Competency_Level"].value_counts()
    
    # Create bar chart for competency levels
    level_fig = go.Figure()
    
    level_colors = {
        "No knowledge": "#e74c3c",
        "Basic": "#f39c12", 
        "Intermediate": "#f1c40f",
        "Advanced": "#2ecc71"
    }
    
    levels = ["No knowledge", "Basic", "Intermediate", "Advanced"]
    counts = [level_counts.get(level, 0) for level in levels]
    colors = [level_colors.get(level, "#95a5a6") for level in levels]
    
    level_fig.add_trace(go.Bar(
        x=levels,
        y=counts,
        text=counts,
        textposition='auto',
        marker_color=colors,
        hoverinfo='y+text'
    ))
    
    level_fig.update_layout(
        title=title,
        xaxis=dict(title="Competency Level"),
        yaxis=dict(title="Number of Responses"),
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    return level_fig

def get_criteria_names():
    """Get mapping of criteria keys to display names"""
    return {
        "understand": "Understanding",
        "read": "Readability", 
        "detail": "Detail",
        "profession": "Professional Relevance",
        "assessment": "Self-Assessment"
    } 