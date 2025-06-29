"""
Beverly Knits Raw Material Planner - Quick Start Guide

This script provides instructions and commands to get started with the system.
"""



def print_banner():
    """Print welcome banner"""
    logger.info("🧶" * 50)
    logger.info("🧶  BEVERLY KNITS - AI RAW MATERIAL PLANNER  🧶")
    logger.info("🧶" * 50)
    logger.info()
    logger.info("Welcome to the intelligent supply chain planning system!")
    logger.info("This system helps optimize raw material procurement for textile manufacturing.")
    logger.info()

def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("📋 Checking Dependencies...")
    
    required_packages = [
        'pandas', 'streamlit', 'plotly', 'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"  ✅ {package}")
        except ImportError:
            logger.info(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        logger.info("   Run: pip install -r requirements.txt")
        return False
    else:
        logger.info("\n✅ All dependencies are installed!")
        return True

def show_quick_start():
    """Show quick start instructions"""
    logger.info("\n🚀 QUICK START GUIDE")
    logger.info("=" * 20)
    
    logger.info("\n1. 🧪 TEST THE SYSTEM:")
    logger.info("   python test_planner.py")
    logger.info("   → Runs complete system test with sample data")
    
    logger.info("\n2. 🌐 LAUNCH WEB INTERFACE:")
    logger.info("   streamlit run main.py")
    logger.info("   → Opens interactive dashboard in your browser")
    
    logger.info("\n3. 📊 USE SAMPLE DATA:")
    logger.info("   → Sample CSV files are available in the 'data/' directory")
    logger.info("   → Or generate new sample data using the web interface")
    
    logger.info("\n4. 📁 UPLOAD YOUR DATA:")
    logger.info("   → Use the web interface to upload your CSV files")
    logger.info("   → Required files: forecasts, boms, inventory, suppliers")

def show_data_format():
    """Show required data format"""
    logger.info("\n📋 DATA FORMAT REQUIREMENTS")
    logger.info("=" * 28)
    
    formats = {
        "Forecasts CSV": ["sku_id", "forecast_qty", "forecast_date", "source"],
        "BOMs CSV": ["sku_id", "material_id", "qty_per_unit", "unit"],
        "Inventory CSV": ["material_id", "on_hand_qty", "unit", "open_po_qty", "po_expected_date"],
        "Suppliers CSV": ["material_id", "supplier_id", "cost_per_unit", "lead_time_days", "moq", "reliability_score"]
    }
    
    for file_type, columns in formats.items():
        logger.info(f"\n📄 {file_type}:")
        for col in columns:
            logger.info(f"   • {col}")

def show_features():
    """Show key features"""
    logger.info("\n🎯 KEY FEATURES")
    logger.info("=" * 15)
    
    features = [
        "🧠 AI-driven planning with 6-step intelligent process",
        "📊 Multi-source forecast processing with reliability weighting",
        "💥 Automatic BOM explosion and material requirement calculation",
        "📦 Smart inventory netting with open PO consideration",
        "🎯 Optimal supplier selection based on cost/reliability/lead time",
        "🚨 Risk assessment with configurable thresholds",
        "📈 Interactive analytics and visualization",
        "📋 Executive summary and detailed reporting",
        "⚙️ Configurable business rules and parameters",
        "💾 CSV export for ERP integration"
    ]
    
    for feature in features:
        logger.info(f"  {feature}")

def show_example_output():
    """Show example output"""
    logger.info("\n📊 EXAMPLE OUTPUT")
    logger.info("=" * 17)
    
    logger.info("""
Sample Procurement Recommendation:
{
  "material_id": "YARN-COTTON",
  "recommended_order_qty": 2500,
  "supplier_id": "YarnCorp",
  "unit": "lb",
  "expected_lead_time": 14,
  "risk_flag": "low",
  "total_cost": 12500.00,
  "reasoning": "Net need of 2100 lb plus 15% safety buffer; 
               supplier selected based on cost/reliability ratio 
               within 14-day lead time."
}
""")

def main():
    """Main function"""
    print_banner()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        logger.info("\n❌ Please install missing dependencies first!")
        logger.info("   Run: pip install -r requirements.txt")
        return
    
    # Show guides
    show_quick_start()
    show_data_format()
    show_features()
    show_example_output()
    
    logger.info("\n" + "🧶" * 50)
    logger.info("🧶  READY TO START PLANNING! 🚀")
    logger.info("🧶" * 50)
    logger.info()
    logger.info("Choose your next step:")
    logger.info("  • Run 'python test_planner.py' to test the system")
    logger.info("  • Run 'streamlit run main.py' to launch the web interface")
    logger.info("  • Check the README.md for detailed documentation")
    logger.info()

if __name__ == "__main__":
    main()