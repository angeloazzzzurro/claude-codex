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
    {
        "name": "suggest_next",
        "description": (
            "Analizza tutti i task aperti e suggerisce quale affrontare per primo, "
            "tenendo conto di priorità, scadenze e progetto."
        ),
        "input_schema": {"type": "object", "properties": {}},
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

    elif name == "suggest_next":
        tasks = db.list_tasks(status="todo") + db.list_tasks(status="doing")
        if not tasks:
            return "Nessun task aperto. Ottimo lavoro! 🎉"
        return "Task aperti (per priorità):\n" + "\n".join(_fmt_task(t) for t in tasks)

    return f"Tool '{name}' non riconosciuto."


SYSTEM_PROMPT = """Sei un assistente personale per la gestione dei lavori.
Aiuti l'utente a organizzare, prioritizzare e tenere traccia dei task.
Rispondi sempre in italiano, in modo conciso e pratico.
Usa gli strumenti disponibili per leggere e modificare i task.
Quando l'utente chiede cosa fare, analizza i task aperti e suggerisci quello più urgente."""


class TaskAgent:
    def __init__(self):
        db.init_db()
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.history: list[anthropic.types.MessageParam] = []

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history,
            )

            if response.stop_reason == "end_turn":
                text = next(
                    (b.text for b in response.content if b.type == "text"), ""
                )
                self.history.append({"role": "assistant", "content": response.content})
                return text

            # tool_use: esegui i tool e rimanda i risultati
            self.history.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _execute_tool(block.name, dict(block.input))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            self.history.append({"role": "user", "content": tool_results})
