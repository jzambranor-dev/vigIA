#!/usr/bin/env python3
"""Entrena los modelos ML con logs reales del servidor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.parser import LogParser
from app.ml.trainer import train_from_events

LOG_FILES = [
    ("/var/log/auth.log", "auth.log"),
    ("/var/log/syslog", "syslog"),
    ("/var/log/apache2/access.log", "access.log"),
]

# También incluir sample_logs.log si existe
SAMPLE_LOG = Path(__file__).parent / "sample_logs.log"


def main():
    parser = LogParser()
    events = []

    # Parsear logs reales
    for log_path, name in LOG_FILES:
        path = Path(log_path)
        if not path.exists():
            print(f"  [SKIP] {log_path} no existe")
            continue

        count = 0
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    result = parser.parse(line.strip(), log_path)
                    if result:
                        events.append(result)
                        count += 1
        except PermissionError:
            print(f"  [SKIP] Sin permisos para {log_path}")
            continue

        print(f"  [{name}] {count} eventos parseados")

    # Parsear sample_logs si existe
    if SAMPLE_LOG.exists():
        count = 0
        with open(SAMPLE_LOG, "r") as f:
            for line in f:
                result = parser.parse(line.strip(), "sample_logs.log")
                if result:
                    events.append(result)
                    count += 1
        print(f"  [sample_logs.log] {count} eventos parseados")

    print(f"\nTotal: {len(events)} eventos")

    if len(events) < 10:
        print("ERROR: Muy pocos eventos. Generando logs de prueba primero...")
        # Generar sample logs
        sys.path.insert(0, str(Path(__file__).parent))
        from generate_sample_logs import generate
        generate()
        # Re-parsear
        count = 0
        with open("sample_logs.log", "r") as f:
            for line in f:
                result = parser.parse(line.strip(), "sample_logs.log")
                if result:
                    events.append(result)
                    count += 1
        print(f"  [generated] {count} eventos adicionales")
        print(f"  Total: {len(events)} eventos")

    # Mostrar distribución de labels
    from collections import Counter
    from app.ml.trainer import _infer_label
    label_counts = Counter(_infer_label(e) for e in events)
    print("\nDistribución de etiquetas:")
    for label, count in label_counts.most_common():
        print(f"  {label:25s} {count:6d} ({count/len(events)*100:.1f}%)")

    # Entrenar
    print("\nEntrenando modelos...")
    results = train_from_events(events)

    # Resultados Isolation Forest
    iso = results["isolation_forest"]
    print(f"\n=== Isolation Forest ===")
    print(f"  Muestras: {iso['n_samples']}")
    print(f"  Contaminación: {iso['contamination']:.2%}")
    print(f"  Anomalías detectadas: {iso['anomalies_detected']}")

    # Resultados Clasificador
    clf = results["classifier"]
    if not clf.get("skipped"):
        print(f"\n=== Clasificador de Ataques ===")
        print(f"  Accuracy: {clf['accuracy']:.2%}")
        print(f"  Clases: {clf['classes']}")
        print(f"  Train: {clf['n_train']}, Test: {clf['n_test']}")
        print(f"\n  Top features de importancia:")
        for name, importance in clf["top_features"]:
            print(f"    {name:30s} {importance:.4f}")
    else:
        print(f"\n  Clasificador omitido: {clf.get('reason')}")

    print("\nModelos guardados en backend/app/ml/models/")


if __name__ == "__main__":
    main()
