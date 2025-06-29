"""
Beverly Knits Raw Material Planner - Streamlit Application

AI-driven raw material planning system with interactive web interface.
"""

import io
import os
import sys
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import BusinessRules
from data.sample_data_generator import SampleDataGenerator
from engine.planner import RawMaterialPlanner
from models.bom import BOMExploder
from models.forecast import ForecastProcessor
from models.inventory import InventoryNetter
from models.recommendation import RecommendationGenerator
from models.supplier import SupplierSelector
from utils.helpers import ReportGenerator


def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="Beverly Knits - Raw Material Planner",
        page_icon="🧶",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🧶 Beverly Knits - AI Raw Material Planner")
    st.markdown("*Intelligent supply chain planning for textile manufacturing*")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📊 Planning Dashboard", "⚙️ Configuration", "📈 Analytics", "ℹ️ About"]
    )
    
    if page == "📊 Planning Dashboard":
        show_planning_dashboard()
    elif page == "⚙️ Configuration":
        show_configuration_page()
    elif page == "📈 Analytics":
        show_analytics_page()
    else:
        show_about_page()


def show_planning_dashboard():
    """Main planning dashboard"""
    
    st.header("Raw Material Planning Dashboard")
    
    # Data input section
    st.subheader("1. Data Input")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_source = st.radio(
            "Choose data source:",
            ["Use Sample Data", "Upload CSV Files"]
        )
    
    with col2:
        if data_source == "Use Sample Data":
            num_skus = st.slider("Number of SKUs for sample data:", 5, 20, 10)
            if st.button("Generate Sample Data"):
                with st.spinner("Generating sample data..."):
                    sample_data = SampleDataGenerator.generate_all_sample_data(num_skus)
                    st.session_state.data = sample_data
                    st.success(f"Generated sample data for {num_skus} SKUs")
    
    # File upload section
    if data_source == "Upload CSV Files":
        st.markdown("Upload your CSV files with the required columns:")
        
        uploaded_files = {}
        file_specs = {
            "Forecasts": ["sku_id", "forecast_qty", "forecast_date", "source"],
            "BOMs": ["sku_id", "material_id", "qty_per_unit", "unit"],
            "Inventory": ["material_id", "on_hand_qty", "unit", "open_po_qty", "po_expected_date"],
            "Suppliers": ["material_id", "supplier_id", "cost_per_unit", "lead_time_days", "moq", "reliability_score", "ordering_cost", "holding_cost_rate"]
        }
        
        for file_type, required_cols in file_specs.items():
            st.markdown(f"**{file_type}** (Required columns: {', '.join(required_cols)})")
            uploaded_file = st.file_uploader(f"Upload {file_type} CSV", type="csv", key=file_type)
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    missing_cols = set(required_cols) - set(df.columns)
                    if missing_cols:
                        st.error(f"Missing columns in {file_type}: {missing_cols}")
                    else:
                        uploaded_files[file_type.lower()] = df
                        st.success(f"✅ {file_type} loaded ({len(df)} records)")
                except Exception as e:
                    st.error(f"Error loading {file_type}: {str(e)}")
        
        if len(uploaded_files) == 4:
            st.session_state.data = uploaded_files
    
    # Planning configuration
    st.subheader("2. Planning Configuration")

    # Create tabs for better organization
    basic_tab, advanced_tab = st.tabs(["Basic Settings", "Advanced Features"])

    with basic_tab:
        config_col1, config_col2, config_col3 = st.columns(3)

        with config_col1:
            safety_buffer = st.slider("Safety Buffer (%)", 0, 30, 10) / 100
            max_lead_time = st.slider("Max Lead Time (days)", 7, 60, 30)
            safety_stock_days = st.slider("Safety Stock (days)", 3, 14, 7)

        with config_col2:
            source_weights = {}
            st.markdown("**Forecast Source Weights:**")
            source_weights['sales_order'] = st.slider("Sales Orders", 0.5, 1.0, 1.0)
            source_weights['prod_plan'] = st.slider("Production Plan", 0.5, 1.0, 0.9)
            source_weights['projection'] = st.slider("Projections", 0.3, 1.0, 0.7)

        with config_col3:
            st.markdown("**Risk Thresholds:**")
            high_risk_threshold = st.slider("High Risk Threshold", 0.5, 0.9, 0.7)
            medium_risk_threshold = st.slider("Medium Risk Threshold", 0.7, 1.0, 0.85)

    with advanced_tab:
        st.markdown("### 🔬 EOQ Optimization")
        enable_eoq = st.checkbox("Enable EOQ Optimization", value=True,
                                help="Use Economic Order Quantity calculations for optimal order sizes")

        if enable_eoq:
            col1, col2 = st.columns(2)
            with col1:
                annual_demand_multiplier = st.slider(
                    "Annual Demand Multiplier", 2, 8, 4,
                    help="Multiply quarterly demand by this factor to estimate annual demand"
                )
            with col2:
                st.info("💡 EOQ optimization considers ordering costs, holding costs, and demand patterns to minimize total inventory costs.")
        else:
            annual_demand_multiplier = 4

        st.markdown("### 🤝 Multi-Supplier Sourcing")
        enable_multi_supplier = st.checkbox("Enable Multi-Supplier Sourcing", value=True,
                                          help="Allow sourcing from multiple suppliers for risk mitigation")

        if enable_multi_supplier:
            col1, col2 = st.columns(2)
            with col1:
                max_suppliers = st.slider("Max Suppliers per Material", 1, 5, 3)
                cost_weight = st.slider("Cost Weight", 0.3, 0.8, 0.6,
                                      help="Weight given to cost vs reliability in supplier selection")
            with col2:
                reliability_weight = 1.0 - cost_weight
                st.write(f"**Reliability Weight:** {reliability_weight:.1f}")
                st.info("🤝 Multi-supplier sourcing reduces risk by diversifying supply sources and can provide better pricing.")
        else:
            max_suppliers = 1
            cost_weight = 0.6
            reliability_weight = 0.4

    # Create configuration dictionary manually since PlanningConfig might not support all new fields
    config = {
        'source_weights': source_weights,
        'safety_buffer': safety_buffer,
        'max_lead_time': max_lead_time,
        'safety_stock_days': safety_stock_days,
        'high_risk_threshold': high_risk_threshold,
        'medium_risk_threshold': medium_risk_threshold,
        'enable_eoq_optimization': enable_eoq,
        'enable_multi_supplier': enable_multi_supplier,
        'annual_demand_multiplier': annual_demand_multiplier,
        'max_suppliers_per_material': max_suppliers,
        'cost_weight': cost_weight,
        'reliability_weight': reliability_weight,
        'planning_horizon_days': 90
    }

    # Planning execution
    st.subheader("3. Execute Planning")
    
    if 'data' not in st.session_state:
        st.warning("Please load data first (Step 1)")
        return
    
    if st.button("🚀 Run Raw Material Planning", type="primary"):
        run_planning(st.session_state.data, config)
    
    # Display results
    if 'planning_results' in st.session_state:
        display_planning_results()


def run_planning(data, config):
    """Execute the planning process"""
    
    try:
        with st.spinner("🧠 AI Planning in Progress..."):
            
            # Initialize planner
            planner = RawMaterialPlanner(config)
            
            # Convert data to model objects
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Converting forecast data...")
            forecasts = ForecastProcessor.from_dataframe(data['forecasts'])
            progress_bar.progress(20)
            
            status_text.text("Processing BOM data...")
            boms = BOMExploder.from_dataframe(data['boms'])
            progress_bar.progress(40)
            
            status_text.text("Loading inventory data...")
            inventories = InventoryNetter.from_dataframe(data['inventory'])
            progress_bar.progress(60)
            
            status_text.text("Processing supplier data...")
            suppliers = SupplierSelector.from_dataframe(data['suppliers'])
            progress_bar.progress(80)
            
            status_text.text("Executing AI planning logic...")
            
            # Validate input data
            validation_issues = planner.validate_input_data(forecasts, boms, inventories, suppliers)
            if validation_issues:
                st.warning("Data validation issues found:")
                for issue in validation_issues[:5]:  # Show first 5 issues
                    st.write(f"• {issue}")
            
            # Run planning
            recommendations = planner.plan_materials(forecasts, boms, inventories, suppliers)
            progress_bar.progress(100)
            
            # Store results
            st.session_state.planning_results = {
                'recommendations': recommendations,
                'planner': planner,
                'summary': planner.get_planning_summary(),
                'dataframes': planner.export_results_to_dataframes()
            }
            
            status_text.text("✅ Planning completed successfully!")
            st.success(f"Generated {len(recommendations)} procurement recommendations!")
            
    except Exception as e:
        st.error(f"Planning failed: {str(e)}")
        st.exception(e)


def display_planning_results():
    """Display planning results"""

    results = st.session_state.planning_results
    recommendations = results['recommendations']

    st.subheader("4. Planning Results")

    # Enhanced summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    total_cost = sum(rec.total_cost for rec in recommendations)
    avg_lead_time = sum(rec.lead_time_days for rec in recommendations if rec.lead_time_days < 999) / len(recommendations) if recommendations else 0
    high_risk_count = sum(1 for rec in recommendations if rec.risk.value == 'high')

    # EOQ and multi-supplier metrics
    eoq_optimized = sum(1 for rec in recommendations if hasattr(rec, 'eoq_quantity') and rec.eoq_quantity is not None)
    unique_suppliers = len(set(rec.supplier_id for rec in recommendations if rec.supplier_id != "NO_SUPPLIER"))

    col1.metric("Total Materials", len(recommendations))
    col2.metric("Estimated Cost", f"${total_cost:,.0f}")
    col3.metric("Avg Lead Time", f"{avg_lead_time:.1f} days")
    col4.metric("High Risk Items", high_risk_count)
    col5.metric("EOQ Optimized", eoq_optimized)

    # Additional metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    len(set(rec.material_id for rec in recommendations)) - len(recommendations)
    materials_without_suppliers = sum(1 for rec in recommendations if rec.supplier_id == "NO_SUPPLIER")
    avg_order_qty = sum(rec.order_quantity for rec in recommendations) / len(recommendations) if recommendations else 0
    total_materials = len(set(rec.material_id for rec in recommendations))

    col1.metric("Unique Suppliers", unique_suppliers)
    col2.metric("No Supplier", materials_without_suppliers)
    col3.metric("Avg Order Qty", f"{avg_order_qty:,.0f}")
    col4.metric("Total Materials", total_materials)

    # Show multi-supplier info if enabled
    if any(rec.reasoning and "Multi-supplier" in rec.reasoning for rec in recommendations):
        multi_supplier_count = len([rec for rec in recommendations if rec.reasoning and "Multi-supplier" in rec.reasoning])
        col5.metric("Multi-Supplier", multi_supplier_count)

    # Risk distribution chart
    st.subheader("Risk Distribution")
    risk_counts = {}
    for rec in recommendations:
        risk = rec.risk.value
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    if risk_counts:
        fig_risk = px.pie(
            values=list(risk_counts.values()),
            names=list(risk_counts.keys()),
            title="Risk Distribution of Recommendations",
            color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    # Recommendations table
    st.subheader("Procurement Recommendations")
    
    # Convert to DataFrame for display
    rec_df = RecommendationGenerator.to_dataframe(recommendations)
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_filter = st.multiselect("Filter by Risk:", ['low', 'medium', 'high'], default=['low', 'medium', 'high'])
    with col2:
        min_cost = st.number_input("Min Cost:", value=0.0)
    with col3:
        max_lead_time = st.number_input("Max Lead Time:", value=999)
    
    # Apply filters
    filtered_df = rec_df[
        (rec_df['risk_flag'].isin(risk_filter)) &
        (rec_df['total_cost'] >= min_cost) &
        (rec_df['expected_lead_time'] <= max_lead_time)
    ]
    
    # Display table
    st.dataframe(
        filtered_df[['material_id', 'recommended_order_qty', 'supplier_id', 'total_cost', 
                    'expected_lead_time', 'risk_flag', 'reasoning']],
        use_container_width=True
    )
    
    # Cost analysis chart
    st.subheader("Cost Analysis")
    if len(filtered_df) > 0:
        fig_cost = px.bar(
            filtered_df.head(10),
            x='material_id',
            y='total_cost',
            color='risk_flag',
            title="Top 10 Materials by Cost",
            color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
        )
        fig_cost.update_xaxes(tickangle=45)
        st.plotly_chart(fig_cost, use_container_width=True)
    
    # Export options
    st.subheader("Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        csv_buffer = io.StringIO()
        rec_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"beverly_knits_recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Executive summary
        if st.button("📋 Generate Executive Summary"):
            summary = ReportGenerator.generate_executive_summary(results)
            st.text_area("Executive Summary", summary, height=400)


def show_configuration_page():
    """Configuration management page"""
    
    st.header("⚙️ Configuration Management")
    
    st.subheader("Business Rules")
    
    # Material categories
    st.markdown("**Material Categories:**")
    for category, rules in BusinessRules.MATERIAL_CATEGORIES.items():
        with st.expander(f"{category.title()} Materials"):
            st.write(f"Default Safety Buffer: {rules['default_safety_buffer']*100:.0f}%")
            st.write(f"Preferred Lead Time: {rules['preferred_lead_time']} days")
            st.write(f"Critical Materials: {', '.join(rules['critical_materials'])}")
    
    # Supplier tiers
    st.subheader("Supplier Performance Tiers")
    tier_df = pd.DataFrame([
        {
            'Tier': tier.replace('_', ' ').title(),
            'Min Reliability': criteria['min_reliability'],
            'Max Lead Time': f"{criteria['max_lead_time']} days",
            'Critical Material Preferred': criteria['preferred_for_critical']
        }
        for tier, criteria in BusinessRules.SUPPLIER_TIERS.items()
    ])
    st.dataframe(tier_df, use_container_width=True)
    
    # Seasonal factors
    st.subheader("Seasonal Demand Adjustments")
    seasonal_df = pd.DataFrame([
        {
            'Quarter': quarter,
            'Demand Multiplier': f"{factors['demand_multiplier']:.1f}x",
            'Lead Time Buffer': f"{factors['lead_time_buffer']:.1f}x"
        }
        for quarter, factors in BusinessRules.SEASONAL_FACTORS.items()
    ])
    st.dataframe(seasonal_df, use_container_width=True)


def show_analytics_page():
    """Analytics and insights page"""
    
    st.header("📈 Analytics & Insights")
    
    if 'planning_results' not in st.session_state:
        st.warning("No planning results available. Please run planning first.")
        return
    
    results = st.session_state.planning_results
    dataframes = results['dataframes']
    
    # Forecast analysis
    if 'unified_forecasts' in dataframes:
        st.subheader("Forecast Analysis")
        forecast_df = dataframes['unified_forecasts']
        
        fig_forecast = px.bar(
            forecast_df.head(10),
            x='sku_id',
            y='weighted_forecast_qty',
            title="Top 10 SKUs by Forecast Quantity"
        )
        fig_forecast.update_xaxes(tickangle=45)
        st.plotly_chart(fig_forecast, use_container_width=True)
    
    # Material requirements analysis
    if 'material_requirements' in dataframes:
        st.subheader("Material Requirements Analysis")
        req_df = dataframes['material_requirements']
        
        fig_req = px.scatter(
            req_df,
            x='source_count',
            y='total_qty',
            hover_data=['material_id'],
            title="Material Requirements vs Source Complexity"
        )
        st.plotly_chart(fig_req, use_container_width=True)
    
    # Inventory status analysis
    if 'net_requirements' in dataframes:
        st.subheader("Inventory Status Analysis")
        inv_df = dataframes['net_requirements']
        
        status_counts = inv_df['inventory_status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Inventory Status Distribution"
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Supplier analysis
    if 'recommendations' in dataframes:
        st.subheader("Supplier Analysis")
        rec_df = dataframes['recommendations']
        
        supplier_summary = rec_df.groupby('supplier_id').agg({
            'total_cost': 'sum',
            'material_id': 'count',
            'expected_lead_time': 'mean'
        }).reset_index()
        supplier_summary.columns = ['Supplier', 'Total Cost', 'Material Count', 'Avg Lead Time']
        
        fig_supplier = px.scatter(
            supplier_summary,
            x='Avg Lead Time',
            y='Total Cost',
            size='Material Count',
            hover_data=['Supplier'],
            title="Supplier Performance: Cost vs Lead Time"
        )
        st.plotly_chart(fig_supplier, use_container_width=True)


def show_about_page():
    """About page with system information"""
    
    st.header("ℹ️ About Beverly Knits Raw Material Planner")
    
    st.markdown("""
    ## 🧠 AI-Driven Supply Chain Intelligence
    
    The Beverly Knits Raw Material Planner is an intelligent supply chain planning system 
    that uses advanced algorithms to optimize raw material procurement for textile manufacturing.
    
    ### 🎯 Key Features:
    
    - **Intelligent Forecast Processing**: Weights different forecast sources by reliability
    - **BOM Explosion**: Automatically converts finished goods forecasts to material requirements
    - **Inventory Netting**: Considers current stock and open purchase orders
    - **Smart Supplier Selection**: Optimizes based on cost, reliability, and lead time
    - **Risk Assessment**: Identifies high-risk procurement decisions
    - **Configurable Business Rules**: Adapts to your specific business requirements
    
    ### 🔧 Planning Process:
    
    1. **Forecast Unification**: Aggregates forecasts with source weighting
    2. **BOM Explosion**: Translates SKU forecasts to material needs
    3. **Inventory Netting**: Subtracts available and incoming stock
    4. **Procurement Optimization**: Applies safety buffers and MOQ constraints
    5. **Supplier Selection**: Chooses optimal suppliers based on multiple criteria
    6. **Output Generation**: Provides detailed recommendations with reasoning
    
    ### 📊 Data Requirements:
    
    - **Forecasts**: SKU-level demand forecasts from multiple sources
    - **BOMs**: Bill of materials linking SKUs to raw materials
    - **Inventory**: Current stock levels and open purchase orders
    - **Suppliers**: Supplier information including costs, lead times, and reliability
    
    ### 🚀 Getting Started:
    
    1. Load your data (CSV files or use sample data)
    2. Configure planning parameters
    3. Run the AI planning engine
    4. Review recommendations and export results
    
    ---
    
    **Built with**: Python, Streamlit, Pandas, Plotly
    
    **Version**: 1.0.0
    """)


if __name__ == "__main__":
    main()