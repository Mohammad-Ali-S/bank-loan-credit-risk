"""Train a default-prediction model and score the full dataset."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CLEAN_PATH = os.path.join("data", "processed", "loans_clean.csv")
SCORED_PATH = os.path.join("data", "processed", "loans_scored.csv")
IMPORTANCE_CSV = os.path.join("data", "processed", "feature_importance.csv")
METRICS_PATH = os.path.join("data", "processed", "model_metrics.json")
IMPORTANCE_PNG = os.path.join("dashboard", "feature_importance.png")

# total_payment is excluded: it is only known after the outcome (target leakage).
NUMERIC = ["loan_amount", "funded_amount", "int_rate", "installment", "annual_income", "dti", "term"]
CATEGORICAL = ["grade", "emp_length", "home_ownership", "purpose", "address_state"]


def build_pipeline(model):
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    return Pipeline([("pre", pre), ("model", model)])


def evaluate(pipe, X_test, y_test):
    proba = pipe.predict_proba(X_test)[:, 1]
    preds = pipe.predict(X_test)
    return {
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds),
        "recall": recall_score(y_test, preds),
        "f1": f1_score(y_test, preds),
        "roc_auc": roc_auc_score(y_test, proba),
        "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
        "report": classification_report(y_test, preds),
    }


def feature_importance(pipe):
    ohe = pipe.named_steps["pre"].named_transformers_["cat"]
    names = NUMERIC + list(ohe.get_feature_names_out(CATEGORICAL))
    model = pipe.named_steps["model"]
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
    else:
        values = np.abs(model.coef_[0])
    return pd.DataFrame({"feature": names, "importance": values}).sort_values(
        "importance", ascending=False)


def main():
    df = pd.read_csv(CLEAN_PATH)
    labeled = df.dropna(subset=["is_default"]).copy()
    labeled["is_default"] = labeled["is_default"].astype(int)

    X = labeled[NUMERIC + CATEGORICAL]
    y = labeled["is_default"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Train: {len(X_train)}  Test: {len(X_test)}  Default rate: {y.mean():.3f}")

    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=20,
            class_weight="balanced", random_state=42, n_jobs=-1),
    }

    results = {}
    best_name, best_auc = None, -1.0
    for name, model in candidates.items():
        pipe = build_pipeline(model).fit(X_train, y_train)
        m = evaluate(pipe, X_test, y_test)
        print(f"\n=== {name} ===")
        print(f"Accuracy {m['accuracy']:.3f} | Precision {m['precision']:.3f} | "
              f"Recall {m['recall']:.3f} | F1 {m['f1']:.3f} | ROC-AUC {m['roc_auc']:.3f}")
        print(f"Confusion matrix: {m['confusion_matrix']}")
        print(m.pop("report"))
        results[name] = m
        if m["roc_auc"] > best_auc:
            best_name, best_auc = name, m["roc_auc"]

    print(f"Best model: {best_name} (ROC-AUC={best_auc:.3f})")

    final = build_pipeline(candidates[best_name]).fit(X, y)
    df["predicted_risk_score"] = final.predict_proba(df[NUMERIC + CATEGORICAL])[:, 1].round(4)
    df["predicted_label"] = final.predict(df[NUMERIC + CATEGORICAL])
    df["predicted_risk_band"] = pd.cut(
        df["predicted_risk_score"], bins=[0, 0.25, 0.5, 0.75, 1.0],
        labels=["Low", "Medium", "High", "Very High"], include_lowest=True)
    df.to_csv(SCORED_PATH, index=False)
    print(f"Wrote {SCORED_PATH}")

    imp = feature_importance(final)
    imp.to_csv(IMPORTANCE_CSV, index=False)
    top = imp.head(15).iloc[::-1]
    os.makedirs(os.path.dirname(IMPORTANCE_PNG), exist_ok=True)
    plt.figure(figsize=(8, 6))
    plt.barh(top["feature"], top["importance"], color="#2b6cb0")
    plt.title(f"Top 15 Feature Importances ({best_name.replace('_', ' ').title()})")
    plt.tight_layout()
    plt.savefig(IMPORTANCE_PNG, dpi=120)
    print(f"Wrote {IMPORTANCE_CSV} and {IMPORTANCE_PNG}")

    with open(METRICS_PATH, "w") as f:
        json.dump({"best_model": best_name, "models": results}, f, indent=2)
    print(f"Wrote {METRICS_PATH}")


if __name__ == "__main__":
    main()
