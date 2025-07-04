"""
Finished Goods Forecast Data Model
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class FinishedGoodsForecast:
    """Represents a finished goods forecast entry"""
    sku_id: str
    forecast_qty: int
    forecast_date: date
    source: str  # "sales_order", "projection", "prod_plan", "sales_history", "manual", "order"
    unit: str = "yards"  # Default unit
    confidence: float = 1.0  # Confidence level (0-1)
    notes: str = ""  # Additional notes

    # Support both sku and sku_id parameter names
    def __init__(self, sku_id=None, forecast_qty=None, forecast_date=None, source=None,
                 unit="yards", confidence=1.0, notes="", sku=None, quantity=None):
        # Handle alternative parameter names
        self.sku_id = sku_id if sku_id is not None else sku
        self.forecast_qty = forecast_qty if forecast_qty is not None else quantity
        self.forecast_date = forecast_date
        self.source = source
        self.unit = unit
        self.confidence = confidence
        self.notes = notes

        # Validate after initialization
        self.__post_init__()

    def __post_init__(self):
        """Validate forecast data"""
        if self.forecast_qty is not None and self.forecast_qty < 0:
            raise ValueError("Forecast quantity cannot be negative")

        valid_sources = ["sales_order", "projection", "prod_plan", "sales_history", "manual", "order", "combined"]
        if self.source and self.source not in valid_sources:
            raise ValueError(f"Source must be one of: {valid_sources}")


class ForecastProcessor:
    """Processes and aggregates forecast data"""

    # Source weights for forecast reliability
    SOURCE_WEIGHTS = {
        "sales_order": 1.0,
        "prod_plan": 0.9,
        "projection": 0.7
    }

    def __init__(self, config=None):
        """Initialize ForecastProcessor with optional config"""
        self.config = config
        if config and hasattr(config, 'forecast_source_weights'):
            self.SOURCE_WEIGHTS = config.forecast_source_weights

    def unify_forecasts(self, forecasts: list[FinishedGoodsForecast]) -> dict[str, float]:
        """
        Unify forecasts by SKU with source weighting
        Returns: {sku_id: weighted_forecast_qty}
        """
        return self.aggregate_forecasts(forecasts)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> list[FinishedGoodsForecast]:
        """Create forecast objects from DataFrame - optimized version"""
        forecasts = []

        # Validate required columns
        required_columns = ['sku_id', 'forecast_qty', 'forecast_date', 'source']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Prepare data with proper types
        df = df.copy()
        df['sku_id'] = df['sku_id'].astype(str)
        df['source'] = df['source'].astype(str)
        df['forecast_qty'] = pd.to_numeric(df['forecast_qty'], errors='coerce').fillna(0).astype(int)
        df['forecast_date'] = pd.to_datetime(df['forecast_date'], errors='coerce')

        # Filter out invalid rows
        invalid_rows = df[df['forecast_date'].isna() | (df['forecast_qty'] < 0)]
        if not invalid_rows.empty:
            logger.warning(f"Filtering out {len(invalid_rows)} invalid forecast rows")
            df = df[~df['forecast_date'].isna() & (df['forecast_qty'] >= 0)]

        # Convert to list of dictionaries for faster iteration
        forecast_data = df.to_dict('records')

        for row in forecast_data:
            try:
                forecast = FinishedGoodsForecast(
                    sku_id=row['sku_id'],
                    forecast_qty=int(row['forecast_qty']),
                    forecast_date=row['forecast_date'].date(),
                    source=row['source']
                )
                forecasts.append(forecast)
            except Exception as e:
                logger.error(f"Error creating forecast from row: {e}")
                continue

        logger.info(f"Successfully created {len(forecasts)} forecasts from {len(df)} rows")
        return forecasts

    def aggregate_forecasts(self, forecasts: list[FinishedGoodsForecast]) -> dict[str, float]:
        """
        Aggregate forecasts by SKU with source weighting
        Returns: {sku_id: weighted_forecast_qty}
        """
        sku_totals = {}

        for forecast in forecasts:
            weight = self.SOURCE_WEIGHTS.get(forecast.source, 0.5)
            weighted_qty = forecast.forecast_qty * weight

            if forecast.sku_id in sku_totals:
                sku_totals[forecast.sku_id] += weighted_qty
            else:
                sku_totals[forecast.sku_id] = weighted_qty

        return sku_totals

    @classmethod
    def get_forecast_summary(cls, forecasts: list[FinishedGoodsForecast]) -> pd.DataFrame:
        """Generate forecast summary for analysis"""
        data = []
        for forecast in forecasts:
            weight = cls.SOURCE_WEIGHTS.get(forecast.source, 0.5)
            data.append({
                'sku_id': forecast.sku_id,
                'forecast_qty': forecast.forecast_qty,
                'source': forecast.source,
                'weight': weight,
                'weighted_qty': forecast.forecast_qty * weight,
                'forecast_date': forecast.forecast_date
            })

        return pd.DataFrame(data)