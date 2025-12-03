"""
ML Model Training Pipeline
Phase 3C: Train delay prediction models from historical data

Run this script periodically to retrain models with latest data:
    python scripts/train_models.py --lines U1,U2,U3,U4,U6 --days 90
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.database import db
from frontend.mcp_server.historical_data import get_historical_collector
from frontend.mcp_server.prediction_service import ML_AVAILABLE, get_prediction_service

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def train_all_models(lines: List[str], days: int = 90):
    """Train models for specified lines.

    Args:
        lines: List of line names to train
        days: Days of historical data to use
    """
    if not ML_AVAILABLE:
        logger.error("ML libraries not installed. Install: pip install scikit-learn numpy pandas")
        return False

    logger.info(f"Starting model training for {len(lines)} lines using {days} days of data")

    # Initialize services
    collector = get_historical_collector(db)
    predictor = get_prediction_service()

    trained_count = 0
    failed_count = 0

    for line in lines:
        logger.info(f"Training model for {line}...")

        try:
            # Get historical data
            historical_data = collector.get_delay_history(line=line, days=days)

            if not historical_data:
                logger.warning(f"No historical data for {line}")
                failed_count += 1
                continue

            logger.info(f"Retrieved {len(historical_data)} records for {line}")

            # Train model
            success = predictor.train_model(line, historical_data, model_type="random_forest")

            if success:
                trained_count += 1
                logger.info(f"✅ Successfully trained model for {line}")
            else:
                failed_count += 1
                logger.warning(f"❌ Failed to train model for {line}")

        except Exception as e:
            logger.error(f"Error training {line}: {e}", exc_info=True)
            failed_count += 1

    logger.info(f"\nTraining complete: {trained_count} success, {failed_count} failed")
    return trained_count > 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train delay prediction models")
    parser.add_argument(
        "--lines",
        type=str,
        help="Comma-separated line names (e.g., U1,U2,U3)",
        default="U1,U2,U3,U4,U6",
    )
    parser.add_argument("--days", type=int, help="Days of historical data to use", default=90)
    parser.add_argument("--all", action="store_true", help="Train for all available lines")

    args = parser.parse_args()

    # Get lines to train
    if args.all:
        # Get all lines from database
        try:
            results = db.execute_query(
                "SELECT DISTINCT line FROM historical_vehicles ORDER BY line"
            )
            lines = [row["line"] for row in results]
            logger.info(f"Found {len(lines)} lines in historical data")
        except:
            logger.error("Failed to get lines from database")
            return 1
    else:
        lines = [line.strip() for line in args.lines.split(",")]

    # Train models
    success = train_all_models(lines, args.days)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
