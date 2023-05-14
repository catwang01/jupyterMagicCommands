import os
import selectors
import types
import functools
import tempfile
from typing import IO, Optional, List
from docker.models.containers import Container, ExecResult

from jupyterMagicCommands.mixins.logmixin import LogMixin
from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.utils.docker import copy_to_container

class DirectoryNotExist(Exception):
    pass

SHELL_DETECT_LIST = ["fish", "bash", "sh", "ash"]

class DockerFileSystem(IFileSystem, LogMixin):
    def __init__(self, container: Container, workdir: str = '/') -> None:
        self.container = container
        self._workdir = workdir
        self._default_shell: Optional[str] = None
        self._default_shell_checked: bool = False
        
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

    def _execute_cmd(self, cmd: str, 
                            background: bool=False, 
                            outFile: Optional[str]=None, **kwargs) -> ExecResult:
        with tempfile.NamedTemporaryFile(mode="w+") as fp:
            fp.write(cmd)
            fp.seek(0)
            self.copy_to_container(fp.name, fp.name)
            actual_cmd_to_run = f"{self.default_shell} {fp.name}"
            if background:
                if outFile is None:
                    actual_cmd_to_run += f" &"
                    print("WARNING: outFile is not set, the output of command will be discarded")
                else:
                    actual_cmd_to_run += f" 1>'{outFile}' 2>&1 &"
            self.logger.debug("actual command to run: %s", actual_cmd_to_run)
            results = self.container.exec_run(actual_cmd_to_run,
                                              workdir=self._workdir,
                                              **kwargs)
        return results

    def exists(self, path: str) -> bool:
        template = f"""
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
        return not ("Doesn't exist" in output)

    def makedirs(self, path: str) -> None:
        template = f"""
mkdir -p '{path}'
"""
        results = self._execute_cmd(template)
        output: str = results.output.decode()
        if results.exit_code != 0:
            raise Exception(output)

    def open(self, filename: str, mode: str="w+", encoding: str='utf8') -> IO:
        f = tempfile.NamedTemporaryFile(mode, encoding=encoding)
        return self.FileInContainerWrapper(self.container, f, filename)

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
                outFile: Optional[str]=None) -> None:
        if background:
            results = self._execute_cmd(cmd, background=background, outFile=outFile, detach=True)
            if results.exit_code and results.exit_code != 0:
                raise Exception(results.output.decode())
        else:
            results = self._execute_cmd(cmd, stdin=True, tty=True, socket=True)
            if results.exit_code is not None and results.exit_code != 0:
                raise Exception(results)
            self._handle_socket(results)

    def _handle_socket(self, results: ExecResult) -> None:
        sock = results.output._sock

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
                print(data.decode("utf8"), end="")
            if mask & selectors.EVENT_WRITE and dataToSend:
                data = dataToSend.pop(0)
                conn.send(data)  # Should be ready

        data = types.SimpleNamespace(callback=read, dataToSend=[])
        sel.register(sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data)

        def get_registered_socket_count():
            return len(sel.get_map())

        shouldContinue = True
        while shouldContinue:
            try:
                events = sel.select()
                for key, mask in events:
                    callback = key.data.callback
                    callback(key, mask)
                shouldContinue = get_registered_socket_count() != 0
            except KeyboardInterrupt:
                data.dataToSend.append(b"\x03")

    class FileInContainerWrapper:

        def __init__(self, container: Container, file: IO, path: str):
            self.container = container
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
            copy_to_container(self.container, self.file.name, self.path)
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