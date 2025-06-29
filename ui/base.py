"""
Base UI component for Beverly Knits application
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)


class BaseUIComponent(ABC):
    """Base class for UI components"""
    
    def __init__(self, title: str):
        """
        Initialize base UI component
        
        Args:
            title: Component title
        """
        self.title = title
        self.logger = get_logger(self.__class__.__name__)
        
    @abstractmethod
    def show(self) -> None:
        """Display the UI component"""
        
    def show_error(self, message: str, details: Optional[str] = None) -> None:
        """
        Display error message
        
        Args:
            message: Error message
            details: Optional error details
        """
        st.error(message)
        if details:
            with st.expander("Error Details"):
                st.code(details)
        self.logger.error(f"{message}: {details}")
        
    def show_success(self, message: str) -> None:
        """
        Display success message
        
        Args:
            message: Success message
        """
        st.success(message)
        self.logger.info(message)
        
    def show_info(self, message: str) -> None:
        """
        Display info message
        
        Args:
            message: Info message
        """
        st.info(message)
        self.logger.info(message)
        
    def show_warning(self, message: str) -> None:
        """
        Display warning message
        
        Args:
            message: Warning message
        """
        st.warning(message)
        self.logger.warning(message)
        
    def get_session_state(self, key: str, default: Any = None) -> Any:
        """
        Get value from session state
        
        Args:
            key: Session state key
            default: Default value if key not found
            
        Returns:
            Value from session state
        """
        return st.session_state.get(key, default)
        
    def set_session_state(self, key: str, value: Any) -> None:
        """
        Set value in session state
        
        Args:
            key: Session state key
            value: Value to store
        """
        st.session_state[key] = value
        
    def clear_session_state(self, key: str) -> None:
        """
        Clear value from session state
        
        Args:
            key: Session state key
        """
        if key in st.session_state:
            del st.session_state[key]