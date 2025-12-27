import os
import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Input, Markdown, Static, Button
from textual.containers import VerticalScroll, Vertical, Horizontal

from api import stream_request, APIError


class AICLI(App):
    CSS_PATH = "style.css"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ascii_art = self.load_ascii_art_file()
        self.stream_task: asyncio.Task | None = None
        self.abort_event = asyncio.Event()

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

            # Горизонтальный контейнер для Input и кнопки Abort
        with Horizontal(id="input-row"):
            yield Input(id="user-input", placeholder="Type your message...")
            yield Button("Abort", id="abort-btn", disabled=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "abort-btn":
            if self.stream_task and not self.stream_task.done():
                self.abort_event.set()
                self.stream_task.cancel()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_request = event.value.strip()
        event.input.value = ""

        if not user_request:
            return

        chat_panel = self.query_one("#chat-panel", VerticalScroll)
        abort_btn = self.query_one("#abort-btn", Button)

        # Добавляем сообщение пользователя
        user_md = Markdown(f"**You:** {user_request}\n")
        chat_panel.mount(user_md)

        # Создаём Markdown для ответа ассистента
        assistant_md = Markdown("**Assistant:**\n\n")
        chat_panel.mount(assistant_md)

        chat_panel.scroll_end(animate=False)

        # Скрываем приветствие и ASCII
        self.query_one("#welcome-text1", Static).update("")
        self.query_one("#welcome-text2", Static).update("")
        self.query_one("#ascii-art", Static).update("")

        abort_btn.disabled = False
        self.abort_event.clear()

        async def run_stream():
            full_text = ""
            try:
                async for token in stream_request(user_request):
                    if self.abort_event.is_set():
                        break
                    full_text += token
                    # Обновляем Markdown с уже набранным текстом
                    assistant_md.update(f"**Assistant:**\n\n{full_text}")
                    chat_panel.scroll_end(animate=False)

            except asyncio.CancelledError:
                # При abort показываем текущее сообщение до момента прерывания
                assistant_md.update(f"**Assistant:**\n\n{full_text}\n⛔ Response aborted")

            except APIError as e:
                assistant_md.update(f"**API Error:** `{e}`")

            finally:
                abort_btn.disabled = True

        self.stream_task = asyncio.create_task(run_stream())


if __name__ == "__main__":
    AICLI().run()
