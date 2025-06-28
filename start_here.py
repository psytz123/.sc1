"""
Beverly Knits Raw Material Planner - Quick Start Guide

This script provides instructions and commands to get started with the system.
"""



def print_banner():
    """Print welcome banner"""
    print("🧶" * 50)
    print("🧶  BEVERLY KNITS - AI RAW MATERIAL PLANNER  🧶")
    print("🧶" * 50)
    print()
    print("Welcome to the intelligent supply chain planning system!")
    print("This system helps optimize raw material procurement for textile manufacturing.")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📋 Checking Dependencies...")
    
    required_packages = [
        'pandas', 'streamlit', 'plotly', 'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies are installed!")
        return True

def show_quick_start():
    """Show quick start instructions"""
    print("\n🚀 QUICK START GUIDE")
    print("=" * 20)
    
    print("\n1. 🧪 TEST THE SYSTEM:")
    print("   python test_planner.py")
    print("   → Runs complete system test with sample data")
    
    print("\n2. 🌐 LAUNCH WEB INTERFACE:")
    print("   streamlit run main.py")
    print("   → Opens interactive dashboard in your browser")
    
    print("\n3. 📊 USE SAMPLE DATA:")
    print("   → Sample CSV files are available in the 'data/' directory")
    print("   → Or generate new sample data using the web interface")
    
    print("\n4. 📁 UPLOAD YOUR DATA:")
    print("   → Use the web interface to upload your CSV files")
    print("   → Required files: forecasts, boms, inventory, suppliers")

def show_data_format():
    """Show required data format"""
    print("\n📋 DATA FORMAT REQUIREMENTS")
    print("=" * 28)
    
    formats = {
        "Forecasts CSV": ["sku_id", "forecast_qty", "forecast_date", "source"],
        "BOMs CSV": ["sku_id", "material_id", "qty_per_unit", "unit"],
        "Inventory CSV": ["material_id", "on_hand_qty", "unit", "open_po_qty", "po_expected_date"],
        "Suppliers CSV": ["material_id", "supplier_id", "cost_per_unit", "lead_time_days", "moq", "reliability_score"]
    }
    
    for file_type, columns in formats.items():
        print(f"\n📄 {file_type}:")
        for col in columns:
            print(f"   • {col}")

def show_features():
    """Show key features"""
    print("\n🎯 KEY FEATURES")
    print("=" * 15)
    
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
        print(f"  {feature}")

def show_example_output():
    """Show example output"""
    print("\n📊 EXAMPLE OUTPUT")
    print("=" * 17)
    
    print("""
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
        print("\n❌ Please install missing dependencies first!")
        print("   Run: pip install -r requirements.txt")
        return
    
    # Show guides
    show_quick_start()
    show_data_format()
    show_features()
    show_example_output()
    
    print("\n" + "🧶" * 50)
    print("🧶  READY TO START PLANNING! 🚀")
    print("🧶" * 50)
    print()
    print("Choose your next step:")
    print("  • Run 'python test_planner.py' to test the system")
    print("  • Run 'streamlit run main.py' to launch the web interface")
    print("  • Check the README.md for detailed documentation")
    print()

if __name__ == "__main__":
    main()