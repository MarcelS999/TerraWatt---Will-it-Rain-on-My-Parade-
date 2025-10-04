import matplotlib.pyplot as plt
import streamlit as st

def plot_wind_histogram(series, results):
    fig, ax = plt.subplots()
    ax.hist(series, bins=10, color="skyblue", edgecolor="black")
    ax.axvline(results['expected'], color="red", linestyle="--", label="Mean")
    ax.axvline(results['p25'], color="green", linestyle="--", label="P25")
    ax.axvline(results['p75'], color="green", linestyle="--", label="P75")
    ax.set_title("Wind speed distribution")
    ax.set_xlabel("Wind speed (m/s)")
    ax.set_ylabel("Frequency")
    ax.legend()
    st.pyplot(fig)

def plot_expected_profile(display_df):
    st.line_chart(display_df)
    st.dataframe(display_df.round(2))
