"""Entrenamiento de modelos: Isolation Forest + Clasificador de ataques."""

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from app.ml.feature_extractor import extract_features, N_FEATURES, FEATURE_NAMES

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"


def train_isolation_forest(
    features: np.ndarray,
    contamination: float = 0.1,
    n_estimators: int = 100,
    model_name: str = "isolation_forest.pkl",
) -> IsolationForest:
    """Entrena un modelo Isolation Forest y lo serializa."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(features)

    model_path = MODELS_DIR / model_name
    joblib.dump(model, model_path)
    logger.info(f"Isolation Forest guardado en {model_path}")

    return model


def train_attack_classifier(
    features: np.ndarray,
    labels: np.ndarray,
    n_estimators: int = 200,
) -> dict:
    """Entrena un clasificador Random Forest para tipos de ataque.

    Args:
        features: Array de features (N, N_FEATURES)
        labels: Array de strings con tipo de ataque
        n_estimators: Número de árboles

    Returns:
        dict con métricas de entrenamiento
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(labels)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        features, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # Train
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = float((y_pred == y_test).mean())
    report = classification_report(
        y_test, y_pred,
        labels=range(len(le.classes_)),
        target_names=le.classes_,
        output_dict=True,
        zero_division=0,
    )

    # Feature importance
    importances = dict(zip(FEATURE_NAMES, clf.feature_importances_))
    top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]

    # Save
    joblib.dump(clf, MODELS_DIR / "attack_classifier.pkl")
    joblib.dump(le, MODELS_DIR / "label_encoder.pkl")
    logger.info(f"Clasificador guardado. Accuracy: {accuracy:.2%}")

    return {
        "accuracy": accuracy,
        "classes": list(le.classes_),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "report": report,
        "top_features": top_features,
    }


def train_from_events(events: list[dict]) -> dict:
    """Entrena ambos modelos a partir de una lista de eventos parseados.

    Cada evento debe tener los campos estándar (event_type, severity_score, etc.)
    y opcionalmente un campo 'label' para el clasificador.

    Returns:
        dict con métricas de ambos modelos
    """
    if len(events) < 10:
        raise ValueError(f"Muy pocos eventos para entrenar: {len(events)}")

    # Extraer features
    all_features = []
    labels = []
    for ev in events:
        feat = extract_features(ev)
        all_features.append(feat)
        labels.append(ev.get("label", _infer_label(ev)))

    X = np.array(all_features)
    y = np.array(labels)

    results = {}

    # 1. Isolation Forest (no supervisado, usa todos los datos)
    logger.info(f"Entrenando Isolation Forest con {len(X)} eventos...")
    anomaly_ratio = max(0.01, min(0.3, (y != "normal").mean()))
    iso_model = train_isolation_forest(X, contamination=anomaly_ratio)
    predictions = iso_model.predict(X)
    results["isolation_forest"] = {
        "n_samples": len(X),
        "contamination": anomaly_ratio,
        "anomalies_detected": int((predictions == -1).sum()),
    }

    # 2. Clasificador (supervisado, necesita al menos 2 clases)
    unique_labels = set(y)
    if len(unique_labels) >= 2 and all(np.sum(y == label) >= 2 for label in unique_labels):
        logger.info(f"Entrenando clasificador con {len(unique_labels)} clases...")
        results["classifier"] = train_attack_classifier(X, y)
    else:
        logger.warning(f"Clasificador omitido: clases insuficientes {unique_labels}")
        results["classifier"] = {"skipped": True, "reason": "insufficient classes"}

    return results


def _infer_label(event: dict) -> str:
    """Infiere la etiqueta de ataque a partir del tipo de evento."""
    event_type = event.get("event_type", "")
    parsed = event.get("message_parsed") or {}
    url = parsed.get("url", "")

    if event_type in ("ssh_login_failed", "ssh_invalid_user"):
        return "brute_force"
    if event_type == "apache_access":
        if any(p in url.lower() for p in ["../", "etc/passwd", "proc/self"]):
            return "directory_traversal"
        if any(p in url.lower() for p in ["union select", "or 1=1", "drop table", "' or '"]):
            return "sql_injection"
        status = parsed.get("status", 200)
        if status >= 500:
            return "server_error"
        if status in (401, 403):
            return "unauthorized"
    if event_type == "sudo_command":
        target = parsed.get("target_user", "")
        if target == "root":
            return "privilege_escalation"
    return "normal"
