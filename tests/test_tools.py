"""
Tests de las herramientas de análisis (DataTools).

No requieren clave de API: prueban directamente la lógica de pandas sobre un
dataset sintético. Ejecutar con:  pytest
"""
import csv
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.tools import DataTools  # noqa: E402


@pytest.fixture()
def csv_tmp(tmp_path):
    """Crea un CSV pequeño y conocido para poder comprobar los resultados."""
    ruta = tmp_path / "datos.csv"
    filas = [
        {"region": "Norte", "categoria": "A", "unidades": 2, "total": 20.0},
        {"region": "Norte", "categoria": "B", "unidades": 1, "total": 50.0},
        {"region": "Sur", "categoria": "A", "unidades": 5, "total": 30.0},
        {"region": "Sur", "categoria": "B", "unidades": 3, "total": 90.0},
    ]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    return str(ruta)


def test_get_schema(csv_tmp):
    info = json.loads(DataTools(csv_tmp).get_schema())
    assert info["filas"] == 4
    nombres = {c["nombre"] for c in info["columnas"]}
    assert nombres == {"region", "categoria", "unidades", "total"}


def test_describe_column_numerica(csv_tmp):
    res = json.loads(DataTools(csv_tmp).describe_column("total"))
    assert res["tipo"] == "numérica"
    assert res["min"] == 20.0
    assert res["max"] == 90.0
    assert res["media"] == 47.5  # (20+50+30+90)/4


def test_describe_column_categorica(csv_tmp):
    res = json.loads(DataTools(csv_tmp).describe_column("region"))
    assert res["tipo"] == "categórica"
    assert res["valores_unicos"] == 2


def test_describe_column_inexistente(csv_tmp):
    res = DataTools(csv_tmp).describe_column("no_existe")
    assert "no existe" in res


def test_aggregate_sum(csv_tmp):
    res = json.loads(DataTools(csv_tmp).aggregate("region", "total", "sum"))
    datos = res["sum(total) por region"]
    assert datos["Sur"] == 120.0   # 30 + 90
    assert datos["Norte"] == 70.0  # 20 + 50


def test_aggregate_operacion_invalida(csv_tmp):
    res = DataTools(csv_tmp).aggregate("region", "total", "median")
    assert "no válida" in res


def test_top_n(csv_tmp):
    filas = json.loads(DataTools(csv_tmp).top_n("total", n=2))
    assert len(filas) == 2
    assert filas[0]["total"] == 90.0  # el mayor primero


def test_top_n_ascending(csv_tmp):
    filas = json.loads(DataTools(csv_tmp).top_n("total", n=1, ascending=True))
    assert filas[0]["total"] == 20.0  # el menor


def test_dispatch_enruta_y_valida(csv_tmp):
    tools = DataTools(csv_tmp)
    # enruta correctamente
    assert "filas" in tools.dispatch("get_schema", {})
    # herramienta desconocida
    assert "desconocida" in tools.dispatch("inventada", {})
    # argumentos incorrectos
    assert "argumentos" in tools.dispatch("describe_column", {"mal_arg": 1})
