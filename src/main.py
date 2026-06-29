"""
Punto de entrada por línea de comandos del agente analista de datos.

Uso:
    python -m src.main                      # modo interactivo sobre el dataset de ejemplo
    python -m src.main --csv datos.csv      # usar tu propio CSV
    python -m src.main --pregunta "¿Qué región vende más?"   # una sola pregunta

Requiere la variable de entorno ANTHROPIC_API_KEY (ver .env.example).
"""
from __future__ import annotations

import argparse
import os
import sys

from .agent import DataAnalystAgent

DATASET_POR_DEFECTO = "data/ventas_ejemplo.csv"

EJEMPLOS = [
    "¿Qué región genera más ingresos totales?",
    "¿Cuál es el precio medio por categoría?",
    "Muéstrame los 5 pedidos más grandes.",
    "Hazme un gráfico de ventas totales por categoría.",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Agente de IA analista de datos.")
    parser.add_argument("--csv", default=DATASET_POR_DEFECTO, help="Ruta al CSV a analizar.")
    parser.add_argument("--pregunta", help="Pregunta única (si se omite, modo interactivo).")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Falta la variable de entorno ANTHROPIC_API_KEY.")
        print("    Crea un fichero .env a partir de .env.example, o expórtala en tu shell.")
        return 1

    if not os.path.exists(args.csv):
        print(f"⚠️  No se encuentra el CSV: {args.csv}")
        return 1

    agente = DataAnalystAgent(args.csv)
    print(f"📊 Dataset cargado: {args.csv} ({len(agente.tools.df)} filas)\n")

    # Pregunta única
    if args.pregunta:
        respuesta = agente.ask(args.pregunta)
        print(f"\n💬 {respuesta}")
        return 0

    # Modo interactivo
    print("Escribe una pregunta sobre los datos (o 'salir' para terminar).")
    print("Ejemplos:")
    for ej in EJEMPLOS:
        print(f"  · {ej}")
    print()

    while True:
        try:
            pregunta = input("❓ > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if pregunta.lower() in {"salir", "exit", "quit", ""}:
            break
        respuesta = agente.ask(pregunta)
        print(f"\n💬 {respuesta}\n")

    print("¡Hasta luego!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
