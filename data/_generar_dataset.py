"""
Genera un dataset de ejemplo (ventas de comercio electrónico) para el agente.
Usa solo la librería estándar — no requiere dependencias externas.
Ejecutar:  python data/_generar_dataset.py
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)  # reproducible

REGIONES = ["Norte", "Sur", "Este", "Oeste", "Centro"]
CATEGORIAS = {
    "Electrónica": [("Auriculares", 49.9), ("Teclado", 35.0), ("Monitor", 189.0), ("Webcam", 59.9)],
    "Hogar": [("Lámpara", 24.5), ("Cafetera", 79.9), ("Sartén", 19.9), ("Toallas", 15.0)],
    "Deporte": [("Zapatillas", 89.9), ("Mochila", 45.0), ("Botella", 12.5), ("Esterilla", 29.9)],
    "Libros": [("Novela", 18.9), ("Manual técnico", 39.9), ("Cómic", 14.9)],
}

inicio = date(2025, 1, 1)
filas = []
for _ in range(300):
    dia = inicio + timedelta(days=random.randint(0, 364))
    categoria = random.choice(list(CATEGORIAS))
    producto, precio_base = random.choice(CATEGORIAS[categoria])
    # pequeña variación de precio
    precio = round(precio_base * random.uniform(0.9, 1.1), 2)
    unidades = random.randint(1, 12)
    filas.append({
        "fecha": dia.isoformat(),
        "region": random.choice(REGIONES),
        "categoria": categoria,
        "producto": producto,
        "unidades": unidades,
        "precio_unitario": precio,
        "total": round(precio * unidades, 2),
    })

filas.sort(key=lambda r: r["fecha"])

with open("data/ventas_ejemplo.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
    writer.writeheader()
    writer.writerows(filas)

print(f"Generadas {len(filas)} filas en data/ventas_ejemplo.csv")
