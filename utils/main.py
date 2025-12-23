from textual.app import App, ComposeResult
from textual.widgets import Input, Markdown, Static
from textual.containers import VerticalScroll, Vertical
from api import stream_request, APIError
import os


class AICLI(App):
    CSS_PATH = "style.css"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ascii_art = self.load_ascii_art_file()

    def load_ascii_art_file(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "ASCII.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "ASCII art file not found."

    def compose(self) -> ComposeResult:
        # Главный вертикальный контейнер
        with Vertical(id="main", classes="centered"):
            yield Static(self.ascii_art, id="ascii-art")
            yield Static("Hey there! Let’s jump in", id="welcome-text1")
            yield Static("linux is the best OS", id="welcome-text2")
            yield VerticalScroll(id="chat-panel")  # <-- вертикальный скролл
            yield Input(id="user-input", placeholder="Type your message...")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_request = event.value.strip()
        event.input.value = ""

        if not user_request:
            return

        chat_panel = self.query_one("#chat-panel", VerticalScroll)

        # Добавляем Markdown как раньше
        user_md = Markdown(f"**You:** {user_request}\n")
        chat_panel.mount(user_md)

        assistant_md = Markdown("**Assistant:**\n\n")
        chat_panel.mount(assistant_md)

        # Скроллим вниз при новых сообщениях
        chat_panel.scroll_end(animate=False)

        # Скрываем приветствие
        self.query_one("#welcome-text1", Static).update("")
        self.query_one("#welcome-text2", Static).update("")
        self.query_one("#ascii-art", Static).update("")

        full_text = ""

        try:
            async for token in stream_request(user_request):
                full_text += token
                assistant_md.update(f"**Assistant:**\n\n{full_text}")
                chat_panel.scroll_end(animate=False)
        except APIError as e:
            assistant_md.update(f"**API Error:** `{e}`")
            chat_panel.scroll_end(animate=False)


if __name__ == "__main__":
    AICLI().run()

