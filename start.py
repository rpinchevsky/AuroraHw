import re
import shlex
import sys


class Command:
    def __init__(self, interpreter):
        self.interpreter = interpreter

    def execute(self, *args):
        pass


class LetCommand(Command):
    def execute(self, register, *expressions):
        # Check if the register is in the range [R0, R9]
        if not re.match(r"^R[0-9]$", register):
            raise ValueError(
                f"Invalid register: {register}. Register must be in the range [R0, R9]."
            )

        value = eval(" ".join(expressions), {}, runtime_state.registers)
        runtime_state.update_register(register, value)
        return runtime_state.pc + 1


class IfCommand(Command):
    def execute(self, register1, comparison, register2, label):
        if len([arg for arg in [register1, comparison, register2, label] if arg]) != 4:
            raise ValueError("IF command expects exactly four arguments.")

        if runtime_state.registers.get(register1, 0) == runtime_state.registers.get(
                register2, 0
        ):
            line_number = self.interpreter.find_label(label)
            return line_number
        else:
            return runtime_state.pc + 1


class JumpCommand(Command):
    def execute(self, label):
        if not label:
            raise ValueError("JUMP command expects a non-empty label.")
        line_number = self.interpreter.find_label(label)
        return line_number


class CallCommand(JumpCommand):
    def execute(self, label):
        label_line_number = super().execute(label)
        runtime_state.stack.append(runtime_state.pc + 1)
        return label_line_number


class PrintCommand(Command):
    def execute(self, register):
        if not register:
            raise ValueError("PRINT command expects a non-empty register.")

        print(runtime_state.registers.get(register, "Register not found"))
        return runtime_state.pc + 1


class ReturnCommand(Command):
    def execute(self):
        if len(runtime_state.stack) > 0:
            return runtime_state.stack.pop()


class RuntimeState:
    def __init__(self):
        self.registers = {}
        self.pc = 0
        self.stack = []

    def update_register(self, register, value):
        self.registers[register] = value


runtime_state = RuntimeState()


class Interpreter:
    def __init__(self, filename):

        self.state = {}
        self.file_name = filename

        self.commands = {
            "LET": LetCommand(self),
            "IF": IfCommand(self),
            "JUMP": JumpCommand(self),
            "CALL": CallCommand(self),
            "PRINT": PrintCommand(self),
            "RETURN": ReturnCommand(self),
        }

        self.labels_dict = {}
        self.code = []

    def prepare_data(self):
        pattern = re.compile(r"^\w+:\s*$")
        lines = self.code
        trimmed_result = []
        line_number_to_read = 0
        line_number_to_write = 0
        while line_number_to_read < len(lines):
            line = lines[line_number_to_read]
            line_number_to_read += 1
            # Remove leading/trailing whitespaces
            line = line.strip()
            line = line.replace("\t", "")
            if not line:
                continue
            trimmed_result.append(line)
            if pattern.match(line):
                label = line.rstrip(":")  # Remove trailing colon
                self.labels_dict[label] = line_number_to_write
            line_number_to_write += 1
            # Skip empty lines
        return trimmed_result

    @staticmethod
    def tokenize_line(line):
        lexer = shlex.shlex(line)
        lexer.whitespace_split = True
        tokens = list(lexer)
        return tokens

    def execute(self):
        self.read_file_and_store()
        lines = self.prepare_data()
        line_number = 0
        while line_number < len(lines):
            line = lines[line_number]
            runtime_state.pc = line_number
            line_number += 1
            tokens = self.tokenize_line(line)
            command_name = tokens[0]
            if not command_name.endswith(":"):
                command_args = [
                    token for token in tokens[1:] if token not in (" ", ":=")
                ]

            if command_name in self.commands:
                command = self.commands[command_name]
                line_number = command.execute(*command_args)

    def find_label(self, key):
        value = self.labels_dict.get(key)
        if value is not None:
            return value
        else:
            raise KeyError(f"Key '{key}' not found in the dictionary.")

    def read_file_and_store(self):
        try:
            with open(self.file_name, "r") as file:
                self.code = file.readlines()
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
            self.code = []
        except Exception as e:
            print(f"Error: {e}")
            self.code = []


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        raise ValueError("Usage: python script.py <filename>")
    else:
        filename = sys.argv[1]

    interpreter = Interpreter(filename)
    interpreter.execute()
