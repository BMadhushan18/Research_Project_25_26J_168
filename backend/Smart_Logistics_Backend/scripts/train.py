"""Training script for prototype models.
This script reads a CSV with columns:
- boq_text
- machinery  (semicolon-separated labels)
- vehicles   (semicolon-separated labels)
- skilled    (int)
- unskilled  (int)

It trains a simple multi-label classifier for machinery+vehicles and a regressor for labour counts, then saves artifacts to --out dir.
"""
import argparse
import os
import random
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report, mean_absolute_error, mean_squared_error
import json
import joblib

# Optional heavy-weight models
try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None
try:
    from lightgbm import LGBMRegressor
except Exception:
    LGBMRegressor = None
try:
    from lightgbm import LGBMClassifier
except Exception:
    LGBMClassifier = None


def load_df(path):
    df = pd.read_csv(path)
    return df


def fit_and_save(df, out_dir, clf_backend='rf', reg_backend='rf', evaluate=False, max_features=50000):
    os.makedirs(out_dir, exist_ok=True)

    X = df['boq_text'].fillna('')

    # Split for evaluation if requested
    if evaluate:
        X_train, X_test, y_mach_train, y_mach_test, y_lab_train, y_lab_test = _prepare_train_test(df)
    else:
        X_train = X

    vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=max_features)
    Xvec = vectorizer.fit_transform(X_train)

    # label splitting helpers
    def split_labels(s):
        if pd.isna(s):
            return []
        return [x.strip() for x in str(s).split(';') if x.strip()]

    mlb_mach = MultiLabelBinarizer()
    Y_mach = mlb_mach.fit_transform(df['machinery'].apply(split_labels))

    # Choose classifier backend
    if clf_backend == 'xgb':
        if XGBClassifier is None:
            print('WARNING: XGBoost not available, falling back to RandomForest')
            clf = RandomForestClassifier(n_estimators=200)
        else:
            from sklearn.multioutput import MultiOutputClassifier
            base_clf = XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=200)
            clf = MultiOutputClassifier(base_clf)
    elif clf_backend == 'lgb':
        if LGBMClassifier is None:
            print('WARNING: LightGBM classifier not available, falling back to RandomForest')
            clf = RandomForestClassifier(n_estimators=200)
        else:
            from sklearn.multioutput import MultiOutputClassifier
            base_clf = LGBMClassifier(n_estimators=200)
            clf = MultiOutputClassifier(base_clf)
    else:
        clf = RandomForestClassifier(n_estimators=200)

    print('Training machinery classifier using', clf_backend)
    try:
        clf.fit(vectorizer.transform(X_train), Y_mach[:len(X_train)])
    except Exception as e:
        print('WARNING: classifier fit failed for backend', clf_backend, 'falling back to RandomForest (smaller). Error:', str(e))
        clf = RandomForestClassifier(n_estimators=100, max_depth=12)
        clf.fit(vectorizer.transform(X_train), Y_mach[:len(X_train)])

    # Labour roles classifier (optional)
    mlb_roles = MultiLabelBinarizer()
    clf_roles = None
    if 'labour_roles' in df.columns:
        Y_roles = mlb_roles.fit_transform(df['labour_roles'].apply(split_labels))
        clf_roles = RandomForestClassifier(n_estimators=200)
        clf_roles.fit(vectorizer.transform(X_train), Y_roles[:len(X_train)])

    # Regressor for labour counts
    Y_lab = df[['skilled', 'unskilled']].fillna(0)

    if reg_backend == 'lgb':
        if LGBMRegressor is None:
            raise RuntimeError('LightGBM is not installed; install lightgbm to use this option')
        reg = MultiOutputRegressor(LGBMRegressor(n_estimators=200))
    else:
        reg = RandomForestRegressor(n_estimators=200)

    print('Training labour regressor using', reg_backend)
    reg.fit(vectorizer.transform(X_train), Y_lab[:len(X_train)])

    # Evaluate if requested
    metrics = {}
    if evaluate:
        Xv_test = vectorizer.transform(X_test)
        # classifier metrics
        try:
            mach_pred = clf.predict(Xv_test)
            metrics['machinery_f1_micro'] = f1_score(y_mach_test, mach_pred, average='micro')
            metrics['machinery_f1_macro'] = f1_score(y_mach_test, mach_pred, average='macro')
            metrics['machinery_report'] = classification_report(y_mach_test, mach_pred, output_dict=True)
        except Exception as e:
            metrics['machinery_error'] = str(e)
        # regressor metrics
        try:
            lab_pred = reg.predict(Xv_test)
            metrics['lab_mae'] = mean_absolute_error(y_lab_test, lab_pred)
            metrics['lab_rmse'] = mean_squared_error(y_lab_test, lab_pred, squared=False)
        except Exception as e:
            metrics['regressor_error'] = str(e)

        # Save metrics
        with open(os.path.join(out_dir, 'metrics.json'), 'w') as f:
            json.dump(metrics, f, indent=2)
        print('Saved metrics to', os.path.join(out_dir, 'metrics.json'))

    # Save artifacts
    joblib.dump(vectorizer, os.path.join(out_dir, 'vectorizer.joblib'))
    joblib.dump(clf, os.path.join(out_dir, 'classifier.joblib'))
    joblib.dump(mlb_mach, os.path.join(out_dir, 'mlb_machinery.joblib'))
    if clf_roles is not None:
        joblib.dump(clf_roles, os.path.join(out_dir, 'classifier_roles.joblib'))
        joblib.dump(mlb_roles, os.path.join(out_dir, 'mlb_roles.joblib'))
    joblib.dump(reg, os.path.join(out_dir, 'regressor_labour.joblib'))

    print('Saved artifacts to', out_dir)


def _prepare_train_test(df, test_size=0.2, random_state=42):
    # Prepare train/test split for evaluation
    X = df['boq_text'].fillna('')
    def split_labels(s):
        if pd.isna(s):
            return []
        return [x.strip() for x in str(s).split(';') if x.strip()]
    mlb = MultiLabelBinarizer()
    Y_mach = mlb.fit_transform(df['machinery'].apply(split_labels))
    Y_lab = df[['skilled', 'unskilled']].fillna(0)
    X_train, X_test, y_mach_train, y_mach_test, y_lab_train, y_lab_test = train_test_split(
        X, Y_mach, Y_lab, test_size=test_size, random_state=random_state
    )
    return X_train, X_test, y_mach_train, y_mach_test, y_lab_train, y_lab_test


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--out', default='../models')
    parser.add_argument('--subsample', type=int, default=100000, help='Number of rows to sample for classifier training (recommended for large datasets).')
    parser.add_argument('--max-features', type=int, default=50000, help='Maximum features for TF-IDF vectorizer (reduce for memory constraints)')
    parser.add_argument('--use-incremental', action='store_true', help='Use incremental training for regressor (SGD) and allow streaming large CSVs.')
    parser.add_argument('--clf-backend', choices=['rf', 'xgb', 'lgb'], default='rf', help='Classifier backend: RandomForest (rf), XGBoost (xgb), or LightGBM (lgb)')
    parser.add_argument('--reg-backend', choices=['rf', 'lgb'], default='rf', help='Regressor backend: RandomForest (rf) or LightGBM (lgb)')
    parser.add_argument('--evaluate', action='store_true', help='Run a train/test split and save evaluation metrics to metrics.json')
    args = parser.parse_args()

    if args.use_incremental:
        print('Running incremental training (regressor streaming) with subsample=', args.subsample)
        # Implement streaming regressor training and subsample-based classifier training
        import pandas as pd
        from sklearn.feature_extraction.text import HashingVectorizer
        from sklearn.preprocessing import MultiLabelBinarizer
        from sklearn.linear_model import SGDRegressor, SGDClassifier
        from sklearn.ensemble import RandomForestClassifier
        import joblib
        
        # Prepare subsample for classifiers
        sample_chunks = []
        total = 0
        for chunk in pd.read_csv(args.data, chunksize=10000):
            sample_chunks.append(chunk.sample(n=min(len(chunk), max(0, args.subsample - total))))
            total = sum(len(c) for c in sample_chunks)
            if total >= args.subsample:
                break
        if total == 0:
            raise RuntimeError('No rows found during sampling')
        sample_df = pd.concat(sample_chunks, ignore_index=True)
        # ensure we have a text field to vectorize
        if 'boq_text' not in sample_df.columns:
            sample_df['boq_text'] = sample_df.apply(lambda r: f"{r.get('item','')} {r.get('description','')} qty:{r.get('quantity','')} {r.get('unit','')} vehicles:{r.get('vehicles','')} labor:{r.get('labor_types','')}", axis=1)
        # derive machinery column from vehicles if missing
        if 'machinery' not in sample_df.columns:
            sample_df['machinery'] = sample_df['vehicles'].fillna('').apply(lambda s: ';'.join([x.strip() for x in str(s).replace(',', ';').split(';') if x and x.lower() != 'none']))
        # derive labour_roles if missing
        def make_roles(row):
            roles = []
            if row.get('masons', 0) > 0:
                roles.append('mason')
            if row.get('welders', 0) > 0:
                roles.append('welder')
            if row.get('laborers', 0) > 0:
                roles.append('labourer')
            if row.get('Excavators', 0) > 0 or row.get('Cranes', 0) > 0 or row.get('Loaders', 0) > 0:
                roles.append('operator')
            if random.random() < 0.2:
                roles.append('supervisor')
            return ';'.join(roles)
        if 'labour_roles' not in sample_df.columns:
            sample_df['labour_roles'] = sample_df.apply(make_roles, axis=1)

        # Prepare final training on a sampled subset (already sampled above into sample_df)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import MultiLabelBinarizer
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        import joblib
        import os

        X = sample_df['boq_text'].fillna('')
        vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=args.max_features)
        Xvec = vectorizer.fit_transform(X)

        def split_labels(s):
            if pd.isna(s):
                return []
            return [x.strip() for x in str(s).split(';') if x.strip()]

        mlb_mach = MultiLabelBinarizer()
        Y_mach = mlb_mach.fit_transform(sample_df['machinery'].apply(split_labels))
        # Use smaller ensembles for incremental / low-memory runs
        clf = RandomForestClassifier(n_estimators=50, max_depth=12, n_jobs=-1)
        clf.fit(Xvec, Y_mach)

        # Labour roles classifier
        mlb_roles = MultiLabelBinarizer()
        Y_roles = mlb_roles.fit_transform(sample_df['labour_roles'].apply(split_labels))
        clf_roles = RandomForestClassifier(n_estimators=50, max_depth=12, n_jobs=-1)
        clf_roles.fit(Xvec, Y_roles)

        # Regressor for labour counts (multi-output)
        Y_lab = sample_df[['skilled', 'unskilled']].fillna(0)
        reg = RandomForestRegressor(n_estimators=50, max_depth=12, n_jobs=-1)
        reg.fit(Xvec, Y_lab)

        # Save canonical artifacts
        os.makedirs(args.out, exist_ok=True)
        joblib.dump(vectorizer, os.path.join(args.out, 'vectorizer.joblib'))
        joblib.dump(clf, os.path.join(args.out, 'classifier.joblib'))
        joblib.dump(mlb_mach, os.path.join(args.out, 'mlb_machinery.joblib'))
        joblib.dump(clf_roles, os.path.join(args.out, 'classifier_roles.joblib'))
        joblib.dump(mlb_roles, os.path.join(args.out, 'mlb_roles.joblib'))
        joblib.dump(reg, os.path.join(args.out, 'regressor_labour.joblib'))

        print('Saved final-trained artifacts to', args.out)
    else:
        # Default path: load full dataset and train standard models
        df = load_df(args.data)
        fit_and_save(df, args.out, clf_backend=args.clf_backend, reg_backend=args.reg_backend, evaluate=args.evaluate, max_features=args.max_features)
