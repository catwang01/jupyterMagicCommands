import functools
import logging
import os
import selectors
import tempfile
import time
import types
from typing import IO, List, Optional

from docker.models.containers import Container, ExecResult

from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.outputters import (AbstractOutputter,
                                             InteractiveOutputter,
                                             NonInteractiveOutputter)
from jupyterMagicCommands.utils.docker import (copy_from_container,
                                               copy_to_container)
from jupyterMagicCommands.utils.log import NULL_LOGGER


class DirectoryNotExist(Exception):
    pass

SHELL_DETECT_LIST = ["bash", "sh"]

class DockerFileSystem(IFileSystem):
    def __init__(self, container: Container, workdir: str = '/', logger: logging.Logger=NULL_LOGGER) -> None:
        self.container = container
        self._workdir = workdir
        self._default_shell: Optional[str] = None
        self._default_shell_checked: bool = False
        self.logger = logger

    @property
    def default_shell(self) -> Optional[str]:
        if self._default_shell is None and not self._default_shell_checked:
            self._default_shell = self._detect_default_shells()
            self._default_shell_checked = True
        return self._default_shell

    def _detect_default_shells(self, detect_list: List[str]=SHELL_DETECT_LIST) -> Optional[str]:
        for shell in detect_list:
            results = self.container.exec_run(shell, workdir=self._workdir)
            if results.exit_code == 0:
                return shell
        return None

    def copy_to_container(self, src: str, dst: str):
        copy_to_container(self.container, src, dst)

    def copy_from_container(self, src: str, dst: str):
        copy_from_container(self.container, src, dst)

    def _execute_cmd(self, cmd: str,
                            background: bool=False,
                            outFile: Optional[str]=None, **kwargs) -> ExecResult:
        with tempfile.NamedTemporaryFile(mode="w+") as fp:
            fp.write(cmd)
            fp.seek(0)
            filename = fp.name
            self.logger.debug("Commands to run into files: %s", filename)
            self.logger.debug("Commands: %s", cmd)
            self.logger.debug("Saved")
            self.copy_to_container(filename, filename)
            self.logger.debug("Copying tmp files from %s into container file %s", filename, filename)
            disable_bracketed_paste = 'echo "set enable-bracketed-paste off" > .inputrc && INPUTRC=$PWD/.inputrc'
            actual_cmd_to_run = f'{disable_bracketed_paste} {self.default_shell} {filename}'
            if background:
                if outFile is None:
                    outFile = "/tmp/out.log"
                    print(f"WARNING: outFile is not set, the output of command will written into {outFile} by default")
                actual_cmd_to_run += f" 1>'{outFile}' 2>&1 &"
            actual_cmd_to_run = f"{self.default_shell} -c \'{actual_cmd_to_run}\'"
            self.logger.info("actual command to run: %s", actual_cmd_to_run)
            results = self.container.exec_run(actual_cmd_to_run,
                                              workdir=self._workdir,
                                              user="root",
                                              **kwargs)
        return results

    def exists(self, path: str) -> bool:
        template = f"""\
if [ -e '{path}' ]; then
    echo "Exists"
else
    echo "Doesn't exist"
fi
"""
        results = self._execute_cmd(template)
        output: str = results.output.decode()
        if results.exit_code != 0:
            raise Exception(output)
        return not "Doesn't exist" in output

    def makedirs(self, path: str) -> None:
        template = f"""
mkdir -p '{path}'
"""
        results = self._execute_cmd(template)
        output: str = results.output.decode()
        if results.exit_code != 0:
            raise Exception(output)

    def _is_mode_require_file_exists(self, mode: str) -> bool:
        return 'r' in mode or 'a' in mode

    def _get_temp_file_path(self) -> str:
        return f"/tmp/{time.time()}"

    def open(self, filename: str, mode: str="w+", encoding: str='utf8', **kwargs) -> IO:
        f: IO
        if self._is_mode_require_file_exists(mode):
            temp_file_path = self._get_temp_file_path()
            self.copy_from_container(filename, temp_file_path)
            f = open(temp_file_path, mode=mode, encoding=encoding, **kwargs)
        else:
            f = tempfile.NamedTemporaryFile(mode=mode, encoding=encoding, **kwargs)
        return self.FileInContainerWrapper(self, f, filename) # type: ignore

    def getcwd(self) -> str:
        results = self._execute_cmd('pwd')
        output = results.output.decode().strip()
        if results.exit_code != 0:
            raise Exception(output)
        return output

    def chdir(self, path: str) -> None:
        if not self.exists(path):
            raise DirectoryNotExist(f"target directory '{path}' doesn't exist!")
        if os.path.isabs(path):
            self._workdir = path
        else:
            self._workdir = os.path.join(self._workdir, path)

    def removedirs(self, path: str) -> None:
        template = f"""
rm -rf '{path}'
"""
        results = self._execute_cmd(template)
        output: str = results.output.decode()
        if results.exit_code != 0:
            raise Exception(output)

    def system(self, cmd: str,
                background: bool=False,
                interactive: bool=False,
                outFile: Optional[str]=None) -> None:
        if background:
            results = self._execute_cmd(cmd, background=background, outFile=outFile, detach=True)
            if results.exit_code and results.exit_code != 0:
                raise Exception(results.output.decode())
        else:
            results = self._execute_cmd(cmd, stdin=True, tty=True, socket=True)
            if results.exit_code is not None and results.exit_code != 0:
                raise Exception(results)
            outputter = InteractiveOutputter() if interactive else NonInteractiveOutputter()
            self._handle_socket(results, outputter)

    def _handle_socket(self, results: ExecResult, outputter: AbstractOutputter) -> None:
        sock = results.output._sock # pylint: disable=protected-access

        sock.setblocking(False)
        sel = selectors.DefaultSelector()

        def read(key, mask):
            conn = key.fileobj
            dataToSend = key.data.dataToSend
            def close_sock():
                self.logger.debug('closing', conn)
                sel.unregister(conn)
                conn.close()
            if mask & selectors.EVENT_READ:
                length = 1024
                data = conn.recv(length)
                if not data:
                    close_sock()
                    return
                outputter.write(data.decode("utf8"))
            if mask & selectors.EVENT_WRITE and dataToSend:
                data = dataToSend.pop(0)
                conn.send(data)  # Should be ready

        data = types.SimpleNamespace(callback=read, dataToSend=[])
        sel.register(sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data)

        def get_registered_socket_count():
            return len(sel.get_map())

        outputter.register_read_callback(
            lambda x: data.dataToSend.append(x.encode('utf8'))
        )
        shouldContinue = True
        while shouldContinue:
            try:
                outputter.handle_read()
                events = sel.select(timeout=0.01)
                for key, mask in events:
                    callback = key.data.callback
                    callback(key, mask)
                shouldContinue = get_registered_socket_count() != 0
            except KeyboardInterrupt:
                data.dataToSend.append(b"\x03")

    class FileInContainerWrapper:

        def __init__(self, docker: 'DockerFileSystem', file: IO, path: str):
            self.docker = docker
            self.file = file
            self.path = path

        def __getattr__(self, name):
            # Attribute lookups are delegated to the underlying file
            # and cached for non-numeric results
            # (i.e. methods are cached, closed and friends are not)
            file = self.__dict__['file']
            a = getattr(file, name)
            if hasattr(a, '__call__'):
                func = a
                @functools.wraps(func)
                def func_wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                a = func_wrapper
            if not isinstance(a, int):
                setattr(self, name, a)
            return a

        # The underlying __enter__ method returns the wrong object
        # (self.file) so override it to return the wrapper
        def __enter__(self):
            self.file.__enter__()
            return self

        # Need to trap __exit__ as well to ensure the file gets
        # deleted when used in a with statement
        def __exit__(self, exc, value, tb):
            self.close()
            result = self.file.__exit__(exc, value, tb)
            return result

        def close(self):
            """
            Copy the temporary file, and close it
            """
            self.file.seek(0)
            self.docker.copy_to_container(self.file.name, self.path)
            self.file.close()

        # iter() doesn't use __getattr__ to find the __iter__ method
        def __iter__(self):
            # Don't return iter(self.file), but yield from it to avoid closing
            # file as long as it's being used as iterator (see issue #23700).  We
            # can't use 'yield from' here because iter(file) returns the file
            # object itself, which has a close method, and thus the file would get
            # closed when the generator is finalized, due to PEP380 semantics.
            for line in self.file:
                yield line