from dataclasses import dataclass
import dataclasses
from enum import Enum
from hashlib import md5
import json
from pprint import pformat
from logging import Logger
import shutil
from typing import Dict, List, Optional, Tuple, TypedDict
from typing_extensions import NotRequired, Required
from jupyterMagicCommands.utils.cmd import executeCmd


from pathlib import Path
from tempfile import mkdtemp

from jupyterMagicCommands.utils.log import NULL_LOGGER


class PackageInfo(TypedDict):
    name: Required[str]
    version: NotRequired[str]

@dataclass
class CacheInfoItem:
    hitCount: int
    packages: Dict[str, PackageInfo]

CacheInfo = Dict[str, CacheInfoItem]

class CacheStatus(Enum):
    MISS = 0  # Not used at this time
    PARTIAL_HIT = 1
    FULL_HIT = 2


class IDotnetCli:

    def addPackage(self, package: PackageInfo, cwd: Optional[str] = None) -> None:
        pass

    def new(self, projectType: str, projectName: str, cwd: Optional[str] = None) -> None:
        pass

    def run(self, cwd: Optional[str] = None) -> None:
        pass

    @property
    def cwd(self) -> str:
        pass

    @cwd.setter
    def cwd(self, value: str) -> None:
        pass


class DotnetCli(IDotnetCli):

    def __init__(self, cwd: str = ".", verbose: bool=False, logger: Logger=NULL_LOGGER) -> None:
        self._cwd = cwd
        self.logger = logger
        self.verbose = verbose

    @property
    def cwd(self) -> str:
        return self._cwd

    @cwd.setter
    def cwd(self, value):
        self._cwd = value

    def addPackage(self, package: PackageInfo, cwd: Optional[str] = None) -> None:
        if "version" in package:
            executeCmd(
                f"dotnet add package {package['name']} --version {package['version']}",
                cwd=cwd or self.cwd,
                verbose=self.verbose,
            )
        else:
            executeCmd(
                f"dotnet add package {package['name']}",
                cwd=cwd or self.cwd,
                verbose=self.verbose,
            )

    def run(self, cwd: Optional[str] = None) -> None:
        # always verbose for `dotnet run`, because it will print the output of the program
        executeCmd("dotnet run --configuration Release --no-restore", cwd=cwd or self.cwd, verbose=True, backend="popen")

    def new(self, projectType: str, projectName: str, cwd: Optional[str] = None) -> None:
        executeCmd(
            f"dotnet new {projectType} -o {projectName}",
            cwd=cwd or self.cwd,
            verbose=self.verbose,
        )


class CSCodeProjectCacheManager:

    cacheRoot: Path
    cacheInfoFile: Path
    logger: Logger
    dotnetCli: IDotnetCli
    cacheInfo: CacheInfo
    EMPTY_CACHE_KEY = "__empty__"

    def __init__(self, dotnetCli: IDotnetCli, cacheRoot: Optional[Path] = None, logger: Logger = NULL_LOGGER) -> None:
        self.dotnetCli = dotnetCli
        self.logger = logger
        self.cacheRoot = cacheRoot or Path("/tmp/jmc/cs")
        if not self.cacheRoot.exists():
            self.cacheRoot.mkdir(parents=True)
        self.cacheInfoFile = self.cacheRoot / "cache.json"

        if self.cacheInfoFile.exists():
            try:
                self.cacheInfo = json.loads(self.cacheInfoFile.read_text(), cls=self.EnhancedJSONDecoder)
            except Exception as e:
                raise Exception(f"Failed to load cache info") from e
        else:
            self.cacheInfo = {}
            cache_path = self.cacheRoot / self.EMPTY_CACHE_KEY
            if not cache_path.exists():
                self.dotnetCli.new(
                    "console", projectName=self.EMPTY_CACHE_KEY, cwd=str(self.cacheRoot)
                )
            self._addCacheItem(self.EMPTY_CACHE_KEY, [])

    def tryToLoadFromCache(
        self, directory: str, packages
    ) -> Tuple[CacheStatus, List[PackageInfo]]:

        if len(packages) == 0:
            self._copyFromCache(self.EMPTY_CACHE_KEY, directory)
            return CacheStatus.FULL_HIT, []
        else:
            shortestMissingPackages = packages
            hittedCacheDir = self.EMPTY_CACHE_KEY
            for cacheDir, cacheInfoItem in self.cacheInfo.items():
                hittedPackages, missingPackageInfo = self.getHittedPackages(
                    cacheInfoItem.packages, packages
                )
                if shortestMissingPackages is None or len(missingPackageInfo) < len(
                    shortestMissingPackages
                ):
                    shortestMissingPackages = missingPackageInfo
                    hittedCacheDir = cacheDir
            self._copyFromCache(hittedCacheDir, directory)
            cacheStatus = CacheStatus.PARTIAL_HIT if len(shortestMissingPackages) > 0 \
                                                  else CacheStatus.FULL_HIT
            return cacheStatus, shortestMissingPackages

    def _addToCache(self, directory: str, packages: List[PackageInfo]) -> None:
        cacheKey = md5(json.dumps(packages).encode()).hexdigest()
        shutil.copytree(directory, self.cacheRoot / cacheKey, dirs_exist_ok=True)
        self._addCacheItem(cacheKey, packages)

    def _copyFromCache(self, cacheKey: str, directory: str) -> None:
        shutil.copytree(
            self.cacheRoot / cacheKey, directory, dirs_exist_ok=True
        )
        self.cacheInfo[cacheKey].hitCount += 1
        self.logger.debug("hit cache to %s", cacheKey)

    def _addCacheItem(self, cacheKey: str, packages: List[PackageInfo]) -> None:
        self.cacheInfo[cacheKey] = CacheInfoItem(
            hitCount=0,
            packages={package["name"]: package for package in packages}
        )

    def getHittedPackages(
        self, packageInfosA: Dict[str, PackageInfo], packages: List[PackageInfo]
    ) -> Tuple[List[PackageInfo], List[PackageInfo]]:
        hittedPackages: List[PackageInfo] = []
        missingPackages: List[PackageInfo] = []
        for packageInfo in packages:
            packageName = packageInfo.get("name")
            if packageName is not None:  # sanity check
                possiblePackageInfo = packageInfosA.get(packageName)
                if possiblePackageInfo:
                    target_version = packageInfo.get("version")
                    if (
                        target_version is None
                        or target_version == possiblePackageInfo.get("version")
                    ):
                        hittedPackages.append(packageInfo)
                        continue
            missingPackages.append(packageInfo)
        return hittedPackages, missingPackages

    class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)
    
    class EnhancedJSONDecoder(json.JSONDecoder):

        def __init__(self, *args, **kwargs):
            super().__init__(object_hook=self.object_hook, *args, **kwargs)

        def object_hook(self, obj):
            if {"hitCount", "packages"} == set(obj.keys()):
                return CacheInfoItem(**obj)
            return obj

    def saveCache(self) -> None:
        self.logger.debug("Saving cache info into %s", self.cacheInfoFile)
        self.logger.debug(pformat(self.cacheInfo))
        with self.cacheInfoFile.open("w") as f:
            json.dump(self.cacheInfo, f, cls=self.EnhancedJSONEncoder)

class CSCodeRunnerOptions(TypedDict):
    cache: bool
    packages: List[PackageInfo]


DEFAULT_CS_CODE_RUNNER_OPTIONS: CSCodeRunnerOptions = {
    "cache": True,
    "packages": [],
}

class CSCodeRunner:

    dotnetCli: IDotnetCli

    def __init__(
        self,
        cacheManager: CSCodeProjectCacheManager,
        dotnetCli: IDotnetCli,
        options: CSCodeRunnerOptions=DEFAULT_CS_CODE_RUNNER_OPTIONS,
        logger: Logger = NULL_LOGGER,
    ):
        self.options = options
        self.cacheManager = cacheManager
        self.dotnetCli = dotnetCli
        self.logger = logger
    
    @property
    def cache(self) -> bool:
        return self.options.get("cache", True)
    
    @property
    def packages(self) -> List[PackageInfo]:
        return self.options.get("packages", [])

    def generateProject(self, directory: str) -> None:
        cacheStatus = None
        if not self.cache:
            missingPackages = self.packages
        else:
            cacheStatus, missingPackages = self.cacheManager.tryToLoadFromCache(
                directory, self.packages
            )
        for package in missingPackages:
            self.dotnetCli.addPackage(package)
        if self.cache and cacheStatus != CacheStatus.FULL_HIT:
            self.cacheManager._addToCache(directory, self.packages)

    def runCsharp(self, cell, directory: Optional[str] = None) -> None:
        # since C#9, there is no need to have a Main
        # code = completeCode(cell, args)
        code = cell
        self.logger.debug(code)
        targetDirectory: Path
        if directory is None:
            targetDirectory = Path(mkdtemp())
        else:
            targetDirectory = Path(directory)
        self.dotnetCli.cwd = str(targetDirectory)
        self.logger.debug('Generating project in %s', targetDirectory)
        self.generateProject(str(targetDirectory))
        tmpFile = targetDirectory / "Program.cs"
        tmpFile.write_text(code)
        self.logger.debug('Running code in %s', targetDirectory)
        self.dotnetCli.run()


def processPackageInfo(s: str) -> PackageInfo:
    ret: PackageInfo = {}  # type: ignore
    infos = s.split("@")
    if len(infos) == 1:
        ret["name"] = infos[0]
    elif len(infos) == 2:
        ret["name"] = infos[0]
        ret["version"] = infos[1]
    else:
        raise Exception(
            f"Not a valid package info: {s}. Package info should be <package-name> or <package-name>@<version>"
        )
    return ret
