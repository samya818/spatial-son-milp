"""
Standardized Plotly visualization wrappers for the SON Dashboard.
"""
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from scripts.dashboard.config import config

def plot_gauge(value: float, reference: float, title: str) -> go.Figure:
    """Plots a performance gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={'reference': reference, 'increasing': {'color': config.PRIMARY_COLOR}},
        title={'text': title, 'font': {'size': 16, 'color': '#e2e8f0'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#64748b"},
            'bar': {'color': config.PRIMARY_COLOR},
            'bgcolor': "#1e293b",
            'borderwidth': 2,
            'bordercolor': "#334155",
            'steps': [
                {'range': [0, 30], 'color': "#3f1818"},
                {'range': [30, 60], 'color': "#3f3618"},
                {'range': [60, 100], 'color': "#183f2e"}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': value}
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        height=300, 
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def plot_sankey_dynamic(df_flows: pl.DataFrame, max_flows: int = 20) -> go.Figure:
    """Plots a dynamic Sankey diagram from transfer flows.
    
    Args:
        df_flows: DataFrame with [master_id, target_ant, transferred_vol].
        max_flows: Maximum number of flows to display.
    """
    if df_flows.is_empty():
        return go.Figure().update_layout(title="No flows to display")
        
    # Aggregate flows to avoid too many links
    df_agg = (df_flows.group_by(["master_id", "target_ant"])
              .agg(pl.col("transferred_vol").sum())
              .filter(pl.col("transferred_vol") > 0.1) # Filter tiny flows
              .sort("transferred_vol", descending=True)
              .head(max_flows)) # Top N flows for clarity
              
    nodes = list(set(df_agg["master_id"].to_list() + df_agg["target_ant"].to_list()))
    node_map = {name: i for i, name in enumerate(nodes)}
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20, line=dict(color="#334155", width=0.5),
            label=nodes,
            # Color by site type: assume sites with more connections are hubs (macros)
            color=[config.PRIMARY_COLOR if n in df_agg["master_id"].to_list() else config.SECONDARY_COLOR for n in nodes]
        ),
        link=dict(
            source=[node_map[s] for s in df_agg["master_id"]],
            target=[node_map[t] for t in df_agg["target_ant"]],
            value=df_agg["transferred_vol"].to_list(),
            color="rgba(0, 212, 170, 0.4)"
        )
    )])
    
    fig.update_layout(
        font=dict(color='#e2e8f0', size=12),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=500,
        margin=dict(l=20, r=20, t=20, b=40),
        annotations=[dict(text=f"Top {len(df_agg)} flux affichés", showarrow=False, xref="paper", yref="paper", x=0.5, y=-0.1)]
    )
    return fig

def plot_heatmap(matrix, title: str, colorscale: str = 'RdYlGn_r') -> go.Figure:
    """Plots a geographic heatmap of congestion."""
    fig = px.imshow(
        matrix,
        color_continuous_scale=colorscale,
        title=title,
        labels=dict(x="Longitude", y="Latitude", color="Volume")
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#0f172a',
        font=dict(color='#e2e8f0')
    )
    return fig

def plot_timeseries(df, x: str, y: list, labels: list) -> go.Figure:
    """Plots a comparison timeseries."""
    fig = go.Figure()
    colors = [config.DANGER_COLOR, config.PRIMARY_COLOR, config.SECONDARY_COLOR]
    
    for i, col in enumerate(y):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            mode='lines',
            name=labels[i],
            line=dict(color=colors[i % len(colors)], width=3),
            fill='tonexty' if i == 0 else 'tozeroy'
        ))
        
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#0f172a',
        font=dict(color='#e2e8f0'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        hovermode='x unified'
    )
    return fig
