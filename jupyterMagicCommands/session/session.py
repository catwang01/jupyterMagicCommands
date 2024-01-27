import pexpect
from jupyterMagicCommands.outputters import AbstractOutputter
import sys

if  sys.platform == "win32":
    from pexpect.popen_spawn import PopenSpawn
    class pexpect_spawn(PopenSpawn):
        def isalive(self):
            return self.proc.poll() is None
    Spawn = pexpect_spawn
else:
    Spawn = pexpect.spawn

class Session:

    child: Spawn
    outputter: AbstractOutputter

    def __init__(self, program: str, *args, outputter: AbstractOutputter):
        self.child = Spawn(program, *args)
        self.outputter = outputter
        self.outputter.register_read_callback(self.child.send)

    def invoke_command(self, command: str):
        self.child.sendline(command)
        prevMessage = ""
        while True:
            try:
                i = self.child.expect_list(
                    [pexpect.TIMEOUT, pexpect.EOF],
                    timeout=0.01,
                )  # fresh terminal per 0.2s
                message = self.child.before.decode()
                self.outputter.write(message[len(prevMessage) :])
                self.outputter.handle_read()
                prevMessage = message
                if i != 0:
                    break
            except KeyboardInterrupt:
                self.child.sendintr()
            except Exception:
                break

    def close(self):
        self.child.close()