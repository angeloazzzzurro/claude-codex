"""
Primo agente Claude — usa tool use con loop automatico.
Strumenti: calcolatrice, meteo (simulato), lista file progetto.

Uso:
    source ~/.venv/bin/activate
    ANTHROPIC_API_KEY=sk-... python primo_agente.py
"""

import json
import os
import math
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Definizione dei tool
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "calcolatrice",
        "description": (
            "Esegue operazioni matematiche. "
            "Supporta: +, -, *, /, ** (potenza), sqrt, sin, cos, tan, log."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "espressione": {
                    "type": "string",
                    "description": "Espressione matematica, es. '2 ** 10' o 'sqrt(144)'",
                }
            },
            "required": ["espressione"],
        },
    },
    {
        "name": "meteo",
        "description": "Restituisce le condizioni meteo simulate per una città italiana.",
        "input_schema": {
            "type": "object",
            "properties": {
                "citta": {
                    "type": "string",
                    "description": "Nome della città, es. 'Milano', 'Roma'",
                }
            },
            "required": ["citta"],
        },
    },
    {
        "name": "lista_file_progetto",
        "description": "Elenca i file Python in una sotto-cartella del progetto claude-codex.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sottocartella": {
                    "type": "string",
                    "description": "Nome della sotto-cartella, es. 'deepML1', 'textual', 'mediapipe'",
                }
            },
            "required": ["sottocartella"],
        },
    },
]

# ---------------------------------------------------------------------------
# Implementazione dei tool
# ---------------------------------------------------------------------------

def _calcolatrice(espressione: str) -> str:
    """Valuta l'espressione in un ambiente sicuro con funzioni math."""
    safe_env = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    safe_env["sqrt"] = math.sqrt
    try:
        risultato = eval(espressione, {"__builtins__": {}}, safe_env)  # noqa: S307
        return f"Risultato di '{espressione}' = {risultato}"
    except Exception as e:
        return f"Errore nel calcolo: {e}"


_METEO_DB = {
    "milano":   "⛅ 18°C, nuvoloso con schiarite",
    "roma":     "☀️  24°C, soleggiato",
    "napoli":   "🌤 22°C, parzialmente nuvoloso",
    "torino":   "🌧 14°C, pioggia leggera",
    "venezia":  "🌫 16°C, nebbia mattutina",
    "firenze":  "☀️  21°C, soleggiato",
    "bologna":  "⛅ 17°C, variabile",
    "palermo":  "☀️  26°C, sereno",
}

def _meteo(citta: str) -> str:
    key = citta.lower().strip()
    if key in _METEO_DB:
        return f"Meteo a {citta.title()}: {_METEO_DB[key]}"
    return f"Dati meteo non disponibili per '{citta}'. Città supportate: {', '.join(c.title() for c in _METEO_DB)}"


def _lista_file_progetto(sottocartella: str) -> str:
    base = Path.home() / "projects" / "claude-codex" / sottocartella
    if not base.exists():
        return f"Cartella '{sottocartella}' non trovata in ~/projects/claude-codex/"
    files = sorted(base.rglob("*.py"))
    if not files:
        return f"Nessun file .py trovato in '{sottocartella}'"
    righe = [f"File Python in '{sottocartella}':"]
    for f in files:
        righe.append(f"  • {f.relative_to(base)}")
    return "\n".join(righe)


def esegui_tool(nome: str, input_data: dict) -> str:
    """Dispatch del tool per nome."""
    if nome == "calcolatrice":
        return _calcolatrice(input_data["espressione"])
    elif nome == "meteo":
        return _meteo(input_data["citta"])
    elif nome == "lista_file_progetto":
        return _lista_file_progetto(input_data["sottocartella"])
    return f"Tool sconosciuto: {nome}"


# ---------------------------------------------------------------------------
# Loop agente
# ---------------------------------------------------------------------------

def agente(prompt_utente: str, verbose: bool = True) -> str:
    """
    Invia il prompt a Claude con tool use.
    Continua il loop finché Claude non risponde con end_turn.
    Restituisce il testo finale dell'agente.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Imposta la variabile d'ambiente ANTHROPIC_API_KEY")

    client = anthropic.Anthropic(api_key=api_key)

    messages = [{"role": "user", "content": prompt_utente}]

    if verbose:
        print(f"\n👤 Utente: {prompt_utente}\n")

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )

        # Raccogliamo il testo e le chiamate tool dalla risposta
        testo_risposta = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                testo_risposta = block.text
            elif block.type == "tool_use":
                tool_calls.append(block)

        # Mostra testo intermedio (se presente prima dei tool)
        if verbose and testo_risposta and response.stop_reason == "tool_use":
            print(f"🤖 Claude (intermedio): {testo_risposta}")

        # Se Claude ha finito, stampa la risposta finale e usciamo
        if response.stop_reason == "end_turn":
            if verbose:
                print(f"🤖 Claude: {testo_risposta}\n")
            return testo_risposta

        # Eseguiamo i tool richiesti
        if verbose:
            for tc in tool_calls:
                print(f"🔧 Tool chiamato: {tc.name}({json.dumps(tc.input, ensure_ascii=False)})")

        # Appendiamo la risposta dell'assistente alla cronologia
        messages.append({"role": "assistant", "content": response.content})

        # Eseguiamo ogni tool e raccogliamo i risultati
        risultati_tool = []
        for tc in tool_calls:
            risultato = esegui_tool(tc.name, tc.input)
            if verbose:
                print(f"   ↳ Risultato: {risultato}")
            risultati_tool.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": risultato,
            })

        # Appendiamo i risultati come messaggio utente
        messages.append({"role": "user", "content": risultati_tool})


# ---------------------------------------------------------------------------
# Main interattivo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Primo Agente Claude 🤖")
    print("  Tool disponibili: calcolatrice, meteo, lista_file_progetto")
    print("  Scrivi 'esci' per terminare")
    print("=" * 60)

    while True:
        try:
            domanda = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nArrivederci!")
            break

        if domanda.lower() in ("esci", "exit", "quit", "q"):
            print("Arrivederci!")
            break

        if not domanda:
            continue

        try:
            agente(domanda)
        except RuntimeError as e:
            print(f"❌ Errore: {e}")
            break
        except anthropic.APIError as e:
            print(f"❌ Errore API: {e}")
