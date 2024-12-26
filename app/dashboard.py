import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="Strawberry Analysis Dashboard",
    page_icon="🍓",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)


# Function to load data
@st.cache_data
def load_data():
    # Replace this with your actual data loading method
    path = "final_data.csv"
    data = pd.read_csv(path)
    # Convert Date to datetime
    data['Date'] = pd.to_datetime(data['Date'])
    return data


# Load the data
data = load_data()

# Title
st.title("🍓 Strawberry Analysis Dashboard")

# Sidebar filters
st.sidebar.header("Search Filters")

# 1. Product Name selector
product_names = sorted(data['Product Name'].unique())
selected_product = st.sidebar.selectbox(
    "1. Select Product Name",
    product_names
)

# Filter data by product
product_data = data[data['Product Name'] == selected_product]

# 2. Date selector
available_dates = sorted(product_data['Date'].unique())
selected_date = st.sidebar.selectbox(
    "2. Select Date",
    available_dates,
    format_func=lambda x: x.strftime('%Y-%m-%d')
)

# Filter data by date
date_data = product_data[product_data['Date'] == selected_date]

# 3. Section selector
available_sections = sorted(date_data['Section'].unique())
selected_section = st.sidebar.selectbox(
    "3. Select Section",
    available_sections
)

# Filter data by section
section_data = date_data[date_data['Section'] == selected_section]

# 4. Plant selector
available_plants = sorted(section_data['Plant'].unique())
selected_plant = st.sidebar.selectbox(
    "4. Select Plant",
    available_plants
)

# Filter data by plant
plant_data = section_data[section_data['Plant'] == selected_plant]

# Now based on Selected Product Name, Section and Plant, we can filter the data and sort it by Date
plant_data = data[
    (data['Product Name'] == selected_product) &
    (data['Section'] == selected_section) &
    (data['Plant'] == selected_plant)
    ].sort_values(by='Date')

# 5. Property selector
available_properties = [
    'Fruit vertical length', 'Fruit horizontal length', 'Fruit weight',
    'Hardness', 'Sweetness', 'Acidity', 'Color_L', 'Color_a', 'Color_b',
    'EC', 'Humidity', 'Sun', 'pH', 'Solid_Temperature', 'Temperature',
    'CO2', 'Solid_Moisture'
]

selected_properties = st.sidebar.multiselect(
    "5. Select Properties to Plot",
    available_properties,
    default=['Fruit weight', 'Sweetness']
)

# Main content
st.subheader("Filtered Data")
st.dataframe(plant_data, use_container_width=True)

# Time series plots for each selected property
if selected_properties:
    st.subheader("Time Series Analysis")

    # Get historical data for the selected plant
    historical_data = data[
        (data['Product Name'] == selected_product) &
        (data['Section'] == selected_section) &
        (data['Plant'] == selected_plant)
        ]

    if not historical_data.empty:
        for property in selected_properties:
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=historical_data['Date'],
                    y=historical_data[property],
                    name=property,
                    mode='lines+markers'
                )
            )

            fig.update_layout(
                title=f"{property} Over Time for Plant {selected_plant} in Section {selected_section}",
                xaxis_title="Date",
                yaxis_title=property,
                height=400,
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical data available for the selected plant.")

# Download button for filtered data
st.markdown("---")


def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')


st.download_button(
    label="Download filtered data as CSV",
    data=convert_df_to_csv(plant_data),
    file_name=f'strawberry_data_{selected_product}_{selected_date.strftime("%Y%m%d")}_S{selected_section}_P{selected_plant}.csv',
    mime='text/csv',
)

# Footer
st.markdown("Dashboard created for Strawberry Analysis")
