import re
import time
import psutil
import pexpect
from jupyterMagicCommands.outputters import AbstractOutputter
from jupyterMagicCommands.utils.log import NULL_LOGGER
import sys

if  sys.platform == "win32":
    from pexpect.popen_spawn import PopenSpawn
    Spawn = PopenSpawn
else:
    Spawn = pexpect.spawn

class Session:

    process: Spawn
    outputter: AbstractOutputter

    def __init__(self, program: str, outputter: AbstractOutputter, *args,  logger=NULL_LOGGER, **kwargs):
        self.outputter = outputter
        self.unique_prompt = "XYZPYEXPECTZYX"
        self.logger = logger
        self.program = program
        self.auto_reconnect = kwargs.get('auto_reconnect', True)
        self.auto_reconnect_times = kwargs.get('auto_reconnect_times', 3)
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
        if not self.isalive:
            self.logger.error("The underlying process %s is dead", self.pid)
            if not self.auto_reconnect:
                return
            else:
                reconnect_times = self.auto_reconnect_times
                while not self.isalive and reconnect_times > 0:
                    reconnect_times -= 1
                    self.logger.debug("Reconnecting ... %s times reconnect left", reconnect_times)
                    self.start_process(self.program)
                if not self.isalive:
                    self.logger.error("Reconnecting %s times but still can't create the process", reconnect_times)
                    return

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
                self.logger.debug('timeout with message: %s', message)
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
    
    @property
    def pid(self) -> int:
        return self.process.pid

    @property
    def isalive(self) -> bool:
        return psutil.pid_exists(self.pid)

    def close(self):
        self.process.kill(9)
