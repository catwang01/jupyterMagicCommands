import os
import functools
import tempfile
from typing import IO, Optional, List

from docker.models.containers import Container, ExecResult

from jupyterMagicCommands.filesystem.Ifilesystem import IFileSystem
from jupyterMagicCommands.utils.docker import copy_to_container

class DirectoryNotExist(Exception):
    pass

SHELL_DETECT_LIST = ["fish", "bash", "sh", "ash"]

class DockerFileSystem(IFileSystem):
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

    def _execute_cmd(self, cmd: str) -> ExecResult:
        with tempfile.NamedTemporaryFile(mode="w+") as fp:
            fp.write(cmd)
            fp.seek(0)
            self.copy_to_container(fp.name, fp.name)
            results = self.container.exec_run(f"{self.default_shell} {fp.name}", workdir=self._workdir)
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

    def system(self, cmd: str) -> None:
        results = self._execute_cmd(cmd)
        output = results.output.decode()
        # remove the latest "\n" while printing
        if output.endswith('\n'):
            print(output, end="")
        else:
            print(output)
    
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