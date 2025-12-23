from textual.app import App, ComposeResult
from textual.widgets import Markdown, Static, TextArea
from textual.containers import VerticalScroll, Vertical
from textual.events import Key
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
        with Vertical(id="main", classes="centered"):
            yield Static(self.ascii_art, id="ascii-art")
            yield Static("Hey there! Let’s jump in", id="welcome-text1")
            yield Static("linux is the best OS", id="welcome-text2")

            yield VerticalScroll(id="chat-panel")

            yield TextArea(
                id="user-input",
                placeholder="Type your message...",
            )

    async def on_key(self, event: Key) -> None:
        textarea = self.query_one("#user-input", TextArea)


        if event.key == "enter" and not event.shift:
            event.prevent_default()

            user_request = textarea.text.strip()
            textarea.text = ""

            if not user_request:
                return

            await self.handle_user_message(user_request)

    async def handle_user_message(self, user_request: str):
        chat_panel = self.query_one("#chat-panel", VerticalScroll)

        user_md = Markdown(f"**You:** {user_request}\n")
        chat_panel.mount(user_md)

        assistant_md = Markdown("**Assistant:**\n\n")
        chat_panel.mount(assistant_md)

        chat_panel.scroll_end(animate=False)

        # Убираем приветствие
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
