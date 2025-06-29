"""
Beverly Knits Raw Material Planner - Streamlit Application

AI-driven raw material planning system with interactive web interface.
"""

import os
import sys

import streamlit as st

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.secure_config import secure_config
from config.settings import PlanningConfig
from engine.planner import RawMaterialPlanner
from ui.about import AboutPage
from ui.analytics import AnalyticsPage
from ui.configuration import ConfigurationPage
from ui.dashboard import PlanningDashboard
from utils.logger import get_logger

logger = get_logger(__name__)


class BeverlyKnitsApp:
    """Main application class for Beverly Knits Raw Material Planner"""
    
    def __init__(self):
        """Initialize the application"""
        self.config = self._load_configuration()
        self.planner = RawMaterialPlanner(self.config)
        
        # Initialize UI components
        self.dashboard = PlanningDashboard(self.planner)
        self.config_page = ConfigurationPage(self.config)
        self.analytics_page = AnalyticsPage()
        self.about_page = AboutPage()
        
    def _load_configuration(self) -> PlanningConfig:
        """Load configuration from environment and settings"""
        try:
            config = PlanningConfig()
            
            # Override with environment variables if available
            config.safety_buffer = float(secure_config.get('SAFETY_BUFFER', config.safety_buffer))
            config.max_lead_time_days = int(secure_config.get('MAX_LEAD_TIME_DAYS', config.max_lead_time_days))
            config.safety_stock_days = int(secure_config.get('SAFETY_STOCK_DAYS', config.safety_stock_days))
            
            logger.info("Configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return PlanningConfig()  # Return default config
            
    def run(self):
        """Run the Streamlit application"""
        st.set_page_config(
            page_title="Beverly Knits - Raw Material Planner",
            page_icon="🧶",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Header
        st.title("🧶 Beverly Knits - AI Raw Material Planner")
        st.markdown("*Intelligent supply chain planning for textile manufacturing*")
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox(
            "Choose a page:",
            ["📊 Planning Dashboard", "⚙️ Configuration", "📈 Analytics", "ℹ️ About"]
        )
        
        # Route to appropriate page
        if page == "📊 Planning Dashboard":
            self.dashboard.show()
        elif page == "⚙️ Configuration":
            self.config_page.show()
        elif page == "📈 Analytics":
            self.analytics_page.show()
        else:
            self.about_page.show()
            
        # Footer
        st.sidebar.markdown("---")
        st.sidebar.markdown("© 2024 Beverly Knits")
        st.sidebar.markdown("Version 2.0")


def main():
    """Main entry point"""
    try:
        app = BeverlyKnitsApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check the logs for more details.")


if __name__ == "__main__":
    main()