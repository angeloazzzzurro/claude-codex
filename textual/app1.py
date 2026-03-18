from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label, Input
from textual.containers import Vertical, Horizontal


class App1(App):
    CSS = """
    Screen {
        align: center middle;
    }
    Vertical {
        width: 60;
        height: auto;
        border: round green;
        padding: 1 2;
    }
    Label#titolo {
        text-style: bold;
        color: green;
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    Label#output {
        width: 100%;
        content-align: center middle;
        color: yellow;
        margin-top: 1;
    }
    Input {
        margin-bottom: 1;
    }
    Horizontal {
        height: auto;
        align: center middle;
    }
    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("🎉 La mia prima app Textual!", id="titolo")
            yield Input(placeholder="Scrivi il tuo nome...", id="testo")
            with Horizontal():
                yield Button("👋 Saluta", id="invia", variant="success")
                yield Button("🗑️ Cancella", id="reset", variant="error")
            yield Label("Scrivi il tuo nome e premi Saluta!", id="output")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        testo = self.query_one("#testo", Input).value
        output = self.query_one("#output", Label)

        if event.button.id == "invia":
            if testo:
                output.update(f"👋 Ciao, [bold green]{testo}[/bold green]! Benvenuto!")
                self.log(f"Saluto inviato a: {testo}")
            else:
                output.update("[red]Scrivi prima il tuo nome![/red]")
        elif event.button.id == "reset":
            self.query_one("#testo", Input).value = ""
            output.update("In attesa...")
            self.log("Reset eseguito")


if __name__ == "__main__":
    App1().run()
