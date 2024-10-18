import argparse
import logging
import sys
from typing import Set

from jupyterMagicCommands.utils.cs import (
    CSCodeProjectCacheManager,
    CSCodeRunner,
    CSCodeRunnerOptions,
    DotnetCli,
    DotnetCliRunOptions,
    processPackageInfo,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s"
)
streamhandler.setFormatter(formatter)

logger.addHandler(streamhandler)

dotnetCli = DotnetCli(logger=logger)
cacheManager = CSCodeProjectCacheManager(dotnetCli, logger=logger)
runner = CSCodeRunner(cacheManager, dotnetCli, logger=logger)


def transformLogLevel(s):
    level = {"INFO": logging.INFO, "DEBUG": logging.DEBUG}.get(s.upper())
    if level is None:
        print(f"Unsupported level: {s}")
        sys.exit(1)
    return level


def cs(line, cell):
    parser = argparse.ArgumentParser()
    parser.add_argument("--logLevel", default="INFO", type=transformLogLevel)
    parser.add_argument(
        "--addPackage",
        dest="packages",
        type=processPackageInfo,
        action="append",
        default=[],
        help="package information formatted as <packagename>@<version>",
    )
    parser.add_argument(
        "--disable-cache",
        dest="cache",
        default=True,
        action="store_false",
        help="Whether disable caching for creating packages",
    )
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--configuration",
        type=str,
        default="Release",
        help="Configuration for dotnet run",
    )
    if line.strip() != "":
        args = parser.parse_args(line.strip(" ").split(" "))
    else:
        args = parser.parse_args([])

    specifiedPackages: Set[str] = set()
    for package in args.packages:
        name = package["name"]
        if name in specifiedPackages:
            print(f"Can't specify the same package multiple times: {name}")
            sys.exit(1)
        specifiedPackages.add(name)

    logger.setLevel(args.logLevel)
    logger.debug("args: %s", args)

    dotnetCli.verbose = args.verbose
    runnerOptions: CSCodeRunnerOptions = vars(args)  # type: ignore
    runner.options = runnerOptions
    logger.debug("runnerOptions: %s", runnerOptions)
    runOptions: DotnetCliRunOptions = {"configuration": args.configuration}
    runner.runCsharp(cell, runOptions=runOptions)
    cacheManager.saveCache()


def load_ipython_extension(ipython):
    ipython.register_magic_function(cs, "cell")
