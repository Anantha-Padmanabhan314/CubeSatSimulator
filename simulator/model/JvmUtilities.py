# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import os
import subprocess
import sys
import jpype
from jpype import (JClass)


def init_orekit():
    """
    Function to initialize the OREKIT data used by the OREKIT library
    :return:
    """
    data_path = os.path.expanduser("~/orekit-data")

    file = JClass("java.io.File")
    data_context = JClass("org.orekit.data.DataContext")
    directory_crawler = JClass("org.orekit.data.DirectoryCrawler")

    manager = data_context.getDefault().getDataProvidersManager()
    manager.clearProviders()  # optional, ensure no old providers
    manager.addProvider(directory_crawler(file(data_path)))

def _find_libjli(java_home: str):
    """
    Looks for a valid, non-empty libjli.dylib under a given Java home directory.
    :param java_home: candidate JDK home directory
    :return: path to the JVM shared library, or None if not found
    """
    for root, _, names in os.walk(java_home):
        if "libjli.dylib" in names:
            candidate = os.path.join(root, "libjli.dylib")
            if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                return candidate
    return None


def _resolve_jvm_path() -> str:
    """
    Resolves a usable JVM shared library path.

    jpype's own auto-detection scans /Library/Java/JavaVirtualMachines
    alphabetically and only consults the OS-maintained `java_home` registry
    as a last resort, so a stale/broken JDK left over from another machine
    (e.g. an incomplete jdk1.8 install that alphabetically sorts first) can
    get picked before a perfectly good, currently-registered JDK. Prefer the
    OS registry first, and validate whatever path we end up with actually
    exists on disk before using it.
    :return: path to the JVM shared library
    """
    if sys.platform == "darwin":
        try:
            java_home = subprocess.check_output(
                ["/usr/libexec/java_home"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            jvm_path = _find_libjli(java_home)
            if jvm_path:
                return jvm_path
        except Exception:
            pass

    try:
        jvm_path = jpype.getDefaultJVMPath()
        if os.path.isfile(jvm_path) and os.path.getsize(jvm_path) > 0:
            return jvm_path
    except Exception:
        pass

    # JAVA_HOME (or another cached default) points at a JDK that no longer exists here.
    # Drop it and let jpype re-detect an installed JVM.
    stale_java_home = os.environ.pop("JAVA_HOME", None)
    try:
        jvm_path = jpype.getDefaultJVMPath()
        if os.path.isfile(jvm_path) and os.path.getsize(jvm_path) > 0:
            return jvm_path
    except Exception:
        pass

    raise FileNotFoundError(
        "Could not locate a valid Java installation. Install a JDK "
        "(e.g. `brew install --cask temurin` on macOS, or run ./install.sh) "
        f"or fix JAVA_HOME (currently set to: {stale_java_home!r})."
    )


def start_jvm() -> None:
    """
    Method to start the JVM and load OREKIT jar files for use in python environment
    Uses a try...except block to handle the case where the JVM is already started.
    :return:
    """
    try:
        # include all the orekit jar files here
        jar_path = os.path.expanduser("~/Orekit-Jars")
        classpath = os.pathsep.join([
            os.path.join(jar_path, jar) for jar in os.listdir(jar_path) if jar.endswith(".jar")
        ])

        if not jpype.isJVMStarted():
            jpype.startJVM(_resolve_jvm_path(), classpath=classpath)

        #print("JVM started successfully.")
    except RuntimeError as e:
        # This exception is raised if the JVM is already running.
        # The message should mention 'already started'.
        if "already started" in str(e).lower():
            print("JVM already running, skipping initialization.")
        else:
            # Re-raise the exception if it's not the expected "already started" error
            raise e
