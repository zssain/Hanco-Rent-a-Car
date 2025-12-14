"""
Train a real pricing model using Saudi car rental dataset and export to ONNX.

This script replaces the dummy ONNX model with a trained GradientBoostingRegressor
while maintaining exact compatibility with the existing pricing engine interfaces.

Run training:
    python app/ml/training/train_pricing_model.py

Requirements:
    - Dataset at: app/ml/data/saudi_car_rental_synthetic.csv
    - Output: app/ml/models/model.onnx (overwrites dummy model)
"""

import os
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import onnx
import onnxruntime as ort
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


# Feature order MUST match onnx_runtime.py exactly
FEATURE_ORDER = [
    "rental_length_days",
    "day_of_week",
    "month",
    "base_daily_rate",
    "avg_temp",
    "rain",
    "wind",
    "avg_competitor_price",
    "demand_index",
    "bias",
]

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_PATH = SCRIPT_DIR.parent / "data" / "saudi_car_rental_synthetic.csv"
MODEL_OUTPUT_PATH = SCRIPT_DIR.parent / "models" / "model.onnx"


def load_and_preprocess_data(csv_path: Path) -> pd.DataFrame:
    """
    Load dataset and preprocess to ensure all required features exist.
    
    Args:
        csv_path: Path to saudi_car_rental_synthetic.csv
        
    Returns:
        DataFrame with all features and daily_price target
    """
    print(f"📂 Loading dataset from: {csv_path}")
    
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}\n"
            f"Please place saudi_car_rental_synthetic.csv in app/ml/data/"
        )
    
    df = pd.read_csv(csv_path)
    print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns)}")
    
    # ========== DERIVE TARGET: daily_price ==========
    if 'daily_price' in df.columns:
        print("   ✓ Found 'daily_price' column")
    elif 'final_daily_price' in df.columns:
        print("   ✓ Found 'final_daily_price' column (renaming to 'daily_price')")
        df['daily_price'] = df['final_daily_price']
    elif 'total_price' in df.columns and 'rental_length_days' in df.columns:
        print("   Converting total_price → daily_price")
        # Guard against division by zero
        df['rental_length_days'] = df['rental_length_days'].replace(0, 1)
        df['daily_price'] = df['total_price'] / df['rental_length_days']
    else:
        raise ValueError(
            "Dataset must have either 'daily_price', 'final_daily_price', or both 'total_price' and 'rental_length_days'"
        )
    
    # ========== ENSURE ALL 10 FEATURES EXIST ==========
    required_features = FEATURE_ORDER.copy()
    
    # bias is always 1.0
    if 'bias' not in df.columns:
        print("   Adding bias column (constant 1.0)")
        df['bias'] = 1.0
    
    # Check for missing features
    missing = [f for f in required_features if f not in df.columns]
    if missing:
        print(f"   ⚠️  Missing features: {missing}")
        print("   Filling with defaults...")
        
        # Default values for missing features
        defaults = {
            'rental_length_days': 3.0,
            'day_of_week': 3.0,  # Wednesday
            'month': 6.0,  # June
            'base_daily_rate': 150.0,
            'avg_temp': 25.0,
            'rain': 0.0,
            'wind': 10.0,
            'avg_competitor_price': 100.0,
            'demand_index': 0.5,
        }
        
        for feat in missing:
            if feat in defaults:
                df[feat] = defaults[feat]
            else:
                df[feat] = 0.0
    
    # ========== HANDLE MISSING VALUES ==========
    print("\n🧹 Handling missing values...")
    for col in required_features + ['daily_price']:
        if df[col].isnull().sum() > 0:
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            print(f"   Filled {col} with median: {median_val:.2f}")
    
    # ========== VALIDATE DATA QUALITY ==========
    print("\n✅ Data validation:")
    print(f"   rental_length_days range: {df['rental_length_days'].min():.0f} - {df['rental_length_days'].max():.0f}")
    print(f"   base_daily_rate range: {df['base_daily_rate'].min():.0f} - {df['base_daily_rate'].max():.0f}")
    print(f"   daily_price range: {df['daily_price'].min():.0f} - {df['daily_price'].max():.0f}")
    print(f"   avg_temp range: {df['avg_temp'].min():.1f} - {df['avg_temp'].max():.1f}")
    print(f"   demand_index range: {df['demand_index'].min():.2f} - {df['demand_index'].max():.2f}")
    
    return df


def build_train_test_split(df: pd.DataFrame, test_size=0.2, random_state=42):
    """
    Build X, y and split into train/test sets.
    
    Args:
        df: Preprocessed DataFrame
        test_size: Fraction for test set
        random_state: Random seed for reproducibility
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    print(f"\n📊 Building feature matrix with {len(FEATURE_ORDER)} features...")
    
    # Construct X using exact feature order
    X = df[FEATURE_ORDER].copy()
    y = df['daily_price'].copy()
    
    print(f"   X shape: {X.shape}")
    print(f"   y shape: {y.shape}")
    print(f"   Features in order: {FEATURE_ORDER}")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    print(f"\n   Train set: {len(X_train)} samples")
    print(f"   Test set:  {len(X_test)} samples")
    
    return X_train, X_test, y_train, y_test


def train_model(X_train: pd.DataFrame, y_train: pd.Series):
    """
    Train GradientBoostingRegressor on training data.
    
    Args:
        X_train: Training features
        y_train: Training target
        
    Returns:
        Trained model
    """
    print("\n🤖 Training GradientBoostingRegressor...")
    
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=5,
        min_samples_leaf=2,
        subsample=0.8,
        random_state=42,
        verbose=0
    )
    
    print("   Hyperparameters:")
    print(f"     n_estimators: {model.n_estimators}")
    print(f"     learning_rate: {model.learning_rate}")
    print(f"     max_depth: {model.max_depth}")
    print(f"     subsample: {model.subsample}")
    
    model.fit(X_train, y_train)
    print("   ✓ Training complete")
    
    # Feature importances
    print("\n   Feature Importances:")
    importances = sorted(
        zip(FEATURE_ORDER, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True
    )
    for feat, imp in importances:
        print(f"     {feat:25s}: {imp:.4f}")
    
    return model


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series):
    """
    Evaluate model on test set and print metrics.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test target
    """
    print("\n📈 Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    
    # Compute metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n   Metrics:")
    print(f"     MAE:  {mae:.2f} SAR")
    print(f"     RMSE: {rmse:.2f} SAR")
    print(f"     R²:   {r2:.4f}")
    
    # Show example predictions
    print(f"\n   Example predictions (first 10 rows):")
    print(f"   {'True Price':>12s} | {'Predicted':>12s} | {'Error':>10s}")
    print(f"   {'-'*12}-+-{'-'*12}-+-{'-'*10}")
    
    for i in range(min(10, len(y_test))):
        true_val = y_test.iloc[i]
        pred_val = y_pred[i]
        error = pred_val - true_val
        print(f"   {true_val:12.2f} | {pred_val:12.2f} | {error:+10.2f}")
    
    return y_pred


def export_to_onnx(model, output_path: Path):
    """
    Convert sklearn model to ONNX format.
    
    Args:
        model: Trained sklearn model
        output_path: Path to save model.onnx
    """
    print(f"\n💾 Exporting model to ONNX format...")
    print(f"   Output: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define input type: FloatTensor [None, 10]
    initial_type = [("features", FloatTensorType([None, 10]))]
    
    # Convert to ONNX
    onnx_model = convert_sklearn(
        model,
        initial_types=initial_type,
        target_opset=12  # Compatible opset version
    )
    
    # Save ONNX model
    onnx.save_model(onnx_model, str(output_path))
    
    print(f"   ✓ ONNX model saved ({output_path.stat().st_size / 1024:.1f} KB)")
    
    # Validate ONNX model structure
    onnx_model_check = onnx.load(str(output_path))
    onnx.checker.check_model(onnx_model_check)
    print("   ✓ ONNX model structure validated")


def validate_onnx_model(onnx_path: Path, sklearn_model, X_test: pd.DataFrame):
    """
    Validate ONNX model produces same results as sklearn model.
    
    Args:
        onnx_path: Path to ONNX model
        sklearn_model: Original sklearn model
        X_test: Test features
    """
    print("\n🔍 Validating ONNX model compatibility...")
    
    # Load ONNX model
    sess = ort.InferenceSession(str(onnx_path))
    
    # Get test batch (first 5 rows)
    test_batch = X_test.head(5).values.astype(np.float32)
    
    # Sklearn predictions
    sklearn_preds = sklearn_model.predict(test_batch)
    
    # ONNX predictions
    input_name = sess.get_inputs()[0].name
    onnx_preds = sess.run(None, {input_name: test_batch})[0].flatten()
    
    # Compare
    print(f"\n   Comparison (sklearn vs ONNX):")
    print(f"   {'sklearn':>12s} | {'ONNX':>12s} | {'Diff':>10s}")
    print(f"   {'-'*12}-+-{'-'*12}-+-{'-'*10}")
    
    max_diff = 0.0
    for i in range(len(sklearn_preds)):
        sk_val = sklearn_preds[i]
        onnx_val = onnx_preds[i]
        diff = abs(onnx_val - sk_val)
        max_diff = max(max_diff, diff)
        print(f"   {sk_val:12.2f} | {onnx_val:12.2f} | {diff:10.4f}")
    
    print(f"\n   Maximum difference: {max_diff:.6f}")
    
    if max_diff < 0.01:
        print("   ✅ ONNX model is numerically identical to sklearn model")
    elif max_diff < 1.0:
        print("   ✓ ONNX model is very close to sklearn model (acceptable)")
    else:
        print("   ⚠️  Warning: ONNX model differs significantly from sklearn model")
    
    return max_diff < 1.0


def main():
    """
    Main training pipeline.
    """
    print("=" * 70)
    print("🚀 HANCO AI - Pricing Model Training Pipeline")
    print("=" * 70)
    
    try:
        # Step 1: Load and preprocess data
        df = load_and_preprocess_data(DATA_PATH)
        
        # Step 2: Build train/test split
        X_train, X_test, y_train, y_test = build_train_test_split(df)
        
        # Step 3: Train model
        model = train_model(X_train, y_train)
        
        # Step 4: Evaluate model
        evaluate_model(model, X_test, y_test)
        
        # Step 5: Export to ONNX
        export_to_onnx(model, MODEL_OUTPUT_PATH)
        
        # Step 6: Validate ONNX model
        is_valid = validate_onnx_model(MODEL_OUTPUT_PATH, model, X_test)
        
        print("\n" + "=" * 70)
        if is_valid:
            print("✅ SUCCESS: Training complete!")
            print(f"   Trained ONNX model saved to: {MODEL_OUTPUT_PATH}")
            print(f"\n   The pricing API will now use the trained model automatically.")
            print(f"   No code changes needed - restart the server to use new model:")
            print(f"   python -m app.main")
        else:
            print("⚠️  WARNING: ONNX validation failed")
            print("   Model was saved but may not produce correct results")
        print("=" * 70)
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\n   Please ensure:")
        print(f"   1. Dataset exists at: {DATA_PATH}")
        print(f"   2. File is named: saudi_car_rental_synthetic.csv")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
