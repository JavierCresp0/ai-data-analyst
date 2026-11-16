# 🤖 AI Data Analyst · Agente de IA para análisis de datos

[![Tests](https://github.com/JavierCresp0/ai-data-analyst/actions/workflows/tests.yml/badge.svg)](https://github.com/JavierCresp0/ai-data-analyst/actions/workflows/tests.yml)

Un **agente de IA (Agentic AI)** que responde preguntas sobre un dataset en **lenguaje natural**. Le preguntas *"¿qué región vende más?"* y el agente **decide por sí solo** qué herramientas usar —inspeccionar el esquema, agregar, ordenar, graficar—, las ejecuta encadenándolas, y te da la respuesta con las cifras reales.

No es un "pregunta → respuesta" simple: el modelo **planifica y actúa de forma autónoma** usando herramientas, que es el núcleo de la *Agentic AI*.

> Proyecto personal construido con la **API de Anthropic (Claude)** y **Python**, aplicando *tool use*, bucle agéntico y *prompt caching*.

---

## ✨ Cómo funciona

```
   Pregunta en lenguaje natural
   "¿Qué categoría tiene el ticket medio más alto?"
              │
              ▼
   ┌────────────────────┐      decide qué herramienta usar
   │   Claude (modelo)  │ ───────────────┐
   │  + razonamiento    │                │
   └────────────────────┘                ▼
              ▲                  ┌──────────────────┐
              │  resultado       │   Herramientas   │
              └──────────────────│  get_schema      │
                                 │  describe_column │  → pandas sobre el CSV
                                 │  aggregate       │
                                 │  top_n           │
                                 │  plot_bar        │
                                 └──────────────────┘
              │
              ▼  (el bucle se repite hasta tener la respuesta)
   Respuesta final con las cifras reales
```

El agente repite el ciclo **razonar → llamar herramienta → leer resultado** tantas veces como necesite antes de responder. Todo el bucle está implementado a mano en [`src/agent.py`](src/agent.py) para que se vea con claridad cómo funciona un agente por dentro.

## 💬 Ejemplo de uso

```text
📊 Dataset cargado: data/ventas_ejemplo.csv (300 filas)

❓ > ¿Qué región genera más ingresos y cuál es su categoría estrella?

  🔧 get_schema({})
  💾 caché — escritos: 612, leídos: 0
  🔧 aggregate({'group_by': 'region', 'metric': 'total', 'operation': 'sum'})
  💾 caché — escritos: 0, leídos: 612
  🔧 aggregate({'group_by': 'categoria', 'metric': 'total', 'operation': 'sum'})
  💾 caché — escritos: 0, leídos: 612

💬 La región con más ingresos es el Centro, con 18.430,55 € en ventas
   totales. A nivel global, la categoría que más factura es Electrónica.
   Te recomendaría priorizar el stock de Electrónica en la región Centro.
```

*(Salida ilustrativa. Fíjate en `💾 caché`: tras la primera llamada, el prompt de sistema y las herramientas se sirven desde caché —`leídos: 612`— abaratando y acelerando el resto del análisis.)*

## 🏗️ Arquitectura

```
ai-data-analyst/
├── src/
│   ├── agent.py      ← bucle agéntico (Claude + tool use + caché + thinking)
│   ├── tools.py      ← las 5 herramientas de análisis (pandas) + sus esquemas
│   └── main.py       ← interfaz por línea de comandos (interactiva)
├── data/
│   └── ventas_ejemplo.csv   ← dataset de ejemplo (300 ventas)
├── tests/
│   └── test_tools.py        ← tests de las herramientas (sin clave de API)
├── requirements.txt
└── .env.example
```

### 🔧 Herramientas que el agente puede invocar

| Herramienta | Qué hace |
|-------------|----------|
| `get_schema` | Devuelve columnas, tipos y nº de filas del dataset |
| `describe_column` | Estadísticos de una columna (media, mediana, top valores...) |
| `aggregate` | Agrupa por una columna y agrega (`sum`/`mean`/`count`/`min`/`max`) |
| `top_n` | Las N filas con mayor (o menor) valor de una métrica |
| `plot_bar` | Genera un gráfico de barras y lo guarda como PNG |

## 🛠️ Tecnologías

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Anthropic_Claude-D97757?style=flat)
![pandas](https://img.shields.io/badge/pandas-150458?style=flat&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=flat)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)

## 🎯 Conceptos aplicados

- **Agentic AI**: el modelo decide y ejecuta acciones de forma autónoma
- **Tool use** (*function calling*) con la API de Anthropic
- **Bucle agéntico manual**: ciclo razonar → actuar → observar, con límite de seguridad de turnos
- **Prompt caching**: el prompt de sistema + las herramientas se cachean para abaratar y acelerar las llamadas sucesivas
- **Pensamiento adaptativo** (`thinking: adaptive`): el modelo regula cuánto razona según la dificultad
- **Análisis de datos** con pandas y visualización con matplotlib
- **Tests** de la lógica de herramientas, independientes de la API

## 🚀 Cómo ejecutar

**1. Instalar dependencias**
```bash
git clone https://github.com/JavierCresp0/ai-data-analyst.git
cd ai-data-analyst
pip install -r requirements.txt
```

**2. Configurar la clave de API** (consíguela en [console.anthropic.com](https://console.anthropic.com/))
```bash
cp .env.example .env        # y edita .env con tu clave
export ANTHROPIC_API_KEY=sk-ant-...   # o expórtala directamente
```

**3. Lanzar el agente**
```bash
python -m src.main                                   # modo interactivo
python -m src.main --pregunta "¿Qué región vende más?"   # una sola pregunta
python -m src.main --csv mis_datos.csv               # con tu propio CSV
```

## 🧪 Tests

Las herramientas de análisis tienen tests que **no requieren clave de API** (prueban la lógica de pandas directamente):

```bash
pytest
```

Se ejecutan también de forma automática en GitHub Actions con cada cambio (la insignia del principio muestra el resultado).

## ⚙️ Configuración

El modelo se define en [`src/agent.py`](src/agent.py) (`MODEL = "claude-opus-4-8"`). Puedes cambiarlo a `claude-sonnet-4-6` o `claude-haiku-4-5` para reducir coste a cambio de algo de capacidad de razonamiento.

---

📌 *Proyecto personal · Javier Crespo Berland — explorando Agentic AI y análisis de datos.*
