import streamlit as st
import pandas as pd
import os
from beverly_knits_data_integration import BeverlyKnitsDataIntegrator

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Beverly Knits Data Integration",
    page_icon="🧶",
    layout="wide"
)

# --- Helper Functions ---
def display_df_with_download(df, header, filename):
    """Displays a dataframe with a header and a download button."""
    st.subheader(header)
    st.dataframe(df)
    st.download_button(
        label=f"Download {filename}",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=filename,
        mime='text/csv',
    )

# --- Main Application ---
st.title("Beverly Knits Data Integration Portal 🧶")

st.write("""
This portal allows you to run the complete data integration process for the Beverly Knits AI Raw Material Planner.
The process reads raw data files, applies automatic quality fixes, and generates clean, integrated CSV files for the planning system.
""")

# --- Sidebar for Configuration ---
st.sidebar.header("Configuration")
data_path = st.sidebar.text_input("Data Directory Path", "data/")
output_path = st.sidebar.text_input("Output Directory Path", "output/")

if st.sidebar.button("Run Data Integration"):
    try:
        # --- Running the Integration ---
        st.header("Integration Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Initialize the integrator
        integrator = BeverlyKnitsDataIntegrator(data_path=data_path, output_path=output_path)
        
        status_text.text("Step 1/4: Loading source data files...")
        integrator.load_data()
        progress_bar.progress(25)

        status_text.text("Step 2/4: Processing and cleaning data...")
        integrator.process_data()
        progress_bar.progress(50)

        status_text.text("Step 3/4: Saving integrated files...")
        integrator.save_integrated_files()
        progress_bar.progress(75)
        
        status_text.text("Step 4/4: Generating data quality report...")
        integrator.save_quality_report()
        progress_bar.progress(100)

        st.success("✅ Data integration completed successfully!")

        # --- Displaying Results ---
        st.header("Integration Results")

        # Display Data Quality Report
        st.subheader("Data Quality and Automatic Fix Report")
        report_path = os.path.join(output_path, "data_quality_report_v2.txt")
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                st.text(f.read())
        else:
            st.warning("Data quality report not found.")

        # Display Integrated Files
        output_files = {
            "Integrated Materials": "integrated_materials_v2.csv",
            "Integrated Suppliers": "integrated_suppliers_v2.csv",
            "Integrated Inventory": "integrated_inventory_v2.csv",
            "Integrated BOMs": "integrated_boms_v2.csv"
        }

        for header, filename in output_files.items():
            filepath = os.path.join(output_path, filename)
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                display_df_with_download(df.head(), header, filename)
            else:
                st.warning(f"{filename} not found in {output_path}")

    except Exception as e:
        st.error(f"An error occurred during integration: {e}")

else:
    st.info("Click the 'Run Data Integration' button in the sidebar to start the process.")
