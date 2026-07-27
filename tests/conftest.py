"""Test fixtures for vsdownload.py tests."""

import json
import os
import sys

import pytest

# Add parent dir so we can import vsdownload
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import vsdownload as vs


@pytest.fixture
def sample_packages():
    """A minimal set of packages for testing dependency resolution."""
    return {
        "microsoft.visualstudio.workload.vctools": [
            {
                "id": "Microsoft.VisualStudio.Workload.VCTools",
                "type": "Workload",
                "version": "1.0.0",
                "chip": "x64",
                "machineArch": "x64",
                "dependencies": {
                    "Microsoft.VisualStudio.Component.VC.Tools.x86.x64": {"version": "1.0.0"},
                    "Microsoft.VisualStudio.Component.VC.ATL": {"version": "1.0.0", "type": "Recommended"},
                },
            }
        ],
        "microsoft.visualstudio.component.vc.tools.x86.x64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "x64",
                "machineArch": "x64",
                "payloads": [{"fileName": "vc_tools.msi", "size": 1000000, "sha256": "a" * 64}],
                "installSizes": {"default": 5000000},
            }
        ],
        "microsoft.visualstudio.component.vc.atl": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.ATL",
                "type": "Component",
                "version": "1.0.0",
                "chip": "x64",
                "machineArch": "x64",
                "payloads": [{"fileName": "vc_atl.msi", "size": 500000, "sha256": "b" * 64}],
                "installSizes": {"default": 2000000},
            }
        ],
        "microsoft.visualstudio.component.vc.14.20.x86.x64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.20.x86.x64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "x64",
                "machineArch": "x64",
            }
        ],
        "microsoft.vc.14.20.asan.x86": [
            {
                "id": "Microsoft.VC.14.20.ASAN.X86",
                "type": "Component",
                "version": "1.0.0",
                "chip": "x86",
                "machineArch": "x86",
            }
        ],
        "microsoft.visualstudio.component.vc.14.20.atl": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.20.ATL",
                "type": "Component",
                "version": "1.0.0",
                "chip": "x64",
                "machineArch": "x64",
            }
        ],
        "microsoft.visualstudio.component.vc.14.20.arm": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.20.ARM",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm",
                "machineArch": "arm",
            }
        ],
        "microsoft.visualstudio.component.vc.14.20.atl.arm": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.20.ATL.ARM",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm",
                "machineArch": "arm",
            }
        ],
        "microsoft.visualstudio.component.vc.14.20.arm64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.20.ARM64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm64",
                "machineArch": "arm64",
            }
        ],
        "microsoft.visualstudio.component.vc.14.20.atl.arm64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.20.ATL.ARM64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm64",
                "machineArch": "arm64",
            }
        ],
        "microsoft.visualstudio.component.vc.tools.arm": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.Tools.ARM",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm",
                "machineArch": "arm",
            }
        ],
        "microsoft.visualstudio.component.vc.tools.arm64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.Tools.ARM64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm64",
                "machineArch": "arm64",
            }
        ],
        "microsoft.visualstudio.component.vc.atl.arm": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.ATL.ARM",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm",
                "machineArch": "arm",
            }
        ],
        "microsoft.visualstudio.component.vc.atl.arm64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.ATL.ARM64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm64",
                "machineArch": "arm64",
            }
        ],
        "win10sdk_10.0.17763": [
            {
                "id": "Win10SDK_10.0.17763",
                "type": "Msi",
                "version": "10.0.17763",
                "payloads": [{"fileName": "sdksetup.msi", "size": 2000000}],
            }
        ],
        "win10sdk_10.0.19041": [
            {
                "id": "Win10SDK_10.0.19041",
                "type": "Msi",
                "version": "10.0.19041",
                "payloads": [{"fileName": "sdksetup.msi", "size": 2000000}],
            }
        ],
        "win11sdk_10.0.26100": [
            {
                "id": "Win11SDK_10.0.26100",
                "type": "Msi",
                "version": "10.0.26100",
                "payloads": [{"fileName": "sdksetup.msi", "size": 2000000}],
            }
        ],
        "microsoft.visualcpp.tools.hostx64.targetx64": [
            {
                "id": "Microsoft.VisualCpp.Tools.HostX64.TargetX64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "x64",
                "machineArch": "x64",
            }
        ],
        "microsoft.visualcpp.tools.hostarm64.targetx64": [
            {
                "id": "Microsoft.VisualCpp.Tools.HostARM64.TargetX64",
                "type": "Component",
                "version": "1.0.0",
                "chip": "arm64",
                "machineArch": "arm64",
            }
        ],
        "component.microsoft.windows.driverkit.buildtools": [
            {
                "id": "Component.Microsoft.Windows.DriverKit.BuildTools",
                "type": "Component",
                "version": "1.0.0",
            }
        ],
        "microsoft.visualstudio.component.vc.tools.14.16": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.Tools.14.16",
                "type": "Component",
                "version": "14.16.0",
            }
        ],
        "microsoft.visualstudio.component.vc.14.44.17.14.x86.x64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.44.17.14.x86.x64",
                "type": "Component",
                "version": "14.44.17.14",
                "chip": "x64",
                "machineArch": "x64",
            }
        ],
        "microsoft.vc.14.44.17.14.asan.x86": [
            {
                "id": "Microsoft.VC.14.44.17.14.ASAN.X86",
                "type": "Component",
                "version": "14.44.17.14",
                "chip": "x86",
                "machineArch": "x86",
            }
        ],
        "microsoft.visualstudio.component.vc.14.44.17.14.atl": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.44.17.14.ATL",
                "type": "Component",
                "version": "14.44.17.14",
                "chip": "x64",
                "machineArch": "x64",
            }
        ],
        "microsoft.visualstudio.component.vc.14.44.17.14.arm": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.44.17.14.ARM",
                "type": "Component",
                "version": "14.44.17.14",
                "chip": "arm",
                "machineArch": "arm",
            }
        ],
        "microsoft.visualstudio.component.vc.14.44.17.14.atl.arm": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.44.17.14.ATL.ARM",
                "type": "Component",
                "version": "14.44.17.14",
                "chip": "arm",
                "machineArch": "arm",
            }
        ],
        "microsoft.visualstudio.component.vc.14.44.17.14.arm64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.44.17.14.ARM64",
                "type": "Component",
                "version": "14.44.17.14",
                "chip": "arm64",
                "machineArch": "arm64",
            }
        ],
        "microsoft.visualstudio.component.vc.14.44.17.14.atl.arm64": [
            {
                "id": "Microsoft.VisualStudio.Component.VC.14.44.17.14.ATL.ARM64",
                "type": "Component",
                "version": "14.44.17.14",
                "chip": "arm64",
                "machineArch": "arm64",
            }
        ],
    }


@pytest.fixture
def sample_manifest(sample_packages):
    """A minimal manifest for testing."""
    return {
        "info": {"productDisplayVersion": "17.0.0"},
        "packages": [p[0] for p in sample_packages.values()],
    }


@pytest.fixture
def args_defaults():
    """Default args object for testing."""
    class Args:
        pass
    a = Args()
    a.manifest = None
    a.major = 17
    a.type = "release"
    a.cache = None
    a.dest = None
    a.package = []
    a.ignore = []
    a.accept_license = True
    a.print_version = False
    a.list_components = False
    a.list_workloads = False
    a.list_packages = False
    a.print_deps_tree = False
    a.print_reverse_deps = False
    a.print_selection = False
    a.only_download = False
    a.only_unpack = False
    a.keep_unpack = False
    a.msvc_version = None
    a.sdk_version = None
    a.architecture = None
    a.host_arch = "x64"
    a.only_host = True
    a.include_optional = False
    a.skip_recommended = False
    a.skip_patch = False
    a.with_wdk_installers = None
    a.save_manifest = None
    return a


