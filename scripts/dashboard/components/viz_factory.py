"""
Visualization Strategy pattern for the SON Dashboard.
Decouples plot logic from page layout.
"""
import streamlit as st
import polars as pl
import numpy as np
from typing import List, Optional
from scripts.dashboard.components.charts import plot_timeseries, plot_heatmap, plot_sankey_dynamic
from scripts.dashboard.resilience import heatmap_cb, sankey_cb

class VizStrategy:
    """Base class for visualization strategies."""
    @staticmethod
    def render(*args, **kwargs):
        pass

class TimelineViz(VizStrategy):
    @staticmethod
    def render(timeline_df: pl.DataFrame):
        # Conversion timestamp -> heure de la journée (0-23.5)
        df_tl = timeline_df.with_columns(((pl.col("slot_30m") / 1800) % 48 / 2).alias("h"))
        
        # Formatage lisible HH:MM
        df_tl = df_tl.with_columns(
            (
                pl.col("h").floor().cast(pl.Int32).cast(pl.String).str.pad_start(2, "0") + 
                ":" + 
                pl.when((pl.col("h") * 2) % 2 >= 0.5).then(pl.lit("30")).otherwise(pl.lit("00"))
            ).alias("hour")
        ).sort("h")
        
        st.plotly_chart(plot_timeseries(df_tl, "hour", ["static", "greedy", "milp"], ["Baseline", "Greedy Industry", "MILP Global"]), use_container_width=True)

class SpatialHeatmapViz(VizStrategy):
    @staticmethod
    def render(matrix: np.ndarray, title: str, colorscale: str = "Reds"):
        def _render():
            st.plotly_chart(plot_heatmap(matrix, title, colorscale=colorscale), use_container_width=True)
        
        heatmap_cb.call(_render, lambda: st.error("Heatmap rendering failed."))

class SankeyFlowViz(VizStrategy):
    @staticmethod
    def render(flows_df: pl.DataFrame):
        def _render():
            st.plotly_chart(plot_sankey_dynamic(flows_df.filter(pl.col("master_id")!=pl.col("target_ant"))), use_container_width=True)
        
        sankey_cb.call(_render, lambda: st.error("Sankey diagram rendering failed."))
