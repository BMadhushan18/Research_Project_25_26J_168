"""Evaluation script for Smart Logistics models.

Computes metrics (F1, precision, recall for classification; MAE, RMSE for regression)
on a holdout test set.

Usage:
    python scripts/evaluate.py --data data/training_for_model.csv --test-split 0.2 --models-dir models
"""
import argparse
import os
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    f1_score, precision_score, recall_score,
    mean_absolute_error, mean_squared_error
)
import joblib
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_models(models_dir):
    """Load trained models from directory."""
    models = {}
    try:
        models['vectorizer'] = joblib.load(os.path.join(models_dir, 'vectorizer.joblib'))
        models['clf'] = joblib.load(os.path.join(models_dir, 'classifier.joblib'))
        models['mlb_mach'] = joblib.load(os.path.join(models_dir, 'mlb_machinery.joblib'))
        models['reg'] = joblib.load(os.path.join(models_dir, 'regressor_labour.joblib'))
        try:
            models['clf_roles'] = joblib.load(os.path.join(models_dir, 'classifier_roles.joblib'))
            models['mlb_roles'] = joblib.load(os.path.join(models_dir, 'mlb_roles.joblib'))
        except:
            models['clf_roles'] = None
            models['mlb_roles'] = None
        logger.info(f'Loaded models from {models_dir}')
        return models
    except FileNotFoundError as e:
        logger.error(f'Model not found: {e}')
        raise

def evaluate(data_path, test_split=0.2, models_dir='models'):
    """Evaluate models on test set."""
    # Load data
    df = pd.read_csv(data_path)
    logger.info(f'Loaded {len(df)} rows from {data_path}')
    
    # Split train/test
    train_df, test_df = train_test_split(df, test_size=test_split, random_state=42)
    logger.info(f'Train: {len(train_df)} rows, Test: {len(test_df)} rows')
    
    # Load models
    models = load_models(models_dir)
    
    # Vectorize test set
    X_test = models['vectorizer'].transform(test_df['boq_text'].fillna(''))
    
    # Evaluate machinery classifier
    def split_labels(s):
        if pd.isna(s):
            return []
        return [x.strip() for x in str(s).split(';') if x.strip()]
    
    y_mach_true = models['mlb_mach'].transform(test_df['machinery'].apply(split_labels))
    y_mach_pred = models['clf'].predict(X_test)
    
    # Multi-label metrics (averaged)
    f1_mach = f1_score(y_mach_true, y_mach_pred, average='weighted', zero_division=0)
    precision_mach = precision_score(y_mach_true, y_mach_pred, average='weighted', zero_division=0)
    recall_mach = recall_score(y_mach_true, y_mach_pred, average='weighted', zero_division=0)
    
    logger.info(f'\n=== Machinery Classification Metrics ===')
    logger.info(f'  F1 Score (weighted): {f1_mach:.4f}')
    logger.info(f'  Precision (weighted): {precision_mach:.4f}')
    logger.info(f'  Recall (weighted): {recall_mach:.4f}')
    
    # Evaluate labour roles (if available)
    if models['clf_roles'] is not None:
        y_roles_true = models['mlb_roles'].transform(test_df.get('labour_roles', [''] * len(test_df)).apply(split_labels))
        y_roles_pred = models['clf_roles'].predict(X_test)
        
        f1_roles = f1_score(y_roles_true, y_roles_pred, average='weighted', zero_division=0)
        precision_roles = precision_score(y_roles_true, y_roles_pred, average='weighted', zero_division=0)
        recall_roles = recall_score(y_roles_true, y_roles_pred, average='weighted', zero_division=0)
        
        logger.info(f'\n=== Labour Roles Classification Metrics ===')
        logger.info(f'  F1 Score (weighted): {f1_roles:.4f}')
        logger.info(f'  Precision (weighted): {precision_roles:.4f}')
        logger.info(f'  Recall (weighted): {recall_roles:.4f}')
    
    # Evaluate labour regressor
    y_lab_true = test_df[['skilled', 'unskilled']].fillna(0).values
    y_lab_pred = models['reg'].predict(X_test)
    
    mae_skilled = mean_absolute_error(y_lab_true[:, 0], y_lab_pred[:, 0])
    mae_unskilled = mean_absolute_error(y_lab_true[:, 1], y_lab_pred[:, 1])
    rmse_skilled = np.sqrt(mean_squared_error(y_lab_true[:, 0], y_lab_pred[:, 0]))
    rmse_unskilled = np.sqrt(mean_squared_error(y_lab_true[:, 1], y_lab_pred[:, 1]))
    
    logger.info(f'\n=== Labour Count Regression Metrics ===')
    logger.info(f'  Skilled Workers:')
    logger.info(f'    MAE: {mae_skilled:.2f}')
    logger.info(f'    RMSE: {rmse_skilled:.2f}')
    logger.info(f'  Unskilled Workers:')
    logger.info(f'    MAE: {mae_unskilled:.2f}')
    logger.info(f'    RMSE: {rmse_unskilled:.2f}')
    
    # Summary
    logger.info(f'\n=== Summary ===')
    logger.info(f'Test set size: {len(test_df)} samples')
    logger.info(f'Machinery classes: {len(models["mlb_mach"].classes_)}')
    if models['clf_roles'] is not None:
        logger.info(f'Labour role classes: {len(models["mlb_roles"].classes_)}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate trained models on test set')
    parser.add_argument('--data', required=True, help='Path to training CSV')
    parser.add_argument('--test-split', type=float, default=0.2, help='Proportion of data for testing (default: 0.2)')
    parser.add_argument('--models-dir', default='models', help='Directory containing trained models')
    args = parser.parse_args()
    
    evaluate(args.data, test_split=args.test_split, models_dir=args.models_dir)
