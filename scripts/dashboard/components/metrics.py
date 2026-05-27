"""
KPI card components for the SON Dashboard.
"""
import streamlit as st

import plotly.graph_objects as go

def kpi_card(label: str, value: str, delta: str = None, color: str = "#00d4aa"):
    """Renders a styled KPI card."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1a1f2e 0%, #162033 100%);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid {color};
        margin-bottom: 10px;
    ">
        <p style="color: #94a3b8; font-size: 14px; margin: 0;">{label}</p>
        <h2 style="color: #f8fafc; margin: 10px 0 5px 0;">{value}</h2>
        {f'<p style="color: {color}; font-size: 12px; margin: 0;">{delta}</p>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

def kpi_card_with_sparkline(label: str, value: str, series: list, color: str = "#00d4aa"):
    """Renders a KPI card with a mini sparkline chart."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        kpi_card(label, value, color=color)
        
    with col2:
        if series and len(series) > 0:
            # Mini sparkline
            fig = go.Figure(go.Scatter(
                y=series, mode='lines', 
                line=dict(color=color, width=2),
                fill='tozeroy', fillcolor=f"{color}22"
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=80,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.markdown("""
            <div style="height: 80px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 12px;">
                N/A
            </div>
            """, unsafe_allow_html=True)
