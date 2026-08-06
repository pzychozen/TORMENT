import asyncio
import sys

import pytest


def _torment_module_names():
    return {
        name
        for name in sys.modules
        if name == "torment_service" or name.startswith("torment_service.")
    }


@pytest.fixture(autouse=True)
def _restore_torment_imports_after_test():
    before = _torment_module_names()
    yield
    appmod = sys.modules.get("torment_service.app")
    if appmod is not None and "torment_service.app" not in before:
        fabric = getattr(appmod, "fabric", None)
        if fabric is not None:
            fabric.close()
    for name in sorted(_torment_module_names() - before, reverse=True):
        sys.modules.pop(name, None)


def test_debug_metrics_exposes_loaded_companion_runtime_flags(monkeypatch):
    import torment_service.app as appmod

    monkeypatch.setattr(appmod._spine_module, "_THINKING_ADVISORY_ENABLE", True)
    monkeypatch.setattr(appmod._thinking_controller_module, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    monkeypatch.setattr(appmod.fabric, "_sqlite_enable", True)
    monkeypatch.setattr(appmod.fabric, "_compress_min_step", 123)
    monkeypatch.setattr(appmod, "DATA_DIR", r"C:\tmp\runtime_integrity_data")
    monkeypatch.setattr(appmod, "TEST_CONDITION", "runtime_test")
    monkeypatch.setattr(appmod, "SERVER_LAUNCHER_PATH", r"C:\tmp\runtime_test_server.cmd")

    data = asyncio.run(appmod.debug_metrics(workspace_id="missing"))
    flags = data["companion_runtime_flags"]
    for name in appmod.CANONICAL_COMPANION_RUNTIME_FLAGS:
        assert name in flags
        assert set(flags[name]) == {"effective_value", "read_timing", "source"}

    assert flags["TORMENT_COGNITION_CORE_SHAPING_V1"]["effective_value"] is True
    assert flags["TORMENT_COGNITION_CORE_SHAPING_V1"]["read_timing"] == "import_time"
    assert flags["TORMENT_SQLITE_INDEX_ENABLE"]["effective_value"] is True
    assert flags["TORMENT_SQLITE_INDEX_ENABLE"]["read_timing"] == "service_start"
    assert flags["TORMENT_COMPRESS_MIN_STEP"]["effective_value"] == 123
    assert flags["TORMENT_TEST_CONDITION"]["effective_value"] == "runtime_test"
    assert flags["TORMENT_DATA_DIR"]["effective_value"] == r"C:\tmp\runtime_integrity_data"
    assert data["features"]["character_enable"] == appmod.fabric._character_enable


def test_import_time_flags_do_not_change_after_environment_mutation(monkeypatch):
    import torment_service.app as appmod

    monkeypatch.setattr(appmod._thinking_controller_module, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    monkeypatch.setenv("TORMENT_COGNITION_CORE_SHAPING_V1", "1")
    monkeypatch.setenv("TORMENT_CONTEXTUAL_ABSTENTION", "0")

    before = appmod.build_companion_runtime_flags()
    monkeypatch.setenv("TORMENT_COGNITION_CORE_SHAPING_V1", "0")
    monkeypatch.setenv("TORMENT_CONTEXTUAL_ABSTENTION", "1")
    after = appmod.build_companion_runtime_flags()

    assert after["TORMENT_COGNITION_CORE_SHAPING_V1"]["effective_value"] == before[
        "TORMENT_COGNITION_CORE_SHAPING_V1"
    ]["effective_value"]
    assert after["TORMENT_COGNITION_CORE_SHAPING_V1"]["effective_value"] is True
    assert after["TORMENT_CONTEXTUAL_ABSTENTION"]["effective_value"] is True
    assert after["TORMENT_CONTEXTUAL_ABSTENTION"]["read_timing"] == "per_request"


def test_every_thinking_shaping_import_flag_is_exposed():
    import torment_service.app as appmod
    import torment_service.thinking_controller as thinking_controller

    discovered = {
        "TORMENT" + attr[: -len("_ENABLE")]
        for attr in dir(thinking_controller)
        if attr.startswith("_")
        and attr.endswith("_ENABLE")
        and ("SHAPING" in attr or "PROMINENCE" in attr or "DIVERSITY" in attr or "GUIDANCE" in attr)
    }
    assert discovered
    assert discovered.issubset(set(appmod.CANONICAL_COMPANION_RUNTIME_FLAGS))
    assert discovered.issubset(set(appmod.build_companion_runtime_flags()))


def test_runtime_integrity_tests_do_not_rebind_spine_response_identity():
    import torment_service.app as appmod
    import torment_service.spine as parent_spine
    from torment_service.spine import SpineResponse as parent_spine_response

    before = parent_spine.SpineResponse
    assert before is parent_spine_response

    appmod.build_companion_runtime_flags()

    from torment_service.spine import SpineResponse as after

    assert parent_spine.SpineResponse is before
    assert after is before
