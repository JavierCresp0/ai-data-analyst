"""
Herramientas de análisis de datos que el agente de IA puede invocar.

Cada método de `DataTools` es una operación de análisis sobre un DataFrame de
pandas (cargado desde un CSV). El agente decide cuáles llamar y con qué
argumentos; esta clase solo ejecuta la operación y devuelve un resultado en
texto, listo para enviarse de vuelta al modelo como `tool_result`.

La lista `TOOL_SCHEMAS` describe estas herramientas en el formato que espera
la API de Anthropic (JSON Schema), y `DataTools.dispatch` enruta una llamada
del modelo al método correspondiente.

Autor: Javier Crespo Berland
"""
from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd


class DataTools:
    """Ejecuta operaciones de análisis sobre un dataset cargado en memoria."""

    def __init__(self, csv_path: str, charts_dir: str = "charts") -> None:
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.charts_dir = charts_dir

    # ------------------------------------------------------------------ #
    # Herramientas (cada una mapea a una entrada de TOOL_SCHEMAS)         #
    # ------------------------------------------------------------------ #

    def get_schema(self) -> str:
        """Devuelve columnas, tipos y nº de filas del dataset."""
        columnas = [
            {"nombre": col, "tipo": str(dtype)}
            for col, dtype in self.df.dtypes.items()
        ]
        info = {
            "filas": int(len(self.df)),
            "columnas": columnas,
            "muestra": self.df.head(3).to_dict(orient="records"),
        }
        return json.dumps(info, ensure_ascii=False, indent=2)

    def describe_column(self, column: str) -> str:
        """Estadísticos de una columna (numérica o categórica)."""
        if column not in self.df.columns:
            return self._error_columna(column)

        serie = self.df[column]
        if pd.api.types.is_numeric_dtype(serie):
            resumen = {
                "columna": column,
                "tipo": "numérica",
                "conteo": int(serie.count()),
                "media": round(float(serie.mean()), 2),
                "mediana": round(float(serie.median()), 2),
                "min": round(float(serie.min()), 2),
                "max": round(float(serie.max()), 2),
                "desviacion_std": round(float(serie.std()), 2),
            }
        else:
            top = serie.value_counts().head(5)
            resumen = {
                "columna": column,
                "tipo": "categórica",
                "valores_unicos": int(serie.nunique()),
                "mas_frecuentes": {str(k): int(v) for k, v in top.items()},
            }
        return json.dumps(resumen, ensure_ascii=False, indent=2)

    def aggregate(self, group_by: str, metric: str, operation: str) -> str:
        """Agrupa por una columna y agrega una métrica (sum/mean/count/min/max)."""
        operaciones = {"sum", "mean", "count", "min", "max"}
        if operation not in operaciones:
            return f"Error: operación '{operation}' no válida. Usa una de: {sorted(operaciones)}."
        if group_by not in self.df.columns:
            return self._error_columna(group_by)
        if metric not in self.df.columns:
            return self._error_columna(metric)

        resultado = self.df.groupby(group_by)[metric].agg(operation)
        resultado = resultado.sort_values(ascending=False).round(2)
        return json.dumps(
            {f"{operation}({metric}) por {group_by}": resultado.to_dict()},
            ensure_ascii=False,
            indent=2,
        )

    def top_n(self, metric: str, n: int = 5, ascending: bool = False) -> str:
        """Devuelve las N filas con mayor (o menor) valor de una métrica."""
        if metric not in self.df.columns:
            return self._error_columna(metric)
        n = max(1, min(int(n), 50))
        filas = self.df.sort_values(metric, ascending=ascending).head(n)
        return json.dumps(filas.to_dict(orient="records"), ensure_ascii=False, indent=2)

    def plot_bar(self, group_by: str, metric: str, operation: str = "sum") -> str:
        """Genera un gráfico de barras agregado y lo guarda como PNG."""
        operaciones = {"sum", "mean", "count", "min", "max"}
        if operation not in operaciones:
            return f"Error: operación '{operation}' no válida. Usa una de: {sorted(operaciones)}."
        if group_by not in self.df.columns or metric not in self.df.columns:
            return self._error_columna(group_by if group_by not in self.df.columns else metric)

        # import diferido: matplotlib solo se necesita al graficar
        import matplotlib
        matplotlib.use("Agg")  # backend sin ventana, para guardar a fichero
        import matplotlib.pyplot as plt

        os.makedirs(self.charts_dir, exist_ok=True)
        datos = self.df.groupby(group_by)[metric].agg(operation).sort_values(ascending=False)

        fig, ax = plt.subplots(figsize=(8, 5))
        datos.plot(kind="bar", ax=ax, color="#1f4e79")
        ax.set_title(f"{operation}({metric}) por {group_by}")
        ax.set_ylabel(f"{operation}({metric})")
        ax.set_xlabel(group_by)
        fig.tight_layout()

        nombre = f"{operation}_{metric}_por_{group_by}.png".replace(" ", "_")
        ruta = os.path.join(self.charts_dir, nombre)
        fig.savefig(ruta, dpi=120)
        plt.close(fig)
        return f"Gráfico guardado en: {ruta}"

    # ------------------------------------------------------------------ #
    # Utilidades internas                                                #
    # ------------------------------------------------------------------ #

    def _error_columna(self, column: str) -> str:
        return (
            f"Error: la columna '{column}' no existe. "
            f"Columnas disponibles: {list(self.df.columns)}."
        )

    def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        """Enruta una llamada de herramienta del modelo al método correspondiente."""
        metodos = {
            "get_schema": self.get_schema,
            "describe_column": self.describe_column,
            "aggregate": self.aggregate,
            "top_n": self.top_n,
            "plot_bar": self.plot_bar,
        }
        if name not in metodos:
            return f"Error: herramienta desconocida '{name}'."
        try:
            return metodos[name](**arguments)
        except TypeError as exc:
            return f"Error en los argumentos de '{name}': {exc}"


# Esquemas de las herramientas en el formato de la API de Anthropic.
# El modelo lee estas descripciones para decidir cuándo y cómo usarlas.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_schema",
        "description": (
            "Devuelve la estructura del dataset: nombre y tipo de cada columna, "
            "número de filas y una muestra. Úsala primero para entender los datos."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "describe_column",
        "description": (
            "Calcula estadísticos de una columna. Si es numérica devuelve media, "
            "mediana, mínimo, máximo y desviación típica; si es categórica, los "
            "valores más frecuentes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "column": {"type": "string", "description": "Nombre exacto de la columna."}
            },
            "required": ["column"],
        },
    },
    {
        "name": "aggregate",
        "description": (
            "Agrupa el dataset por una columna y agrega una métrica numérica. "
            "Útil para responder '¿cuánto vende cada región/categoría?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "description": "Columna por la que agrupar."},
                "metric": {"type": "string", "description": "Columna numérica a agregar."},
                "operation": {
                    "type": "string",
                    "enum": ["sum", "mean", "count", "min", "max"],
                    "description": "Operación de agregación.",
                },
            },
            "required": ["group_by", "metric", "operation"],
        },
    },
    {
        "name": "top_n",
        "description": "Devuelve las N filas con mayor (o menor) valor de una métrica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "description": "Columna por la que ordenar."},
                "n": {"type": "integer", "description": "Cuántas filas devolver (1-50)."},
                "ascending": {
                    "type": "boolean",
                    "description": "true para las más bajas, false (por defecto) para las más altas.",
                },
            },
            "required": ["metric"],
        },
    },
    {
        "name": "plot_bar",
        "description": (
            "Genera un gráfico de barras de una métrica agregada por una columna "
            "y lo guarda como imagen PNG. Úsalo cuando el usuario pida una "
            "visualización o un gráfico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "group_by": {"type": "string", "description": "Columna del eje X."},
                "metric": {"type": "string", "description": "Columna numérica del eje Y."},
                "operation": {
                    "type": "string",
                    "enum": ["sum", "mean", "count", "min", "max"],
                    "description": "Operación de agregación (por defecto sum).",
                },
            },
            "required": ["group_by", "metric"],
        },
    },
]
