import re
import time
import pexpect
from jupyterMagicCommands.outputters import AbstractOutputter
import sys

if  sys.platform == "win32":
    from pexpect.popen_spawn import PopenSpawn
    Spawn = PopenSpawn
else:
    Spawn = pexpect.spawn

class Session:

    process: Spawn
    outputter: AbstractOutputter

    def __init__(self, program: str, *args, outputter: AbstractOutputter):
        self.outputter = outputter
        self.unique_prompt = "XYZPYEXPECTZYX"
        self.start_process(program)
        self.outputter.register_read_callback(self.process.send)

    def start_process(self, program: str):
        self.process = Spawn(program)
        time.sleep(2)
        init_banner = self.process.read_nonblocking(4096, 2)
        try:
            prompt = re.findall(b'PS [A-Z]:', init_banner, re.MULTILINE)[0]
        except Exception as e:
            raise(Exception("Unable to determine powershell prompt. {0}".format(e)))
        self.process.sendline("Get-Content function:\prompt")
        self.process.expect(prompt)
        #The first 32 characters will be the command we sent in
        self.orig_prompt = self.process.before[32:]
        self.process.sendline('Function prompt{{"{0}"}}'.format(self.unique_prompt))
        self.process.expect(self.unique_prompt)
        self.process.expect(self.unique_prompt)

    def invoke_command(self, command: str):
        self.process.sendline(command)
        prevMessage = ""
        echoedCommandIsRemoved = False
        while True:
            try:
                i = self.process.expect(
                    [pexpect.TIMEOUT, self.unique_prompt],
                    timeout=0.02,
                )  # fresh terminal per 0.2s
                message = self.process.before.decode()
                previousLen = len(prevMessage)
                if not echoedCommandIsRemoved:
                    echoedCommandIsRemoved = True
                    previousLen += len(command)+2
                self.outputter.write(message[previousLen :])
                self.outputter.handle_read()
                prevMessage = message
                if i != 0:
                    break
            except KeyboardInterrupt:
                self.close()
            except Exception:
                break

    def close(self):
        self.process.kill(9)