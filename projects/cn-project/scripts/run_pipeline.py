import sys
from pathlib import Path
# Ensure project package root is on sys.path so local modules can be imported when
# this script is executed from a different working directory.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_generation import generate_dataset
from data_preprocessing import load_and_preprocess
from anomaly_detection import train_isolation_forest, train_random_forest, load_models, predict_with_models
from output_reporting import plot_confusion, plot_feature_importance, plot_roc
import pandas as pd


def main():
    print('--- Generating dataset (1000 rows for quick run) ---')
    df = generate_dataset(n=1000, anomaly_fraction=0.12, save_csv=True)
    print(f'Dataset rows: {len(df)}')

    print('\n--- Preprocessing & split (test_size=0.25) ---')
    # load_and_preprocess returns 7 items when test_size is provided
    res = load_and_preprocess(test_size=0.25)
    if len(res) == 7:
        df, X_train, X_test, y_train, y_test, scaler, le = res
    else:
        df, X_all, y_all = res
        # fallback: treat all as training
        X_train, y_train = X_all, y_all
        X_test, y_test = X_all, y_all

    print('Train size:', len(y_train), 'Test size:', len(y_test))

    print('\n--- Training IsolationForest (unsupervised) ---')
    iso = train_isolation_forest(X_train, contamination=0.12)
    print('IsolationForest saved.')

    print('\n--- Training RandomForest ---')
    rf_res = train_random_forest(X_train, y_train, X_test=X_test, y_test=y_test)
    print('RandomForest metrics:')
    for k in ('acc','auc'):
        print(f'  {k}:', rf_res.get(k))

    print('\n--- Saving plots (if any) ---')
    try:
        cm_path = plot_confusion(rf_res['confusion_matrix'], name='rf_confusion_run.png')
        print('Confusion matrix saved to', cm_path)
    except Exception as e:
        print('Could not plot confusion:', e)

    try:
        fi_path = plot_feature_importance(rf_res['model'], ['Packets_per_sec','Packet_Size','Connection_Duration','Protocol'], name='rf_fi_run.png')
        print('Feature importance saved to', fi_path)
    except Exception as e:
        print('Could not plot feature importance:', e)

    try:
        proba = rf_res['model'].predict_proba(X_test)[:,1]
        roc_path = plot_roc(y_test, proba, name='rf_roc_run.png')
        print('ROC plot saved to', roc_path)
    except Exception as e:
        print('Could not plot ROC:', e)

    print('\n--- Loading models and running a sample prediction ---')
    models = load_models()
    sample_X = X_test[:3]
    preds = predict_with_models(models, sample_X)
    print('Sample preds:', preds)

    print('\n--- Done ---')

if __name__ == '__main__':
    main()
