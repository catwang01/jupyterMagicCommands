import tarfile
import os
from docker.models.containers import Container

def copy_to_container(container: Container, src: str, dst: str) -> None:
    with tarfile.open(src + '.tar', mode='w') as f:
        f.add(src, arcname=os.path.basename(src))
    with  open(src + '.tar', 'rb') as f:
        data = f.read()
    targetFolder = os.path.dirname(dst)
    container.exec_run(f"mkdir -p '{targetFolder}'")
    container.put_archive(targetFolder, data)