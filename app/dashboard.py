import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
import os
from lang_config import LANG  # Import language config

# Set page config
st.set_page_config(
    page_title="Strawberry Analysis Dashboard",
    page_icon="🍓",
    layout="wide"
)

# Initialize session state for language if not already set
if 'language' not in st.session_state:
    st.session_state.language = 'en'


# Function to get text for current language
def get_text(key):
    return LANG[st.session_state.language].get(key, key)


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
    .language-selector {
        float: right;
        margin-top: -60px;
        position: relative;
        z-index: 1000;
    }
    </style>
""", unsafe_allow_html=True)

# Rest of your imports and functions
import base64


def get_image_as_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string


# Add responsive logo at the top
logo_base64 = get_image_as_base64("app/logo.png")
st.markdown(
    f"""
    <style>
    .logo-container {{
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }}
    .logo-img {{
        max-width: 100%;
        height: auto;
    }}
    /* Media query for mobile devices */
    @media (max-width: 400px) {{
        .logo-img {{
            max-width: 100%;
        }}
    }}
    </style>
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="Logo">
    </div>
    """,
    unsafe_allow_html=True
)


# Data Access Object for CSV
class CsvDAO:
    def __init__(self, file_path="app/final_data.csv"):
        self.file_path = file_path

    def load_data(self):
        if os.path.exists(self.file_path):
            data = pd.read_csv(self.file_path)
            data['Date'] = pd.to_datetime(data['Date'], format="%m/%d/%Y")
            return data
        return pd.DataFrame()

    def insert_data(self, new_data):
        try:
            # Load existing data
            if os.path.exists(self.file_path):
                existing_data = pd.read_csv(self.file_path)
            else:
                existing_data = pd.DataFrame()

            # Convert new_data dict to DataFrame with one row
            new_row = pd.DataFrame([new_data])

            # Append new data to existing
            updated_data = pd.concat([existing_data, new_row], ignore_index=True)

            # Save back to CSV
            updated_data.to_csv(self.file_path, index=False)
            return True, "Data inserted successfully"
        except Exception as e:
            return False, f"Error inserting data: {str(e)}"


# Initialize DAO
data_dao = CsvDAO()


# Function to load data
@st.cache_data
def load_data():
    return data_dao.load_data()


# Load the data
data = load_data()

# Add language selector (right-aligned)
col1, col2 = st.columns([6, 1])
with col2:
    selected_lang = st.selectbox(
        "🌐",
        options=["English", "한국어"],
        index=0 if st.session_state.language == "en" else 1,
        label_visibility="collapsed"
    )

    # Update the session state based on selection
    if selected_lang == "English" and st.session_state.language != "en":
        st.session_state.language = "en"
        st._rerun()
    elif selected_lang == "한국어" and st.session_state.language != "ko":
        st.session_state.language = "ko"
        st._rerun()

# Title
st.title(get_text("title"))

# Streamlit tabs - using translated text
view_tab, insert_tab = st.tabs([
    get_text("view_data_tab"),
    get_text("insert_data_tab")
])

# View Data tab
with view_tab:
    st.sidebar.header(get_text("search_filters"))

    # 1. Product Name selector
    product_names = sorted(data['Product Name'].unique())
    selected_product = st.sidebar.selectbox(
        get_text("select_product"),
        product_names
    )

    # Filter data by product
    product_data = data[data['Product Name'] == selected_product]

    # 2. Date selector
    available_dates = sorted(product_data['Date'].unique())
    selected_date = st.sidebar.selectbox(
        get_text("select_date"),
        available_dates,
        format_func=lambda x: x.strftime('%Y-%m-%d')
    )

    # Filter data by date
    date_data = product_data[product_data['Date'] == selected_date]

    # 3. Section selector
    available_sections = sorted(date_data['Section'].unique())
    selected_section = st.sidebar.selectbox(
        get_text("select_section"),
        available_sections
    )

    # Filter data by section
    section_data = date_data[date_data['Section'] == selected_section]

    # 4. Plant selector
    available_plants = sorted(section_data['Plant'].unique())
    selected_plant = st.sidebar.selectbox(
        get_text("select_plant"),
        available_plants
    )

    # Filter data by plant
    plant_data = data[
        (data['Product Name'] == selected_product) &
        (data['Section'] == selected_section) &
        (data['Plant'] == selected_plant)
        ].sort_values(by='Date')

    # 5. Property selector
    available_properties = [
        'Fruit vertical length', 'Fruit horizontal length', 'Fruit weight',
        'Hardness', 'Sweetness', 'Acidity', 'Color_L', 'Color_a', 'Color_b',
    ]

    selected_properties = st.sidebar.multiselect(
        get_text("select_properties"),
        available_properties,
        default=['Fruit weight', 'Sweetness']
    )

    # Main content - View Mode
    st.subheader(get_text("filtered_data"))
    st.dataframe(plant_data, use_container_width=True)

    # Time series plots for each selected property
    if selected_properties:
        st.subheader(get_text("time_series"))

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
            st.info(get_text("no_historical_data"))

    # Download button for filtered data
    st.markdown("---")


    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')


    st.download_button(
        label=get_text("download_button"),
        data=convert_df_to_csv(plant_data),
        file_name=f'strawberry_data_{selected_product}_{selected_date.strftime("%Y%m%d")}_S{selected_section}_P{selected_plant}.csv',
        mime='text/csv',
    )

# Insert Data Mode
with insert_tab:
    st.subheader(get_text("insert_new"))

    # Create form for data entry
    with st.form("insert_data_form"):
        col1, col2 = st.columns(2)

        with col1:
            # Basic information
            new_product_name = st.selectbox(
                "Product Name",
                sorted(data['Product Name'].unique()) if not data.empty else [""]
            )
            new_date = st.date_input("Date", datetime.now())
            new_section = st.number_input("Section", min_value=1, step=1)
            new_plant = st.number_input("Plant", min_value=1, step=1)

            # Fruit measurements
            st.subheader(get_text("fruit_measurements"))
            new_vertical_length = st.number_input("Fruit Vertical Length (mm)", min_value=0.0, step=0.1)
            new_horizontal_length = st.number_input("Fruit Horizontal Length (mm)", min_value=0.0, step=0.1)
            new_weight = st.number_input("Fruit Weight (g)", min_value=0.0, step=0.1)

        with col2:
            # Quality measures
            st.subheader(get_text("quality_measures"))
            new_hardness = st.number_input("Hardness", min_value=0.0, step=0.1)
            new_sweetness = st.number_input("Sweetness (Brix)", min_value=0.0, step=0.1)
            new_acidity = st.number_input("Acidity", min_value=0.0, step=0.01)

            # Color
            st.subheader(get_text("color_metrics"))
            new_color_l = st.number_input("Color L", min_value=0.0, step=0.1)
            new_color_a = st.number_input("Color a", min_value=0.0, step=0.1)
            new_color_b = st.number_input("Color b", min_value=0.0, step=0.1)

        # Submit button
        submitted = st.form_submit_button(get_text("insert_btn"))

    # Handle form submission
    if submitted:
        new_data = {
            "Product Name": new_product_name,
            "Date": new_date.strftime("%m/%d/%Y"),
            "Section": new_section,
            "Plant": new_plant,
            "Fruit vertical length": new_vertical_length,
            "Fruit horizontal length": new_horizontal_length,
            "Fruit weight": new_weight,
            "Hardness": new_hardness,
            "Sweetness": new_sweetness,
            "Acidity": new_acidity,
            "Color_L": new_color_l,
            "Color_a": new_color_a,
            "Color_b": new_color_b,
        }

        # Insert data
        success, message = data_dao.insert_data(new_data)

        if success:
            st.success(message)
            st.cache_data.clear()
        else:
            st.error(message)

# Footer
st.markdown(get_text("footer"))
