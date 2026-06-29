"""
Agente de IA analista de datos — bucle agéntico sobre la API de Anthropic.

El agente recibe una pregunta en lenguaje natural sobre un dataset y decide de
forma autónoma qué herramientas usar (ver `tools.py`) para responderla:
inspecciona el esquema, agrega, ordena, grafica... encadenando llamadas hasta
tener la respuesta. Esto es "Agentic AI": el modelo planifica y actúa, no solo
responde a un único prompt.

Características destacadas:
  - Bucle agéntico manual (tool use) — control total del ciclo pensar→actuar.
  - Pensamiento adaptativo (`thinking: adaptive`) — el modelo decide cuánto razonar.
  - Caché de prompt — el prompt de sistema + las herramientas (la parte estable
    y más grande de cada petición) se cachean para abaratar y acelerar las
    siguientes llamadas del mismo análisis.

Autor: Javier Crespo Berland
"""
from __future__ import annotations

import anthropic

from .tools import TOOL_SCHEMAS, DataTools

# Modelo por defecto. Puedes cambiarlo a "claude-sonnet-4-6" o "claude-haiku-4-5"
# para reducir coste a cambio de algo de capacidad de razonamiento.
MODEL = "claude-opus-4-8"
MAX_TOKENS = 8000
MAX_TURNS = 10  # límite de seguridad para que el bucle nunca sea infinito


SYSTEM_PROMPT = """\
Eres un asistente analista de datos. Respondes preguntas sobre un dataset \
tabular usando exclusivamente las herramientas disponibles; nunca inventes \
cifras que no provengan de una herramienta.

Método de trabajo:
1. Si aún no conoces la estructura del dataset, llama primero a `get_schema`.
2. Elige las herramientas adecuadas para responder (puedes encadenar varias).
3. Cuando el usuario pida un gráfico o visualización, usa `plot_bar`.
4. Termina con una respuesta clara y concisa en español, citando las cifras \
   concretas que has obtenido. Si procede, añade una breve interpretación.
"""


class DataAnalystAgent:
    """Orquesta el ciclo pregunta → razonamiento → herramientas → respuesta."""

    def __init__(self, csv_path: str, model: str = MODEL) -> None:
        self.client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
        self.tools = DataTools(csv_path)
        self.model = model

    def ask(self, question: str, verbose: bool = True) -> str:
        """Responde una pregunta ejecutando el bucle agéntico completo."""
        messages: list[dict] = [{"role": "user", "content": question}]

        for _ in range(MAX_TURNS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                thinking={"type": "adaptive"},
                # Caché de prompt: el sistema + las herramientas son idénticos en
                # cada llamada del análisis. Un breakpoint en el bloque de sistema
                # cachea también las herramientas (orden de render: tools → system).
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            # Guardamos la respuesta completa (incluye bloques de pensamiento,
            # necesarios para continuar la conversación en el mismo modelo).
            messages.append({"role": "assistant", "content": response.content})

            if verbose:
                self._log_cache(response)

            # ¿Ha terminado el agente?
            if response.stop_reason != "tool_use":
                return self._extraer_texto(response)

            # Ejecutamos cada herramienta solicitada y devolvemos los resultados.
            tool_results = []
            for bloque in response.content:
                if bloque.type == "tool_use":
                    if verbose:
                        print(f"  🔧 {bloque.name}({bloque.input})")
                    resultado = self.tools.dispatch(bloque.name, bloque.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": bloque.id,
                            "content": resultado,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})

        return "Se alcanzó el límite de turnos sin una respuesta final."

    # ------------------------------------------------------------------ #

    @staticmethod
    def _extraer_texto(response: anthropic.types.Message) -> str:
        return "\n".join(b.text for b in response.content if b.type == "text").strip()

    @staticmethod
    def _log_cache(response: anthropic.types.Message) -> None:
        u = response.usage
        creados = getattr(u, "cache_creation_input_tokens", 0) or 0
        leidos = getattr(u, "cache_read_input_tokens", 0) or 0
        if creados or leidos:
            print(f"  💾 caché — escritos: {creados}, leídos: {leidos}")
