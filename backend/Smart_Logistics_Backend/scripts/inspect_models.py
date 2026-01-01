"""Small utility to load trained artifacts and print a short summary.
Usage: python scripts/inspect_models.py
"""
import os
import joblib

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))

def load(path):
    try:
        return joblib.load(path)
    except Exception as e:
        print('Failed to load', path, '->', e)
        return None

def main():
    print('Models directory:', MODELS_DIR)
    files = ['vectorizer.joblib', 'classifier.joblib', 'mlb_machinery.joblib', 'regressor_labour.joblib']
    for f in files:
        p = os.path.join(MODELS_DIR, f)
        if os.path.exists(p):
            obj = load(p)
            print('\nLoaded:', f)
            if hasattr(obj, 'classes_'):
                print(' - classes:', getattr(obj, 'classes_', 'N/A'))
            if hasattr(obj, 'get_params'):
                print(' - params keys:', list(obj.get_params().keys())[:10])
            try:
                import numpy as np
                if hasattr(obj, 'shape'):
                    print(' - shape:', obj.shape)
            except Exception:
                pass
        else:
            print('\nMissing artifact:', f)

if __name__ == '__main__':
    main()
