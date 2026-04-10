"""AI Task Manager — Claude API with tool use."""

import json
import os
import anthropic
from . import db

TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "add_task",
        "description": "Aggiunge un nuovo task alla lista.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":    {"type": "string", "description": "Titolo breve del task"},
                "desc":     {"type": "string", "description": "Descrizione dettagliata"},
                "priority": {"type": "integer", "enum": [1, 2, 3],
                             "description": "1=alta 2=media 3=bassa"},
                "project":  {"type": "string", "description": "Progetto di appartenenza"},
                "due_date": {"type": "string", "description": "Scadenza YYYY-MM-DD"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_tasks",
        "description": "Elenca i task. Filtra per stato e/o progetto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status":  {"type": "string", "enum": ["all", "todo", "doing", "done"],
                            "description": "Filtra per stato"},
                "project": {"type": "string", "description": "Filtra per progetto"},
            },
        },
    },
    {
        "name": "update_task",
        "description": "Aggiorna titolo, priorità, stato o progetto di un task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":  {"type": "integer", "description": "ID del task"},
                "title":    {"type": "string"},
                "desc":     {"type": "string"},
                "priority": {"type": "integer", "enum": [1, 2, 3]},
                "status":   {"type": "string", "enum": ["todo", "doing", "done"]},
                "project":  {"type": "string"},
                "due_date": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Elimina definitivamente un task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID del task da eliminare"},
            },
            "required": ["task_id"],
        },
    },
]

PRIORITY_LABEL = {1: "🔴 alta", 2: "🟡 media", 3: "🟢 bassa"}
STATUS_LABEL   = {"todo": "📋 todo", "doing": "⚙️  doing", "done": "✅ done"}


def _fmt_task(t: dict) -> str:
    pri  = PRIORITY_LABEL.get(t.get("priority", 2), "?")
    stat = STATUS_LABEL.get(t.get("status", "todo"), "?")
    proj = f" [{t['project']}]" if t.get("project") else ""
    due  = f" ⏰ {t['due_date']}" if t.get("due_date") else ""
    return f"#{t['id']} {t['title']}{proj} | {pri} | {stat}{due}"


def _execute_tool(name: str, inp: dict) -> str:
    try:
        if name == "add_task":
            t = db.add_task(**inp)
            return f"Task aggiunto: {_fmt_task(t)}"

        elif name == "list_tasks":
            tasks = db.list_tasks(
                status=inp.get("status", "all"),
                project=inp.get("project", ""),
            )
            if not tasks:
                return "Nessun task trovato."
            return "\n".join(_fmt_task(t) for t in tasks)

        elif name == "update_task":
            task_id = inp.pop("task_id")
            t = db.update_task(task_id, **inp)
            if not t:
                return f"Task #{task_id} non trovato."
            return f"Task aggiornato: {_fmt_task(t)}"

        elif name == "delete_task":
            ok = db.delete_task(inp["task_id"])
            return f"Task #{inp['task_id']} eliminato." if ok else "Task non trovato."

        return f"Tool '{name}' non riconosciuto."

    except Exception as e:
        return f"Errore nell'esecuzione di '{name}': {e}"


SYSTEM_PROMPT = """Sei un assistente personale per la gestione dei lavori.
Aiuti l'utente a organizzare, prioritizzare e tenere traccia dei task.
Rispondi sempre in italiano, in modo conciso e pratico.
Usa gli strumenti disponibili per leggere e modificare i task.
Quando l'utente chiede cosa fare, analizza i task aperti e suggerisci quello più urgente."""


class TaskAgent:
    MAX_STEPS = 10
    MAX_HISTORY_TURNS = 20  # turni utente+assistente tenuti in memoria

    def __init__(self):
        db.init_db()
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.history: list[anthropic.types.MessageParam] = db.load_history()

    def _trim_history(self) -> list[anthropic.types.MessageParam]:
        """Ritorna gli ultimi MAX_HISTORY_TURNS turni, sempre in coppia user/assistant."""
        if len(self.history) <= self.MAX_HISTORY_TURNS:
            return self.history
        trimmed = self.history[-self.MAX_HISTORY_TURNS:]
        # Assicura che il primo messaggio sia sempre "user" (no orphan assistant)
        while trimmed and trimmed[0]["role"] != "user":
            trimmed = trimmed[1:]
        return trimmed

    def _step(self, depth: int) -> str:
        if depth == 0:
            return "Errore: raggiunto il limite massimo di operazioni senza completare."

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=self._trim_history(),
        )

        assistant_content = [b.model_dump() for b in response.content]
        self.history.append({"role": "assistant", "content": assistant_content})
        db.save_message("assistant", assistant_content)

        if response.stop_reason == "end_turn":
            return next((b.text for b in response.content if b.type == "text"), "")

        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": _execute_tool(block.name, dict(block.input)),
            }
            for block in response.content
            if block.type == "tool_use"
        ]
        self.history.append({"role": "user", "content": tool_results})
        db.save_message("user", tool_results)
        return self._step(depth - 1)

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        db.save_message("user", user_message)
        return self._step(self.MAX_STEPS)
