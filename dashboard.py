
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "https://transportpredicton.onrender.com"

st.set_page_config(page_title="Advanced Transport Dashboard", layout="wide")

st.title("🚚 Advanced Transport Dashboard")

# -------------------------------
# Section 1: Historical Transport Data
# -------------------------------
st.header("📊 Logged Transport Data")

if st.button("Refresh Data"):
    transports = requests.get(f"{API_URL}/transports/").json()
    df = pd.DataFrame(transports)
    if not df.empty:
        st.dataframe(df)

        # Pie chart of mode usage
        mode_counts = df['mode'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(mode_counts, labels=mode_counts.index, autopct='%1.1f%%')
        ax.set_title("Distribution of Transport Modes")
        st.pyplot(fig)
    else:
        st.warning("No transport data logged yet.")

# -------------------------------
# Section 2: Predict Transport Mode
# -------------------------------
st.header("🤖 Predict Best Transport Mode")

with st.form("predict_form"):
    weight = st.number_input("Weight (kg)", min_value=1, step=1)
    volume = st.number_input("Volume (m³)", min_value=1, step=1)
    distance = st.number_input("Distance (km)", min_value=1, step=1)
    priority = st.slider("Priority (1 = Low, 5 = High)", 1, 5, 3)

    road_available = st.selectbox("Road Available?", [0, 1])
    rail_available = st.selectbox("Rail Available?", [0, 1])
    air_available = st.selectbox("Air Available?", [0, 1])
    water_available = st.selectbox("Water Available?", [0, 1])

    submitted = st.form_submit_button("Predict")

if submitted:
    params = {
        "weight": weight,
        "volume": volume,
        "distance": distance,
        "priority": priority,
        "road_available": road_available,
        "rail_available": rail_available,
        "air_available": air_available,
        "water_available": water_available,
    }

    response = requests.post(f"{API_URL}/predict/", params=params)

    if response.status_code == 200:
        result = response.json()
        st.subheader(f"✅ Recommended Mode: **{result['recommended_mode']}**")
        st.write("### Justification")
        for reason in result["justification"]:
            st.markdown(f"- {reason}")

        # -------------------------------
        # Section 3: Comparison Charts
        # -------------------------------
        st.write("### 📉 Mode Comparison Analysis")

        comparison_data = [
            {"Mode": "Road", "Cost": distance*5, "CO2": distance*0.25},
            {"Mode": "Rail", "Cost": distance*3, "CO2": distance*0.15},
            {"Mode": "Air", "Cost": distance*10, "CO2": distance*0.50},
            {"Mode": "Water", "Cost": distance*2, "CO2": distance*0.10},
        ]
        df_compare = pd.DataFrame(comparison_data)

        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots()
            ax.bar(df_compare["Mode"], df_compare["Cost"])
            ax.set_title("Cost Comparison")
            ax.set_ylabel("Cost (₹ per km approx)")
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots()
            ax.bar(df_compare["Mode"], df_compare["CO2"])
            ax.set_title("CO₂ Emissions Comparison")
            ax.set_ylabel("Kg CO₂ per km")
            st.pyplot(fig)

    else:
        st.error("Prediction failed. Please check the API server.")
