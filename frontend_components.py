"""
Reusable UI Components for Frontend
"""
import streamlit as st
import time
from typing import Callable, Optional

def toast_message(message: str, type: str = "success"):
    """Show a toast notification"""
    icons = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
        "warning": "⚠️"
    }
    st.markdown(f"""
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        background: {'#27ae60' if type == 'success' else '#e74c3c' if type == 'error' else '#3498db'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    ">
        {icons.get(type, '📌')} {message}
    </div>
    """, unsafe_allow_html=True)
    time.sleep(2)

def loading_animation(message: str = "Processing..."):
    """Show a loading animation"""
    return st.spinner(message)

def progress_tracker(stages: list):
    """Show a progress tracker"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stage in enumerate(stages):
        status_text.text(stage)
        progress_bar.progress((i + 1) / len(stages))
        time.sleep(0.5)
    
    status_text.empty()
    progress_bar.empty()

def metric_card(title: str, value: str, icon: str, color: str = "#667eea"):
    """Create a metric card"""
    st.markdown(f"""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border-left: 4px solid {color};
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    ">
        <div style="font-size: 2rem;">{icon}</div>
        <div style="font-size: 0.9rem; color: #718096;">{title}</div>
        <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def create_tooltip(text: str, tooltip: str):
    """Create a tooltip"""
    return st.markdown(f"""
    <div style="position: relative; display: inline-block;">
        <span style="border-bottom: 1px dotted #999;">{text}</span>
        <div style="
            visibility: hidden;
            background-color: #555;
            color: #fff;
            text-align: center;
            padding: 5px 10px;
            border-radius: 6px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
        ">
            {tooltip}
        </div>
    </div>
    <style>
        div:hover > div {{
            visibility: visible;
            opacity: 1;
        }}
    </style>
    """, unsafe_allow_html=True)