"""Tests for vsdownload.py — pure functions tested without network access."""

import hashlib
import os
import sys
import tempfile
import zipfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import vsdownload as vs


class TestFormatSize:
    def test_bytes(self):
        assert vs.formatSize(0) == "0 bytes"
        assert vs.formatSize(1) == "1 bytes"
        assert vs.formatSize(900) == "900 bytes"
        assert vs.formatSize(1024) == "1024 bytes"  # threshold is > 900*1024

    def test_kb(self):
        # Threshold is > 900*1024 (900 KB) → returns MB
        assert vs.formatSize(1024 * 900 + 1) == "0.9 MB"
        assert vs.formatSize(1024 * 500) == "500.0 KB"
        assert vs.formatSize(1024 * 900) == "900.0 KB"

    def test_mb(self):
        assert vs.formatSize(1024 * 1024) == "1.0 MB"
        assert vs.formatSize(1024 * 1024 * 500) == "500.0 MB"

    def test_gb(self):
        assert vs.formatSize(1024 * 1024 * 1024) == "1.0 GB"
        assert vs.formatSize(1024 * 1024 * 1024 * 2) == "2.0 GB"


class TestFindPackage:
    def test_find_existing(self, sample_packages):
        p = vs.findPackage(sample_packages, "Microsoft.VisualStudio.Component.VC.Tools.x86.x64")
        assert p is not None
        assert p["id"] == "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"

    def test_find_case_insensitive(self, sample_packages):
        p = vs.findPackage(sample_packages, "MICROSOFT.VISUALSTUDIO.COMPONENT.VC.TOOLS.X86.X64")
        assert p is not None
        assert p["id"] == "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"

    def test_find_not_found(self, sample_packages):
        p = vs.findPackage(sample_packages, "NonExistent.Package", warn=False)
        assert p is None

    def test_find_with_constraints(self, sample_packages):
        p = vs.findPackage(sample_packages, "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                           constraints={"chip": "x64"})
        assert p is not None
        assert p["chip"] == "x64"

    def test_find_with_mismatched_constraints(self, sample_packages):
        p = vs.findPackage(sample_packages, "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                           constraints={"chip": "arm64"}, warn=False)
        # Falls back to first candidate when constraints don't match
        assert p is not None


class TestGetPackageKey:
    def test_basic(self):
        p = {"id": "Test.Package"}
        assert vs.getPackageKey(p) == "Test.Package"

    def test_with_version(self):
        p = {"id": "Test.Package", "version": "1.0.0"}
        assert vs.getPackageKey(p) == "Test.Package-1.0.0"

    def test_with_arch(self):
        p = {"id": "Test.Package", "chip": "x64", "machineArch": "x64"}
        key = vs.getPackageKey(p)
        assert "chip.x64" in key
        assert "machineArch.x64" in key

    def test_with_all_fields(self):
        p = {"id": "Test.Package", "version": "2.0.0", "chip": "arm64", "machineArch": "arm64", "productArch": "arm64"}
        key = vs.getPackageKey(p)
        assert key.startswith("Test.Package-2.0.0")
        assert "chip.arm64" in key
        assert "machineArch.arm64" in key
        assert "productArch.arm64" in key


class TestPrioritizePackage:
    def test_neutral_arch(self):
        a = {"chip": "neutral"}
        b = {"chip": "neutral"}
        assert vs.prioritizePackage("x64", a, b) == 0

    def test_preferred_arch_first(self):
        a = {"chip": "x64"}
        b = {"chip": "arm64"}
        assert vs.prioritizePackage("x64", a, b) < 0

    def test_preferred_arch_second(self):
        a = {"chip": "arm64"}
        b = {"chip": "x64"}
        assert vs.prioritizePackage("x64", a, b) > 0

    def test_english_preferred(self):
        a = {"chip": "neutral", "language": "en-US"}
        b = {"chip": "neutral", "language": "de-DE"}
        assert vs.prioritizePackage("x64", a, b) < 0

    def test_english_over_non_english(self):
        a = {"chip": "neutral", "language": "de-DE"}
        b = {"chip": "neutral", "language": "en-US"}
        assert vs.prioritizePackage("x64", a, b) > 0


class TestMatchPackageHostArch:
    def test_none_host(self):
        p = {"id": "Test.Package"}
        assert vs.matchPackageHostArch(p, None) is True

    def test_host_in_id_matches(self):
        p = {"id": "Microsoft.VisualCpp.Tools.HostX64.TargetX64"}
        assert vs.matchPackageHostArch(p, "x64") is True

    def test_host_in_id_mismatch(self):
        p = {"id": "Microsoft.VisualCpp.Tools.HostARM64.TargetX64"}
        assert vs.matchPackageHostArch(p, "x64") is False

    def test_chip_matches(self):
        p = {"id": "Test", "chip": "x64"}
        assert vs.matchPackageHostArch(p, "x64") is True

    def test_chip_mismatch(self):
        p = {"id": "Test", "chip": "arm64"}
        assert vs.matchPackageHostArch(p, "x64") is False

    def test_neutral_chip(self):
        p = {"id": "Test", "chip": "neutral"}
        assert vs.matchPackageHostArch(p, "x64") is True


class TestSumInstalledSize:
    def test_empty(self):
        assert vs.sumInstalledSize([]) == 0

    def test_single_package(self):
        l = [{"installSizes": {"default": 5000000}}]
        assert vs.sumInstalledSize(l) == 5000000

    def test_multiple_packages(self):
        l = [
            {"installSizes": {"default": 5000000}},
            {"installSizes": {"default": 2000000}},
        ]
        assert vs.sumInstalledSize(l) == 7000000

    def test_package_without_install_sizes(self):
        l = [{"id": "Test"}]
        assert vs.sumInstalledSize(l) == 0

    def test_multiple_locations(self):
        l = [{"installSizes": {"a": 1000000, "b": 2000000}}]
        assert vs.sumInstalledSize(l) == 3000000


class TestSumDownloadSize:
    def test_empty(self):
        assert vs.sumDownloadSize([]) == 0

    def test_single_payload(self):
        l = [{"payloads": [{"size": 1000000}]}]
        assert vs.sumDownloadSize(l) == 1000000

    def test_multiple_payloads(self):
        l = [{"payloads": [{"size": 1000000}, {"size": 500000}]}]
        assert vs.sumDownloadSize(l) == 1500000

    def test_package_without_payloads(self):
        l = [{"id": "Test"}]
        assert vs.sumDownloadSize(l) == 0

    def test_payload_without_size(self):
        l = [{"payloads": [{"fileName": "test.msi"}]}]
        assert vs.sumDownloadSize(l) == 0


class TestGetPayloadName:
    def test_simple_filename(self):
        assert vs.getPayloadName({"fileName": "test.msi"}) == "test.msi"

    def test_windows_path(self):
        assert vs.getPayloadName({"fileName": "dir\\sub\\test.msi"}) == "test.msi"

    def test_unix_path(self):
        assert vs.getPayloadName({"fileName": "dir/sub/test.msi"}) == "test.msi"

    def test_mixed_path(self):
        assert vs.getPayloadName({"fileName": "dir\\sub/test.msi"}) == "test.msi"


class TestSha256File:
    def test_known_hash(self):
        content = b"hello world"
        expected = hashlib.sha256(content).hexdigest()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            f.flush()
            result = vs.sha256File(f.name)
        os.unlink(f.name)
        assert result == expected

    def test_empty_file(self):
        expected = hashlib.sha256(b"").hexdigest()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.flush()
            result = vs.sha256File(f.name)
        os.unlink(f.name)
        assert result == expected


class TestMakedirs:
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "a", "b", "c")
            vs.makedirs(d)
            assert os.path.isdir(d)

    def test_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            vs.makedirs(tmp)  # Should not raise
            assert os.path.isdir(tmp)


class TestLowercaseIgnores:
    def test_none_ignore(self):
        class Args:
            pass
        a = Args()
        a.ignore = None
        vs.lowercaseIgnores(a)
        assert a.ignore == []

    def test_lowercases(self):
        class Args:
            pass
        a = Args()
        a.ignore = ["MICROSOFT.VISUALSTUDIO", "Test.Package"]
        vs.lowercaseIgnores(a)
        assert a.ignore == ["microsoft.visualstudio", "test.package"]

    def test_empty_list(self):
        class Args:
            pass
        a = Args()
        a.ignore = []
        vs.lowercaseIgnores(a)
        assert a.ignore == []


class TestGetPackages:
    def test_groups_by_id(self, sample_manifest):
        packages = vs.getPackages(sample_manifest, "x64")
        assert len(packages) > 0
        # Each key should map to a list
        for key, vals in packages.items():
            assert isinstance(vals, list)
            assert len(vals) > 0

    def test_sorted_by_priority(self, sample_manifest):
        packages = vs.getPackages(sample_manifest, "x64")
        for key, vals in packages.items():
            if len(vals) > 1:
                # First should be preferred arch
                assert vals[0].get("chip", "neutral") in ("neutral", "x64")


class TestListPackageType:
    def test_list_components(self, sample_packages, capsys):
        vs.listPackageType(sample_packages, "Component")
        captured = capsys.readouterr()
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in captured.out

    def test_list_workloads(self, sample_packages, capsys):
        vs.listPackageType(sample_packages, "Workload")
        captured = capsys.readouterr()
        assert "Microsoft.VisualStudio.Workload.VCTools" in captured.out

    def test_list_all(self, sample_packages, capsys):
        vs.listPackageType(sample_packages, None)
        captured = capsys.readouterr()
        assert "Microsoft.VisualStudio.Workload.VCTools" in captured.out
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in captured.out


class TestSetPackageSelectionMSVC16:
    def test_adds_x86_x64_packages(self, sample_packages, args_defaults):
        args_defaults.architecture = ["x86", "x64"]
        args_defaults.sdk_version = None
        vs.setPackageSelectionMSVC16(args_defaults, sample_packages, "16.0", "10.0.17763", "14.20", ["default"])
        assert "Microsoft.VisualStudio.Component.VC.14.20.x86.x64" in args_defaults.package
        assert "Microsoft.VC.14.20.ASAN.X86" in args_defaults.package
        assert "Microsoft.VisualStudio.Component.VC.14.20.ATL" in args_defaults.package

    def test_adds_arm_packages(self, sample_packages, args_defaults):
        args_defaults.architecture = ["arm"]
        args_defaults.sdk_version = None
        vs.setPackageSelectionMSVC16(args_defaults, sample_packages, "16.0", "10.0.17763", "14.20", ["default"])
        assert "Microsoft.VisualStudio.Component.VC.14.20.ARM" in args_defaults.package
        assert "Microsoft.VisualStudio.Component.VC.14.20.ATL.ARM" in args_defaults.package

    def test_adds_arm64_packages(self, sample_packages, args_defaults):
        args_defaults.architecture = ["arm64"]
        args_defaults.sdk_version = None
        vs.setPackageSelectionMSVC16(args_defaults, sample_packages, "16.0", "10.0.17763", "14.20", ["default"])
        assert "Microsoft.VisualStudio.Component.VC.14.20.ARM64" in args_defaults.package
        assert "Microsoft.VisualStudio.Component.VC.14.20.ATL.ARM64" in args_defaults.package

    def test_sets_sdk_version(self, sample_packages, args_defaults):
        args_defaults.architecture = ["x64"]
        args_defaults.sdk_version = None
        vs.setPackageSelectionMSVC16(args_defaults, sample_packages, "16.0", "10.0.17763", "14.20", ["default"])
        assert args_defaults.sdk_version == "10.0.17763"

    def test_fallback_to_default(self, sample_packages, args_defaults):
        args_defaults.architecture = ["x64"]
        args_defaults.sdk_version = None
        vs.setPackageSelectionMSVC16(args_defaults, sample_packages, "99.0", "10.0.99999", "99.99", ["default"])
        assert "default" in args_defaults.package


class TestSetPackageSelectionMSVC15:
    def test_adds_packages(self, sample_packages, args_defaults):
        vs.setPackageSelectionMSVC15(args_defaults, sample_packages, "15.9", "10.0.17763", "14.16", ["default"])
        assert "Win10SDK_10.0.17763" in args_defaults.package
        assert "Microsoft.VisualStudio.Component.VC.Tools.14.16" in args_defaults.package

    def test_fallback_to_default(self, sample_packages, args_defaults):
        vs.setPackageSelectionMSVC15(args_defaults, sample_packages, "99.0", "10.0.99999", "99.99", ["default"])
        assert "default" in args_defaults.package


class TestSetPackageSelection:
    def test_default_architectures(self, sample_packages, args_defaults):
        args_defaults.architecture = None
        vs.setPackageSelection(args_defaults, sample_packages)
        # host_arch="x64" gets appended when "host" is in architecture
        assert args_defaults.architecture == ["host", "x86", "x64", "arm", "arm64", "x64"]

    def test_default_packages_when_empty(self, sample_packages, args_defaults):
        args_defaults.architecture = ["x64"]
        vs.setPackageSelection(args_defaults, sample_packages)
        assert "Microsoft.VisualStudio.Workload.VCTools" in args_defaults.package
        assert "Microsoft.VisualStudio.Component.VC.ATL" in args_defaults.package

    def test_msvc_16_0_selection(self, sample_packages, args_defaults):
        args_defaults.msvc_version = "16.0"
        args_defaults.architecture = ["x64"]
        vs.setPackageSelection(args_defaults, sample_packages)
        assert args_defaults.sdk_version == "10.0.17763"

    def test_msvc_17_14_selection(self, sample_packages, args_defaults):
        args_defaults.msvc_version = "17.14"
        args_defaults.architecture = ["x64"]
        vs.setPackageSelection(args_defaults, sample_packages)
        assert args_defaults.sdk_version == "10.0.26100"

    def test_msvc_15_9_selection(self, sample_packages, args_defaults):
        args_defaults.msvc_version = "15.9"
        args_defaults.architecture = ["x64"]
        vs.setPackageSelection(args_defaults, sample_packages)
        assert "Win10SDK_10.0.17763" in args_defaults.package

    def test_unsupported_msvc_version(self, sample_packages, args_defaults):
        args_defaults.msvc_version = "14.0"
        with pytest.raises(SystemExit):
            vs.setPackageSelection(args_defaults, sample_packages)

    def test_sdk_version_override(self, sample_packages, args_defaults):
        args_defaults.sdk_version = "10.0.19041"
        args_defaults.architecture = ["x64"]
        vs.setPackageSelection(args_defaults, sample_packages)
        # The code appends the lowercase key from the packages dict
        assert "win10sdk_10.0.19041" in args_defaults.package

    def test_sdk_version_not_found(self, sample_packages, args_defaults):
        args_defaults.sdk_version = "10.0.99999"
        args_defaults.architecture = ["x64"]
        with pytest.raises(SystemExit):
            vs.setPackageSelection(args_defaults, sample_packages)

    def test_wdk_installer(self, sample_packages, args_defaults):
        args_defaults.with_wdk_installers = "/tmp/wdk"
        args_defaults.architecture = ["x64"]
        vs.setPackageSelection(args_defaults, sample_packages)
        assert "Component.Microsoft.Windows.DriverKit.BuildTools" in args_defaults.package

    def test_host_arch_in_architecture(self, sample_packages, args_defaults):
        args_defaults.architecture = ["host"]
        args_defaults.host_arch = "arm64"
        vs.setPackageSelection(args_defaults, sample_packages)
        assert "arm64" in args_defaults.architecture


class TestAggregateDepends:
    def test_simple_dependency(self, sample_packages, args_defaults):
        included = {}
        args_defaults.only_host = False
        result = vs.aggregateDepends(sample_packages, included,
                                     "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", {}, args_defaults)
        assert len(result) == 1
        assert result[0]["id"] == "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"

    def test_ignored_package(self, sample_packages):
        class Args:
            pass
        a = Args()
        a.ignore = ["microsoft.visualstudio.component.vc.tools.x86.x64"]
        a.only_host = False
        a.host_arch = None
        a.include_optional = False
        a.skip_recommended = False
        included = {}
        result = vs.aggregateDepends(sample_packages, included,
                                     "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", {}, a)
        assert result == []

    def test_deduplication(self, sample_packages):
        class Args:
            pass
        a = Args()
        a.ignore = []
        a.only_host = False
        a.host_arch = None
        a.include_optional = False
        a.skip_recommended = False
        included = {}
        # Add same package twice; first call populates included, second sees it already there.
        vs.aggregateDepends(sample_packages, included,
                            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", {}, a)
        result2 = vs.aggregateDepends(sample_packages, included,
                                      "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", {}, a)
        assert len(result2) == 0  # Already included

    def test_workload_with_deps(self, sample_packages):
        class Args:
            pass
        a = Args()
        a.ignore = []
        a.only_host = False
        a.host_arch = None
        a.include_optional = False
        a.skip_recommended = False
        included = {}
        result = vs.aggregateDepends(sample_packages, included,
                                     "Microsoft.VisualStudio.Workload.VCTools", {}, a)
        # Should include workload + its deps (but not Recommended ones when skip_recommended=False)
        ids = [p["id"] for p in result]
        assert "Microsoft.VisualStudio.Workload.VCTools" in ids
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in ids
        # Recommended dep should be included by default
        assert "Microsoft.VisualStudio.Component.VC.ATL" in ids


class TestGetSelectedPackages:
    def test_selects_packages(self, sample_packages, args_defaults):
        args_defaults.package = ["Microsoft.VisualStudio.Component.VC.Tools.x86.x64"]
        args_defaults.only_host = False
        result = vs.getSelectedPackages(sample_packages, args_defaults)
        assert len(result) >= 1
        ids = [p["id"] for p in result]
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in ids

    def test_selects_workload(self, sample_packages, args_defaults):
        args_defaults.package = ["Microsoft.VisualStudio.Workload.VCTools"]
        args_defaults.only_host = False
        result = vs.getSelectedPackages(sample_packages, args_defaults)
        ids = [p["id"] for p in result]
        assert "Microsoft.VisualStudio.Workload.VCTools" in ids
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in ids


class TestPrintDepends:
    def test_prints_dependency_tree(self, sample_packages, args_defaults, capsys):
        vs.printDepends(sample_packages, "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", {}, "", args_defaults)
        captured = capsys.readouterr()
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in captured.out

    def test_ignored_package(self, sample_packages, args_defaults, capsys):
        args_defaults.ignore = ["microsoft.visualstudio.component.vc.tools.x86.x64"]
        vs.printDepends(sample_packages, "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", {}, "", args_defaults)
        captured = capsys.readouterr()
        assert "Ignored" in captured.out


class TestPrintReverseDepends:
    def test_prints_reverse_deps(self, sample_packages, args_defaults, capsys):
        vs.printReverseDepends(sample_packages, "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "", "", args_defaults)
        captured = capsys.readouterr()
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in captured.out

    def test_finds_dependents(self, sample_packages, args_defaults, capsys):
        vs.printReverseDepends(sample_packages, "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "", "", args_defaults)
        captured = capsys.readouterr()
        assert "Microsoft.VisualStudio.Workload.VCTools" in captured.out


class TestPrintPackageList:
    def test_prints_packages(self, sample_packages, capsys):
        selected = [sample_packages["microsoft.visualstudio.component.vc.tools.x86.x64"][0]]
        vs.printPackageList(selected)
        captured = capsys.readouterr()
        assert "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in captured.out
        assert "Component" in captured.out
        assert "MB" in captured.out  # size formatted


class TestMergeTrees:
    def test_nonexistent_src(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "dest")
            os.makedirs(dest)
            vs.mergeTrees(os.path.join(tmp, "nonexistent"), dest)
            # Should not raise

    def test_moves_src_to_dest(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "src")
            dest = os.path.join(tmp, "dest")
            os.makedirs(src)
            open(os.path.join(src, "test.txt"), "w").close()
            vs.mergeTrees(src, dest)
            assert os.path.isfile(os.path.join(dest, "test.txt"))
            assert not os.path.isdir(src)

    def test_merges_into_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "src")
            dest = os.path.join(tmp, "dest")
            os.makedirs(src)
            os.makedirs(dest)
            open(os.path.join(src, "a.txt"), "w").close()
            open(os.path.join(dest, "b.txt"), "w").close()
            vs.mergeTrees(src, dest)
            assert os.path.isfile(os.path.join(dest, "a.txt"))
            assert os.path.isfile(os.path.join(dest, "b.txt"))


class TestCopyDependentAssemblies:
    def test_no_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = os.path.join(tmp, "test.exe")
            open(app, "w").close()
            vs.copyDependentAssemblies(app)
            # Should not raise

    def test_with_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = os.path.join(tmp, "test.exe")
            open(app, "w").close()
            config = app + ".config"
            with open(config, "w") as f:
                f.write('''<?xml version="1.0"?>
<configuration>
  <runtime>
    <assemblyBinding xmlns="urn:schemas-microsoft-com:asm.v1">
      <dependentAssembly>
        <codeBase href="sub/lib.dll"/>
      </dependentAssembly>
    </assemblyBinding>
  </runtime>
</configuration>''')
            subdir = os.path.join(tmp, "sub")
            os.makedirs(subdir)
            lib = os.path.join(subdir, "lib.dll")
            open(lib, "w").close()
            vs.copyDependentAssemblies(app)
            assert os.path.isfile(os.path.join(tmp, "lib.dll"))


class TestMoveVCSDK:
    def test_moves_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            unpack = os.path.join(tmp, "unpack")
            dest = os.path.join(tmp, "dest")
            os.makedirs(os.path.join(unpack, "VC"))
            os.makedirs(os.path.join(unpack, "Windows Kits"))
            os.makedirs(os.path.join(unpack, "Common7", "Tools"))
            os.makedirs(dest)
            vs.moveVCSDK(unpack, dest)
            assert os.path.isdir(os.path.join(dest, "VC"))
            assert os.path.isdir(os.path.join(dest, "Windows Kits"))
            assert os.path.isdir(os.path.join(dest, "Common7", "Tools"))


class TestUnzipFiltered:
    def test_simple_extract(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "test.zip")
            dest = os.path.join(tmp, "out")
            os.makedirs(dest)
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("hello.txt", "world")
                z.writestr("sub/deep/file.txt", "nested")
            with zipfile.ZipFile(zip_path, "r") as z:
                vs.unzipFiltered(z, dest)
            assert os.path.isfile(os.path.join(dest, "hello.txt"))
            assert open(os.path.join(dest, "hello.txt")).read() == "world"
            assert os.path.isfile(os.path.join(dest, "sub", "deep", "file.txt"))

    def test_url_encoded_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "test.zip")
            dest = os.path.join(tmp, "out")
            os.makedirs(dest)
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("file%20name.txt", "spaces")
            with zipfile.ZipFile(zip_path, "r") as z:
                vs.unzipFiltered(z, dest)
            assert os.path.isfile(os.path.join(dest, "file name.txt"))

    def test_dir_structure_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "test.zip")
            dest = os.path.join(tmp, "out")
            os.makedirs(dest)
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("a/b/c/d.txt", "deeply")
                z.writestr("a/b/e.txt", "shallow")
            with zipfile.ZipFile(zip_path, "r") as z:
                vs.unzipFiltered(z, dest)
            assert os.path.isfile(os.path.join(dest, "a", "b", "c", "d.txt"))
            assert os.path.isfile(os.path.join(dest, "a", "b", "e.txt"))


class TestUnpackVsix:
    def test_basic_vsix(self):
        with tempfile.TemporaryDirectory() as tmp:
            vsix_path = os.path.join(tmp, "test.vsix")
            dest = os.path.join(tmp, "out")
            os.makedirs(dest)
            with zipfile.ZipFile(vsix_path, "w") as z:
                z.writestr("extension.vsixmanifest", "<xml/>")
                z.writestr("[Content_Types].xml", "<xml/>")
            listing = os.path.join(dest, "listing.txt")
            vs.unpackVsix(vsix_path, dest, listing)
            # Files extracted to temp, then if no Contents/ or $MSBuild/ dirs, temp is cleaned
            assert not os.path.isdir(os.path.join(dest, "vsix"))
            # Listing file written
            assert os.path.isfile(listing)
            content = open(listing).read()
            assert "extension.vsixmanifest" in content
            assert "[Content_Types].xml" in content

    def test_vsix_with_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            vsix_path = os.path.join(tmp, "test.vsix")
            dest = os.path.join(tmp, "out")
            os.makedirs(dest)
            # Create a VSIX with Contents/ directory that should be merged to root
            with zipfile.ZipFile(vsix_path, "w") as z:
                z.writestr("Contents/", "")
                z.writestr("Contents/SubDir/file.dll", "binary")
            listing = os.path.join(dest, "listing.txt")
            vs.unpackVsix(vsix_path, dest, listing)
            # Contents/SubDir/file.dll should be merged to dest/SubDir/file.dll
            assert os.path.isfile(os.path.join(dest, "SubDir", "file.dll"))
            # Temp cleaned
            assert not os.path.isdir(os.path.join(dest, "vsix"))

    def test_vsix_with_msbuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            vsix_path = os.path.join(tmp, "test.vsix")
            dest = os.path.join(tmp, "out")
            os.makedirs(dest)
            with zipfile.ZipFile(vsix_path, "w") as z:
                z.writestr("$MSBuild/", "")
                z.writestr("$MSBuild/Tasks/bin/task.dll", "msbuild task")
            listing = os.path.join(dest, "listing.txt")
            vs.unpackVsix(vsix_path, dest, listing)
            # $MSBuild contents should go to dest/MSBuild/
            assert os.path.isfile(os.path.join(dest, "MSBuild", "Tasks", "bin", "task.dll"))
            assert not os.path.isdir(os.path.join(dest, "vsix"))


class TestUnpackWin10SDK:
    def test_creates_program_files_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "cache")
            dest = os.path.join(tmp, "out")
            os.makedirs(src)
            os.makedirs(dest)
            payloads = [{"fileName": "sdksetup.msi", "size": 1000}]
            vs.unpackWin10SDK(src, payloads, dest)
            # Symlink Program Files -> . should exist
            pf = os.path.join(dest, "Program Files")
            assert os.path.islink(pf)
            assert os.readlink(pf) == "."

    def test_skips_symlink_if_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "cache")
            dest = os.path.join(tmp, "out")
            os.makedirs(src)
            os.makedirs(dest)
            # Create Program Files as real dir first
            os.makedirs(os.path.join(dest, "Program Files"))
            payloads = [{"fileName": "sdksetup.msi", "size": 1000}]
            vs.unpackWin10SDK(src, payloads, dest)
            pf = os.path.join(dest, "Program Files")
            assert os.path.isdir(pf)
            assert not os.path.islink(pf)

    def test_skips_non_msi_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "cache")
            dest = os.path.join(tmp, "out")
            os.makedirs(src)
            os.makedirs(dest)
            payloads = [
                {"fileName": "sdksetup.msi", "size": 1000},
                {"fileName": "cab1.cab", "size": 500},
            ]
            vs.unpackWin10SDK(src, payloads, dest)
            # Should only have tried to extract the .msi (fail gracefully
            # because sdksetup.msi doesn't exist in src, no cab attempt)
            pf = os.path.join(dest, "Program Files")
            assert os.path.islink(pf)

    def test_creates_listing_file_on_msi_extract(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "cache")
            dest = os.path.join(tmp, "out")
            os.makedirs(src)
            os.makedirs(dest)
            # Create a dummy .msi file so check_call runs
            msi_path = os.path.join(src, "sdksetup.msi")
            open(msi_path, "w").close()
            payloads = [{"fileName": "sdksetup.msi", "size": 1000}]
            # Mock subprocess.check_call to avoid actually running msiextract
            calls = []
            monkeypatch.setattr(
                vs.subprocess,
                "check_call",
                lambda cmd, stdout: calls.append((cmd, stdout.name)),
            )
            vs.unpackWin10SDK(src, payloads, dest)
            # Listing file should exist
            listing = os.path.join(dest, "WinSDK-sdksetup.msi-listing.txt")
            assert os.path.isfile(listing)
            # check_call was called with msiextract command
            assert len(calls) == 1
            cmd, log_path = calls[0]
            assert cmd[0] == "msiextract"
            assert cmd[1] == "-C"
            assert cmd[2] == dest
            assert cmd[3] == msi_path
