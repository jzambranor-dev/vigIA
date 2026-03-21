#!/usr/bin/env python3
"""Script standalone para entrenar el modelo Isolation Forest."""

import sys
from pathlib import Path

import numpy as np

# Agregar el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.ml.trainer import train_isolation_forest


def main():
    """Entrena el modelo con datos sintéticos de ejemplo."""
    print("Generando datos de entrenamiento sintéticos...")

    # Features: [severity_score, is_ssh_failed, is_error_level, status_normalized, has_ip]
    n_normal = 1000
    n_anomalous = 50

    # Datos normales
    normal = np.column_stack([
        np.random.uniform(0.0, 0.2, n_normal),     # severity baja
        np.random.choice([0.0, 1.0], n_normal, p=[0.9, 0.1]),  # raro ssh_failed
        np.random.choice([0.0, 1.0], n_normal, p=[0.95, 0.05]),  # raro error
        np.random.uniform(0.3, 0.4, n_normal),      # status 200-ish
        np.random.choice([0.0, 1.0], n_normal, p=[0.3, 0.7]),  # mayoría tiene IP
    ])

    # Datos anómalos
    anomalous = np.column_stack([
        np.random.uniform(0.6, 1.0, n_anomalous),   # severity alta
        np.random.choice([0.0, 1.0], n_anomalous, p=[0.2, 0.8]),  # frecuente ssh_failed
        np.random.choice([0.0, 1.0], n_anomalous, p=[0.3, 0.7]),  # frecuente error
        np.random.uniform(0.6, 1.0, n_anomalous),    # status alto (400-600)
        np.ones(n_anomalous),                         # siempre tiene IP
    ])

    features = np.vstack([normal, anomalous])
    np.random.shuffle(features)

    print(f"Entrenando con {len(features)} muestras ({n_normal} normal, {n_anomalous} anómalas)...")
    model = train_isolation_forest(features, contamination=0.05)

    # Verificar
    predictions = model.predict(features)
    n_detected = (predictions == -1).sum()
    print(f"Anomalías detectadas en entrenamiento: {n_detected}/{len(features)}")
    print("Modelo guardado exitosamente.")


if __name__ == "__main__":
    main()
