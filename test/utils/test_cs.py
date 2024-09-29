from pathlib import Path
from tempfile import mkdtemp
from typing import List, Tuple
from unittest.mock import ANY

import pytest
from jupyterMagicCommands.utils.cs import (
    CSCodeProjectCacheManager,
    CSCodeRunner,
    CSCodeRunnerOptions,
    CacheInfo,
    CacheInfoItem,
    DotnetCli,
    PackageInfo,
    processPackageInfo,
)


@pytest.fixture
def emptyCacheInfo():
    return {"__empty__": CacheInfoItem(hitCount=0, packages={})}


@pytest.fixture
def dotnetCli():
    dotnetCli = DotnetCli()
    from unittest.mock import MagicMock

    dotnetCli.addPackage = MagicMock()
    dotnetCli.run = MagicMock()
    return dotnetCli


def generateTestDataForMultiple():
    p1 = processPackageInfo("Newtonsoft.Json@12.0.3")
    p2 = processPackageInfo("Newtonsoft.Json")
    p3 = processPackageInfo("AutoMapper")
    p4 = processPackageInfo("EntityFramework@5.0.0")

    return [
        [
            ([], {"__empty__": CacheInfoItem(hitCount=1, packages={})}),
            (
                [p1],
                {
                    "__empty__": CacheInfoItem(hitCount=2, packages={}),
                    "294314ba6e464fec7c368a55fe4a92f1": CacheInfoItem(
                        hitCount=0, packages={p1["name"]: p1}
                    ),
                },
            ),
            (
                [p2],
                {
                    "__empty__": CacheInfoItem(hitCount=2, packages={}),
                    "294314ba6e464fec7c368a55fe4a92f1": CacheInfoItem(
                        hitCount=1, packages={p1["name"]: p1}
                    ),
                },
            ),
        ],
        [
            (
                [p1, p3],
                {
                    "__empty__": CacheInfoItem(hitCount=1, packages={}),
                    "a7bd2e543f51271413964fb9b092fcad": CacheInfoItem(
                        hitCount=0, packages={p1["name"]: p1, p3["name"]: p3}
                    ),
                },
            ),
            (
                [p1, p3, p4],
                {
                    "__empty__": CacheInfoItem(hitCount=1, packages={}),
                    "a7bd2e543f51271413964fb9b092fcad": CacheInfoItem(
                        hitCount=1, packages={p1["name"]: p1, p3["name"]: p3}
                    ),
                    "31b680b07579079f2124ee3e21b7b6e3": CacheInfoItem(
                        hitCount=0,
                        packages={
                            p1["name"]: p1,
                            p3["name"]: p3,
                            p4["name"]: p4,
                        },
                    ),
                },
            ),
        ]
    ]


def generateTestData():
    p1 = processPackageInfo("Newtonsoft.Json@12.0.3")
    p2 = processPackageInfo("Newtonsoft.Json")
    p3 = processPackageInfo("AutoMapper")
    p4 = processPackageInfo("EntityFramework@5.0.0")

    return [
        ([], {"__empty__": CacheInfoItem(hitCount=1, packages={})}),
        (
            [p1],
            {
                "__empty__": CacheInfoItem(hitCount=1, packages={}),
                "294314ba6e464fec7c368a55fe4a92f1": CacheInfoItem(
                    hitCount=0, packages={p1["name"]: p1}
                ),
            },
        ),
        (
            [p2],
            {
                "__empty__": CacheInfoItem(hitCount=1, packages={}),
                "1ee44a660a92d5aced100ee3d9eb1c86": CacheInfoItem(
                    hitCount=0, packages={p2["name"]: p2}
                ),
            },
        ),
        (
            [p1, p3],
            {
                "__empty__": CacheInfoItem(hitCount=1, packages={}),
                "a7bd2e543f51271413964fb9b092fcad": CacheInfoItem(
                    hitCount=0, packages={p1["name"]: p1, p3["name"]: p3}
                ),
            },
        ),
        (
            [p1, p3, p4],
            {
                "__empty__": CacheInfoItem(hitCount=1, packages={}),
                "31b680b07579079f2124ee3e21b7b6e3": CacheInfoItem(
                    hitCount=0,
                    packages={
                        p1["name"]: p1,
                        p3["name"]: p3,
                        p4["name"]: p4,
                    },
                ),
            },
        ),
    ]


@pytest.mark.parametrize("packages, expected", generateTestData())
def test_1(
    dotnetCli,
    tmp_path,
    packages: List[PackageInfo],
    expected: CacheInfo,
):
    runnerOptions: CSCodeRunnerOptions = {
        "cache": True,
        "packages": packages,
        "verbose": False,
    }
    cell = 'Console.WriteLine("hello");'
    cacheRoot = Path(tmp_path)
    if not cacheRoot.exists():
        cacheRoot.mkdir(parents=True)

    cacheManager = CSCodeProjectCacheManager(dotnetCli, cacheRoot)
    runner = CSCodeRunner(cacheManager, dotnetCli, runnerOptions)
    targetDirectory = mkdtemp()
    runner.runCsharp(cell, targetDirectory)
    assert Path(targetDirectory).exists()
    assert (Path(targetDirectory) / "Program.cs").exists()
    assert (Path(targetDirectory) / "Program.cs").read_text() == cell
    assert (Path(cacheRoot) / "__empty__").exists()
    assert cacheManager.cacheInfo == expected

@pytest.mark.parametrize("data", generateTestDataForMultiple())
def test_multiple(
    dotnetCli, tmp_path, data: List[Tuple[List[PackageInfo], CacheInfo]]
):
    cell = 'Console.WriteLine("hello");'
    cacheRoot = Path(tmp_path)
    if not cacheRoot.exists():
        cacheRoot.mkdir(parents=True)

    cacheManager = CSCodeProjectCacheManager(dotnetCli, cacheRoot)

    for packages, expected in data:
        runnerOptions: CSCodeRunnerOptions = {
            "cache": True,
            "packages": packages,
            "verbose": False,
        }
        runner = CSCodeRunner(cacheManager, dotnetCli, runnerOptions)
        targetDirectory = mkdtemp()
        runner.runCsharp(cell, targetDirectory)
        assert Path(targetDirectory).exists()
        assert (Path(targetDirectory) / "Program.cs").exists()
        assert (Path(targetDirectory) / "Program.cs").read_text() == cell
        assert (Path(cacheRoot) / "__empty__").exists()
        assert cacheManager.cacheInfo == expected

def test_cacheManager_load_save(emptyCacheInfo, dotnetCli, tmp_path):
    cacheRoot = Path(tmp_path)
    if not cacheRoot.exists():
        cacheRoot.mkdir(parents=True)

    cacheManager = CSCodeProjectCacheManager(dotnetCli, cacheRoot)
    assert cacheManager.cacheInfo == emptyCacheInfo
    cacheManager.saveCache()
    cache_file_path = cacheRoot / "cache.json"
    assert cache_file_path.exists()
    assert cache_file_path.read_text() == '{"__empty__": {"hitCount": 0, "packages": {}}}'
