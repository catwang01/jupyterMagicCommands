import os
import tarfile
import tempfile
from docker.models.containers import Container
import logging

logger = logging.getLogger(__name__)

def copy_to_container(container: Container, src: str, dst: str) -> None:
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source file {src} can't be found")
    # convert python bytes to hex string
    with open(src, 'rb') as f:
        data = f.read()
    hexString = "".join(map(lambda x: "\\x" + x, data.hex(" ").split(" ")))
    cmd = ["/bin/sh", "-c", f"/bin/echo -n -e '{hexString}' > {dst}"]
    targetFolder = os.path.dirname(dst)
    container.exec_run(f"mkdir -p '{targetFolder}'")
    container.exec_run(cmd)
    # if result.exit_code != 0:
    #     logger.warning(f"Failed to copy {src} to {dst}, error message: {result.output.decode()}")
    #     logger.warning("Down grading to put_archive")
    #     with tarfile.open(src + '.tar', mode='w') as f:
    #         f.add(src, arcname=os.path.basename(dst))
    #     with  open(src + '.tar', 'rb') as f:
    #         data = f.read()
    #     container.put_archive(targetFolder, data)

def _rename_members(members, original, target):
    for member in members:
        if member.name.startswith(original):
            member.name = target + member.name[len(original):]

def copy_from_container(container: Container, src: str, dst: str) -> None:
    # make sure target folder exists
    targetFolder = os.path.dirname(dst)
    if not os.path.exists(targetFolder):
        os.makedirs(targetFolder)
    bits, stat = container.get_archive(src)
    with tempfile.NamedTemporaryFile('wb+', delete=False) as f:
        for chunk in bits:
            f.write(chunk)
    with tarfile.open(f.name) as tar:
        _rename_members(tar.getmembers(), os.path.basename(src), os.path.basename(dst))
        # path参数指定解压到的目录
        tar.extractall(path=targetFolder)