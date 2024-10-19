import subprocess

from textual import events
from textual import log
from textual.app import App, ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Header, Footer, Input, Static, Log


class PromptInput(Input):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.action_submit()


class Prompt(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class Executed(Message):
        def __init__(self, command: str):
            self.command = command
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Log()
        yield PromptInput()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.post_message(self.Executed(event.value))


class AlpRunner(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alp_commands = []
        self.input = None

    class Exited(Message):
        def __init__(self):
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Static()

    def command(self, command: str) -> None:
        match command.split():
            case ["add", *arg]:
                self.command_add(" ".join(arg))
            case ["remove", index]:
                self.command_remove(int(index))
            case ["list"]:
                self.command_list()
            case ["load", file_type, *arg]:
                self.command_load(file_type, " ".join(arg))
            case ["run"]:
                self.run_alp()
            case ["help"]:
                self.command_help()
            case ["exit"]:
                self.post_message(self.Exited())

    def command_add(self, command: str) -> None:
        self.alp_commands.append(command)
        self.run_alp()

    def command_remove(self, index: int) -> None:
        self.alp_commands.pop(index)
        self.command_list()

    def command_list(self):
        self.query_one(Static).update("\n".join((f'{i}: {x}' for i, x in enumerate(self.alp_commands))))

    def command_load(self, file_type: str, file: str) -> None:
        self.alp_commands.insert(0, file_type)
        with open(file) as f:
            self.input = f.read()
        self.run_alp()

    def command_help(self) -> None:
        help = """
        add <arg> - add argument
        remove <index> - remove argument
        list - list arguments with index
        load <type> <file> - load logs from file
        exit - exit
        """
        self.query_one(Static).update(help)

    def parse_alp_commands(self, commands: list[str]) -> list[str]:
        options = {}
        for command in commands:
            pos = command.find(' ')
            if pos == -1:
                options.setdefault(command, [])
                continue
            option = command[:pos]
            options.setdefault(option, []).append(command[pos:].strip(' "\''))

        raw_commands = []
        for option in options:
            raw_commands.append(option)
            if len(options[option]) == 0:
                continue
            value = ",".join(options[option])
            log(value)
            raw_commands.append(value)
        return raw_commands

    def run_alp(self) -> None:
        command = ["alp"] + self.parse_alp_commands(self.alp_commands)
        log(f'run {command}')
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, input=self.input)
            self.query_one(Static).update(result.stdout)
        except subprocess.CalledProcessError as e:
            self.query_one(Static).update(f"Error: {e.stderr}")


class AlpConsole(App):
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header()
        yield AlpRunner()
        yield Prompt()
        yield Footer()

    def on_prompt_executed(self, event: Prompt.Executed) -> None:
        command = event.command
        self.query_one(AlpRunner).command(command)

    def on_alp_runner_exited(self, event: AlpRunner.Exited) -> None:
        self.exit()


if __name__ == "__main__":
    AlpConsole().run()
