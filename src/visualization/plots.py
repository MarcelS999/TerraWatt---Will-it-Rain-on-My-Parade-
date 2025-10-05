# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================

import matplotlib.pyplot as plt
import streamlit as st

def plot_wind_histogram(series, results):
    fig, ax = plt.subplots()
    ax.hist(series, bins=10, color="skyblue", edgecolor="black")
    ax.axvline(results['expected'], color="red", linestyle="--", label="Mean")
    ax.axvline(results['p25'], color="green", linestyle="--", label="P25")
    ax.axvline(results['p75'], color="green", linestyle="--", label="P75")
    ax.set_title("Wind Speed Distribution", fontsize=14, fontweight='bold')
    ax.set_xlabel("Wind Speed (m/s)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Frequency (Number of Occurrences)", fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

def plot_expected_profile(display_df):
    # Add axis titles and description for the line chart
    st.line_chart(display_df, x="Height (m)", y="Wind Speed (m/s)")
    st.caption("📈 **Expected Wind Profile** - Wind speed variation with height")
    st.dataframe(display_df.round(2))
