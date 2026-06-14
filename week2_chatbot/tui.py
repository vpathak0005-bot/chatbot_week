import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from textual.binding import Binding

from agent import run_agent


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

MAX_HISTORY_TURNS = 20


# ---------------------------------------------------------------------
# Textual App
# ---------------------------------------------------------------------

class ChatApp(App):
    """Perplexity-style research chatbot TUI."""

    TITLE = "Perplexity Clone (Week 2 Project)"

    CSS = """
    Screen {
        layout: vertical;
    }

    RichLog {
        height: 1fr;
        border: solid green;
        padding: 1;
    }

    Input {
        dock: bottom;
        height: 3;
    }
    """

    # -------------------------------------------------------------
    # Key bindings
    # -------------------------------------------------------------

    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear Screen"),
        Binding("ctrl+k", "clear_all", "Reset Chat"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    # -------------------------------------------------------------
    # Init
    # -------------------------------------------------------------

    def __init__(self):
        super().__init__()

        self.messages = []  # not strictly needed here (agent handles state)

    # -------------------------------------------------------------
    # UI layout
    # -------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="log", wrap=True, markup=True)
        yield Input(placeholder="Ask a research question...")
        yield Footer()

    # -------------------------------------------------------------
    # Startup
    # -------------------------------------------------------------

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)

        log.write("[bold green]Perplexity Clone Started[/bold green]\n")
        log.write("Type a question and press Enter.\n")
        log.write("Ctrl+L = clear screen | Ctrl+K = reset | Ctrl+Q = quit\n\n")

        self.query_one(Input).focus()

    # -------------------------------------------------------------
    # Input handler
    # -------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()

        if not user_text:
            return

        event.input.clear()

        log = self.query_one("#log", RichLog)

        # Show user message
        log.write(f"[bold cyan][You][/bold cyan] {user_text}\n")

        # Show thinking indicator
        log.write("[dim]Thinking... searching web & papers...[/dim]\n")

        # Run agent in background thread
        self.run_worker(
             lambda: self._get_response(user_text),
             thread=True
       )

    # -------------------------------------------------------------
    # Worker function (runs in background thread)
    # -------------------------------------------------------------

    def _get_response(self, user_text: str) -> None:
        log = self.query_one("#log", RichLog)

        try:
            # Call agent (blocking, safe in worker thread)
            reply = run_agent(user_text)

            # Update UI safely
            self.call_from_thread(
                log.write,
                f"[bold green][Agent][/bold green] {reply}\n\n",
            )

        except Exception as e:
            self.call_from_thread(
                log.write,
                f"[bold red][Error][/bold red] {str(e)}\n\n",
            )

    # -------------------------------------------------------------
    # Ctrl + L → clear display only
    # -------------------------------------------------------------

    def action_clear_display(self) -> None:
        log = self.query_one("#log", RichLog)
        log.clear()
        log.write("[yellow]Screen cleared (history preserved in agent).[/yellow]\n")

    # -------------------------------------------------------------
    # Ctrl + K → reset everything
    # -------------------------------------------------------------

    def action_clear_all(self) -> None:
        log = self.query_one("#log", RichLog)
        log.clear()
        log.write("[red]Chat reset.[/red]\n")

    # -------------------------------------------------------------
    # Ctrl + Q handled automatically by Textual
    # -------------------------------------------------------------


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    ChatApp().run()