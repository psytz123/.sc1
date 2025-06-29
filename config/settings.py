"""
Configuration and Business Rules for Beverly Knits Raw Material Planner
"""

from typing import Any, Dict, List


class PlanningConfig:
    """Configuration class for planning parameters"""
    
    # Default source weights for forecast reliability
    DEFAULT_SOURCE_WEIGHTS = {
        'sales_order': 1.0,     # Highest reliability - actual orders
        'prod_plan': 0.9,       # High reliability - production planning
        'projection': 0.7,      # Lower reliability - sales projections
        'sales_history': 0.8    # Historical sales-based forecasts
    }
    
    # Default procurement parameters
    DEFAULT_PROCUREMENT_CONFIG = {
        'safety_buffer': 0.1,           # 10% safety stock buffer
        'max_lead_time': 30,            # Maximum acceptable lead time (days)
        'planning_horizon_days': 90,    # Planning horizon
        'enable_eoq_optimization': True,   # Economic Order Quantity optimization
        'enable_multi_supplier': True      # Multi-supplier sourcing
    }
    
    # Risk assessment thresholds
    DEFAULT_RISK_THRESHOLDS = {
        'high_risk_threshold': 0.7,     # Reliability below this = high risk
        'medium_risk_threshold': 0.85,  # Reliability below this = medium risk
        'critical_lead_time': 21,       # Lead time above this = higher risk
        'large_order_multiplier': 2.0   # Order qty > requirement * this = risk
    }
    
    # Unit conversion factors (from_unit -> to_unit)
    DEFAULT_UNIT_CONVERSIONS = {
        ('kg', 'lb'): 2.20462,
        ('lb', 'kg'): 0.453592,
        ('m', 'yd'): 1.09361,
        ('yd', 'm'): 0.9144,
        ('ton', 'kg'): 1000,
        ('kg', 'ton'): 0.001
    }

    # Sales Integration Settings
    DEFAULT_SALES_FORECAST_CONFIG = {
        'lookback_days': 90,              # Historical period for demand calculation
        'planning_horizon_days': 90,      # Future planning period
        'min_sales_history_days': 30,     # Minimum history required
        'seasonality_enabled': True,      # Apply seasonal adjustments
        'growth_factor': 1.0,             # Default growth multiplier
        'safety_stock_method': 'statistical',  # 'statistical', 'percentage', 'min_max', 'dynamic'
        'confidence_level': 0.95,         # For statistical safety stock
        'aggregation_period': 'weekly',   # 'daily', 'weekly', 'monthly'
        'enable_sales_forecasting': True, # Enable automatic sales-based forecasting
        'use_style_yarn_bom': True,       # Use style-to-yarn BOM explosion
        'style_yarn_bom_file': 'data/cfab_Yarn_Demand_By_Style.csv'
    }

    # Forecast Source Weights (when combining multiple sources)
    FORECAST_SOURCE_WEIGHTS = {
        'sales_history': 0.7,
        'manual_forecast': 0.2,
        'customer_orders': 1.0,  # Confirmed orders always highest weight
        'sales_order': 1.0,
        'prod_plan': 0.9,
        'projection': 0.7
    }

    # Safety Stock Configuration
    SAFETY_STOCK_CONFIG = {
        'method': 'statistical',          # 'percentage', 'statistical', 'min_max', 'dynamic'
        'service_level': 0.95,            # Target service level for statistical method
        'min_safety_percentage': 0.1,     # Minimum 10% safety stock
        'max_safety_percentage': 0.5,     # Maximum 50% safety stock
        'variability_threshold': 0.3,     # CV above this triggers higher safety stock
        'lead_time_factor': True          # Include lead time in safety stock calculation
    }

    # Aggregation Settings
    AGGREGATION_CONFIG = {
        'default_period': 'weekly',       # Default aggregation period
        'available_periods': ['daily', 'weekly', 'monthly', 'quarterly'],
        'forecast_buckets': 'weekly',     # Bucketing for forecasts
        'min_periods_required': 4,        # Minimum periods for reliable statistics
        'outlier_detection': True,        # Enable outlier detection in demand
        'outlier_threshold': 3.0          # Standard deviations for outlier detection
    }
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get complete default configuration"""
        return {
            'source_weights': cls.DEFAULT_SOURCE_WEIGHTS.copy(),
            **cls.DEFAULT_PROCUREMENT_CONFIG,
            **cls.DEFAULT_RISK_THRESHOLDS,
            **cls.DEFAULT_SALES_FORECAST_CONFIG,
            'forecast_source_weights': cls.FORECAST_SOURCE_WEIGHTS.copy(),
            'unit_conversions': cls.DEFAULT_UNIT_CONVERSIONS.copy()
        }
    
    @classmethod
    def create_custom_config(cls, 
                           source_weights: Dict[str, float] = None,
                           safety_buffer: float = None,
                           max_lead_time: int = None,
                           risk_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """Create custom configuration with overrides"""
        
        config = cls.get_default_config()
        
        if source_weights:
            config['source_weights'].update(source_weights)
        
        if safety_buffer is not None:
            config['safety_buffer'] = safety_buffer
        
        if max_lead_time is not None:
            config['max_lead_time'] = max_lead_time
        
        if risk_thresholds:
            config.update(risk_thresholds)
        
        return config
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> list[str]:
        """Validate configuration parameters"""
        issues = []
        
        # Validate source weights
        if 'source_weights' in config:
            for source, weight in config['source_weights'].items():
                if not 0 <= weight <= 1:
                    issues.append(f"Source weight for '{source}' must be between 0 and 1")
        
        # Validate safety buffer
        if 'safety_buffer' in config:
            if not 0 <= config['safety_buffer'] <= 1:
                issues.append("Safety buffer must be between 0 and 1")
        
        # Validate lead time
        if 'max_lead_time' in config:
            if config['max_lead_time'] <= 0:
                issues.append("Max lead time must be positive")
        
        # Validate risk thresholds
        risk_fields = ['high_risk_threshold', 'medium_risk_threshold']
        for field in risk_fields:
            if field in config:
                if not 0 <= config[field] <= 1:
                    issues.append(f"{field} must be between 0 and 1")
        
        return issues

    def __init__(self, custom_config: Dict[str, Any] = None):
        """Initialize configuration with defaults and custom overrides"""
        # Set all default values
        self.forecast_source_weights = self.DEFAULT_SOURCE_WEIGHTS.copy()
        self.forecast_source_weights.update(self.FORECAST_SOURCE_WEIGHTS)

        # Procurement configuration
        self.safety_stock_percentage = self.DEFAULT_PROCUREMENT_CONFIG['safety_buffer']
        self.max_lead_time = self.DEFAULT_PROCUREMENT_CONFIG['max_lead_time']
        self.planning_horizon_days = self.DEFAULT_PROCUREMENT_CONFIG['planning_horizon_days']
        self.enable_eoq_optimization = self.DEFAULT_PROCUREMENT_CONFIG['enable_eoq_optimization']
        self.enable_multi_supplier = self.DEFAULT_PROCUREMENT_CONFIG['enable_multi_supplier']

        # Sales forecast configuration
        self.sales_forecast_config = self.DEFAULT_SALES_FORECAST_CONFIG.copy()
        self.lookback_days = self.sales_forecast_config['lookback_days']
        self.sales_lookback_days = self.sales_forecast_config['lookback_days']
        self.min_sales_history_days = self.sales_forecast_config['min_sales_history_days']
        self.safety_stock_method = self.sales_forecast_config['safety_stock_method']
        self.service_level = self.sales_forecast_config['confidence_level']
        self.aggregation_period = self.sales_forecast_config['aggregation_period']
        self.enable_sales_forecasting = self.sales_forecast_config['enable_sales_forecasting']
        self.use_style_yarn_bom = self.sales_forecast_config['use_style_yarn_bom']
        self.style_yarn_bom_file = self.sales_forecast_config['style_yarn_bom_file']

        # Safety stock configuration
        self.safety_stock_config = self.SAFETY_STOCK_CONFIG.copy()

        # Aggregation configuration
        self.aggregation_config = self.AGGREGATION_CONFIG.copy()

        # Risk thresholds
        self.high_risk_threshold = self.DEFAULT_RISK_THRESHOLDS['high_risk_threshold']
        self.medium_risk_threshold = self.DEFAULT_RISK_THRESHOLDS['medium_risk_threshold']
        self.critical_lead_time = self.DEFAULT_RISK_THRESHOLDS['critical_lead_time']
        self.large_order_multiplier = self.DEFAULT_RISK_THRESHOLDS['large_order_multiplier']

        # Update with any custom config
        if custom_config:
            self._update_from_dict(custom_config)

    def _update_from_dict(self, config_dict: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_forecast_weight(self, source: str) -> float:
        """Get weight for a forecast source"""
        return self.forecast_source_weights.get(source, 0.5)

    def get_safety_stock_method(self) -> str:
        """Get the configured safety stock calculation method"""
        return self.safety_stock_config.get('method', 'percentage')

    def get_service_level(self) -> float:
        """Get the target service level for safety stock"""
        return self.safety_stock_config.get('service_level', 0.95)

    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate configuration settings"""
        errors = []
        warnings = []

        # Validate numeric ranges
        if self.safety_stock_percentage < 0 or self.safety_stock_percentage > 1:
            errors.append("safety_stock_percentage must be between 0 and 1")

        if self.service_level < 0 or self.service_level > 1:
            errors.append("service_level must be between 0 and 1")

        if self.planning_horizon_days < 1:
            errors.append("planning_horizon_days must be positive")

        if self.lookback_days < self.min_sales_history_days:
            warnings.append(f"lookback_days ({self.lookback_days}) is less than min_sales_history_days ({self.min_sales_history_days})")

        # Validate file paths
        import os
        if self.use_style_yarn_bom and not os.path.exists(self.style_yarn_bom_file):
            warnings.append(f"Style-yarn BOM file not found: {self.style_yarn_bom_file}")

        # Validate aggregation period
        if self.aggregation_period not in self.aggregation_config['available_periods']:
            errors.append(f"Invalid aggregation_period: {self.aggregation_period}")

        return {
            'errors': errors,
            'warnings': warnings,
            'valid': len(errors) == 0
        }


class BusinessRules:
    """Business rules and constraints for Beverly Knits"""
    
    # Material categories and their specific rules
    MATERIAL_CATEGORIES = {
        'yarn': {
            'default_safety_buffer': 0.15,  # Higher buffer for yarn
            'preferred_lead_time': 14,
            'critical_materials': ['YARN-COTTON', 'YARN-WOOL']
        },
        'fabric': {
            'default_safety_buffer': 0.10,
            'preferred_lead_time': 21,
            'critical_materials': ['FABRIC-DENIM', 'FABRIC-SILK']
        },
        'accessories': {
            'default_safety_buffer': 0.05,  # Lower buffer for accessories
            'preferred_lead_time': 7,
            'critical_materials': ['BUTTON-METAL', 'ZIPPER-YKK']
        }
    }
    
    # Supplier performance tiers
    SUPPLIER_TIERS = {
        'tier_1': {
            'min_reliability': 0.95,
            'max_lead_time': 14,
            'preferred_for_critical': True
        },
        'tier_2': {
            'min_reliability': 0.85,
            'max_lead_time': 21,
            'preferred_for_critical': False
        },
        'tier_3': {
            'min_reliability': 0.70,
            'max_lead_time': 30,
            'preferred_for_critical': False
        }
    }
    
    # Seasonal adjustments
    SEASONAL_FACTORS = {
        'Q1': {'demand_multiplier': 0.8, 'lead_time_buffer': 1.0},
        'Q2': {'demand_multiplier': 1.1, 'lead_time_buffer': 1.1},
        'Q3': {'demand_multiplier': 1.3, 'lead_time_buffer': 1.2},  # Peak season
        'Q4': {'demand_multiplier': 1.0, 'lead_time_buffer': 1.0}
    }
    
    @classmethod
    def get_material_category(cls, material_id: str) -> str:
        """Determine material category from material ID"""
        material_upper = material_id.upper()
        
        if 'YARN' in material_upper:
            return 'yarn'
        elif 'FABRIC' in material_upper:
            return 'fabric'
        elif any(acc in material_upper for acc in ['BUTTON', 'ZIPPER', 'THREAD']):
            return 'accessories'
        else:
            return 'other'
    
    @classmethod
    def get_category_rules(cls, material_id: str) -> Dict[str, Any]:
        """Get business rules for a material category"""
        category = cls.get_material_category(material_id)
        return cls.MATERIAL_CATEGORIES.get(category, {
            'default_safety_buffer': 0.10,
            'preferred_lead_time': 21,
            'critical_materials': []
        })
    
    @classmethod
    def is_critical_material(cls, material_id: str) -> bool:
        """Check if material is considered critical"""
        category_rules = cls.get_category_rules(material_id)
        return material_id in category_rules.get('critical_materials', [])
    
    @classmethod
    def get_supplier_tier(cls, reliability_score: float, lead_time: int) -> str:
        """Determine supplier tier based on performance"""
        for tier, criteria in cls.SUPPLIER_TIERS.items():
            if (reliability_score >= criteria['min_reliability'] and 
                lead_time <= criteria['max_lead_time']):
                return tier
        return 'tier_3'  # Default to lowest tier
    
    @classmethod
    def apply_seasonal_adjustment(cls, base_quantity: float, quarter: str) -> float:
        """Apply seasonal demand adjustments"""
        factor = cls.SEASONAL_FACTORS.get(quarter, {}).get('demand_multiplier', 1.0)
        return base_quantity * factor