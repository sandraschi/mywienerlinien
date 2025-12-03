"""
ML-based delay prediction service.
Phase 3C Enhancement: Machine learning models for transit delay prediction.

Uses historical data to predict delays and optimize routing decisions.
"""

import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Optional ML dependencies
try:
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    ML_AVAILABLE = True
except ImportError:
    logger.warning("ML libraries not available. Install: pip install scikit-learn numpy")
    ML_AVAILABLE = False
    np = None
    RandomForestRegressor = None
    GradientBoostingRegressor = None
    StandardScaler = None


@dataclass
class DelayPrediction:
    """Prediction of expected delay for a line at a specific time."""

    line: str
    predicted_delay_minutes: float
    confidence: float  # 0-1
    factors: dict[str, float]  # Contributing factors
    timestamp: datetime


@dataclass
class RoutePrediction:
    """Prediction for entire route including all segments."""

    route_id: str
    predicted_total_delay: float
    segment_predictions: list[DelayPrediction]
    reliability_score: float
    recommendation: str  # "recommended", "caution", "avoid"


class DelayPredictionModel:
    """ML model for predicting transit delays."""

    def __init__(self, model_dir: Optional[Path] = None):
        """Initialize prediction model.

        Args:
            model_dir: Directory for model storage
        """
        self.model_dir = model_dir or Path(__file__).parent.parent / "models" / "ml"
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.models: dict[str, any] = {}  # line -> model
        self.scalers: dict[str, any] = {}  # line -> scaler
        self.feature_names = [
            "hour",
            "day_of_week",
            "is_weekend",
            "is_rush_hour",
            "is_early_morning",
            "is_late_night",
            "month",
            "is_holiday",
        ]

        if not ML_AVAILABLE:
            logger.warning("ML libraries not available - predictions will use historical averages")

    def extract_features(self, target_time: datetime, line: str) -> dict[str, float]:
        """Extract features for prediction.

        Args:
            target_time: Time to predict for
            line: Transit line

        Returns:
            Feature dictionary
        """
        hour = target_time.hour
        dow = target_time.weekday()

        features = {
            "hour": hour,
            "day_of_week": dow,
            "is_weekend": 1.0 if dow >= 5 else 0.0,
            "is_rush_hour": 1.0 if (7 <= hour <= 9 or 16 <= hour <= 18) else 0.0,
            "is_early_morning": 1.0 if 5 <= hour <= 7 else 0.0,
            "is_late_night": 1.0 if hour >= 22 or hour <= 1 else 0.0,
            "month": target_time.month,
            "is_holiday": 0.0,  # TODO: Integrate holiday calendar
        }

        return features

    def train_model(
        self, line: str, historical_data: list[dict], model_type: str = "random_forest"
    ) -> bool:
        """Train prediction model for a specific line.

        Args:
            line: Line to train model for
            historical_data: Historical delay records
            model_type: 'random_forest' or 'gradient_boosting'

        Returns:
            True if training successful
        """
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available")
            return False

        if len(historical_data) < 100:
            logger.warning(
                f"Insufficient data for {line}: {len(historical_data)} records (need 100+)"
            )
            return False

        try:
            # Extract features and targets
            X = []
            y = []

            for record in historical_data:
                timestamp = record["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)

                features = self.extract_features(timestamp, line)
                feature_vector = [features[name] for name in self.feature_names]

                X.append(feature_vector)
                y.append(record["delay_minutes"])

            X = np.array(X)
            y = np.array(y)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            if model_type == "gradient_boosting":
                model = GradientBoostingRegressor(
                    n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
                )
            else:  # random_forest
                model = RandomForestRegressor(
                    n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
                )

            model.fit(X_train_scaled, y_train)

            # Evaluate
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)

            logger.info(
                f"Model trained for {line}: R² train={train_score:.3f}, test={test_score:.3f}"
            )

            # Store model and scaler
            self.models[line] = model
            self.scalers[line] = scaler

            # Save to disk
            self._save_model(line, model, scaler)

            return True

        except Exception as e:
            logger.error(f"Error training model for {line}: {e}", exc_info=True)
            return False

    def predict_delay(
        self, line: str, target_time: datetime, use_fallback: bool = True
    ) -> Optional[DelayPrediction]:
        """Predict delay for a line at a specific time.

        Args:
            line: Line to predict for
            target_time: Time to predict for
            use_fallback: Use historical average if model unavailable

        Returns:
            Delay prediction or None
        """
        if not ML_AVAILABLE and not use_fallback:
            return None

        # Try ML prediction first
        if ML_AVAILABLE and line in self.models:
            try:
                return self._predict_ml(line, target_time)
            except Exception as e:
                logger.warning(f"ML prediction failed for {line}: {e}")
                if not use_fallback:
                    return None

        # Fallback to historical average
        if use_fallback:
            return self._predict_historical(line, target_time)

        return None

    def _predict_ml(self, line: str, target_time: datetime) -> DelayPrediction:
        """Make ML-based prediction."""
        model = self.models[line]
        scaler = self.scalers[line]

        # Extract features
        features = self.extract_features(target_time, line)
        feature_vector = np.array([[features[name] for name in self.feature_names]])

        # Scale and predict
        feature_scaled = scaler.transform(feature_vector)
        predicted_delay = model.predict(feature_scaled)[0]

        # Get feature importances (if available)
        try:
            importances = model.feature_importances_
            factors = {name: float(imp) for name, imp in zip(self.feature_names, importances)}
        except:
            factors = {}

        # Estimate confidence based on feature values
        confidence = 0.8  # Base confidence for ML models
        if features["is_rush_hour"]:
            confidence *= 0.9  # Lower confidence during variable rush hour
        if features["is_late_night"]:
            confidence *= 0.85  # Lower confidence for sparse late-night data

        return DelayPrediction(
            line=line,
            predicted_delay_minutes=max(0, predicted_delay),
            confidence=confidence,
            factors=factors,
            timestamp=datetime.now(),
        )

    def _predict_historical(self, line: str, target_time: datetime) -> Optional[DelayPrediction]:
        """Fallback prediction using historical averages."""
        # This would query the delay_patterns table
        # For now, return a simple prediction
        hour = target_time.hour
        dow = target_time.weekday()

        # Simple heuristics
        base_delay = 0.0

        # Rush hour
        if 7 <= hour <= 9 or 16 <= hour <= 18:
            base_delay = 3.0
        # Early morning
        elif 5 <= hour <= 7:
            base_delay = 2.0
        # Late night
        elif hour >= 22 or hour <= 2:
            base_delay = 4.0

        # Weekend adjustment
        if dow >= 5:
            base_delay *= 0.7

        return DelayPrediction(
            line=line,
            predicted_delay_minutes=base_delay,
            confidence=0.6,  # Lower confidence for heuristic
            factors={"method": "historical_average"},
            timestamp=datetime.now(),
        )

    def _save_model(self, line: str, model, scaler):
        """Save model and scaler to disk."""
        try:
            model_file = self.model_dir / f"{line}_model.pkl"
            scaler_file = self.model_dir / f"{line}_scaler.pkl"

            with open(model_file, "wb") as f:
                pickle.dump(model, f)

            with open(scaler_file, "wb") as f:
                pickle.dump(scaler, f)

            logger.info(f"Saved model for {line}")

        except Exception as e:
            logger.error(f"Error saving model: {e}", exc_info=True)

    def load_model(self, line: str) -> bool:
        """Load model and scaler from disk.

        Args:
            line: Line to load model for

        Returns:
            True if loaded successfully
        """
        if not ML_AVAILABLE:
            return False

        try:
            model_file = self.model_dir / f"{line}_model.pkl"
            scaler_file = self.model_dir / f"{line}_scaler.pkl"

            if not model_file.exists() or not scaler_file.exists():
                return False

            with open(model_file, "rb") as f:
                self.models[line] = pickle.load(f)

            with open(scaler_file, "rb") as f:
                self.scalers[line] = pickle.load(f)

            logger.info(f"Loaded model for {line}")
            return True

        except Exception as e:
            logger.error(f"Error loading model for {line}: {e}", exc_info=True)
            return False

    def load_all_models(self) -> int:
        """Load all available models from disk.

        Returns:
            Number of models loaded
        """
        count = 0
        model_files = list(self.model_dir.glob("*_model.pkl"))

        for model_file in model_files:
            line = model_file.stem.replace("_model", "")
            if self.load_model(line):
                count += 1

        logger.info(f"Loaded {count} models from disk")
        return count


# Singleton instance
_prediction_service: Optional[DelayPredictionModel] = None


def get_prediction_service() -> DelayPredictionModel:
    """Get or create prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = DelayPredictionModel()
        if ML_AVAILABLE:
            _prediction_service.load_all_models()
    return _prediction_service
