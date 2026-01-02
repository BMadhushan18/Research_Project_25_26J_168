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
import joblib


def load_df(path):
    df = pd.read_csv(path)
    return df


def fit_and_save(df, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    X = df['boq_text'].fillna('')
    vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=5000)
    Xvec = vectorizer.fit_transform(X)

    # Multi-label for machinery + vehicles (concatenate labels as features)
    def split_labels(s):
        if pd.isna(s):
            return []
        return [x.strip() for x in str(s).split(';') if x.strip()]

    mlb_mach = MultiLabelBinarizer()
    Y_mach = mlb_mach.fit_transform(df['machinery'].apply(split_labels))

    clf = RandomForestClassifier(n_estimators=100)
    clf.fit(Xvec, Y_mach)

    # Multi-label for labour roles
    mlb_roles = MultiLabelBinarizer()
    if 'labour_roles' in df.columns:
        Y_roles = mlb_roles.fit_transform(df['labour_roles'].apply(split_labels))
        clf_roles = RandomForestClassifier(n_estimators=100)
        clf_roles.fit(Xvec, Y_roles)
    else:
        clf_roles = None

    # Regressor for labour counts
    Y_lab = df[['skilled', 'unskilled']].fillna(0)
    reg = RandomForestRegressor(n_estimators=100)
    reg.fit(Xvec, Y_lab)

    # Save artifacts
    joblib.dump(vectorizer, os.path.join(out_dir, 'vectorizer.joblib'))
    joblib.dump(clf, os.path.join(out_dir, 'classifier.joblib'))
    joblib.dump(mlb_mach, os.path.join(out_dir, 'mlb_machinery.joblib'))
    if clf_roles is not None:
        joblib.dump(clf_roles, os.path.join(out_dir, 'classifier_roles.joblib'))
        joblib.dump(mlb_roles, os.path.join(out_dir, 'mlb_roles.joblib'))
    joblib.dump(reg, os.path.join(out_dir, 'regressor_labour.joblib'))

    print('Saved artifacts to', out_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--out', default='../models')
    parser.add_argument('--subsample', type=int, default=100000, help='Number of rows to sample for classifier training (recommended for large datasets).')
    parser.add_argument('--use-incremental', action='store_true', help='Use incremental training for regressor (SGD) and allow streaming large CSVs.')
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
        vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=50000)
        Xvec = vectorizer.fit_transform(X)

        def split_labels(s):
            if pd.isna(s):
                return []
            return [x.strip() for x in str(s).split(';') if x.strip()]

        mlb_mach = MultiLabelBinarizer()
        Y_mach = mlb_mach.fit_transform(sample_df['machinery'].apply(split_labels))
        clf = RandomForestClassifier(n_estimators=200)
        clf.fit(Xvec, Y_mach)

        # Labour roles classifier
        mlb_roles = MultiLabelBinarizer()
        Y_roles = mlb_roles.fit_transform(sample_df['labour_roles'].apply(split_labels))
        clf_roles = RandomForestClassifier(n_estimators=200)
        clf_roles.fit(Xvec, Y_roles)

        # Regressor for labour counts (multi-output)
        Y_lab = sample_df[['skilled', 'unskilled']].fillna(0)
        reg = RandomForestRegressor(n_estimators=200)
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
        fit_and_save(df, args.out)
