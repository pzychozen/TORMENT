"""Independent order-sensitive synthetic-validation runner v0.1 (Stage S3A).

Offline, quarantined, deterministic, integer-exact, single-process, single-threaded.
Standard-library only except importing the frozen Stage S2 descriptor module.
Import-inert: importing this module reads no manifest, evaluates no fixture, executes
no descriptor, runs no subprocess, creates no filesystem output, and builds no control
plan eagerly.

This build contains the COMPLETE future non-circular S3B binding/execution route. The
runner is not permanently incapable of execution: it resolves the future runner and
runner-test identities from a machine-readable binding block embedded in the committed
S3B execution-authorization document, and compares an independently computed
configuration identity against that block. A later docs-only S3B commit enables this
unchanged runner. Stage S3A execution remains unauthorized by policy: with the S3B
document absent, the authoritative path fails closed at pre-contact before any real
manifest byte could be read.

The nuisance controls use an exact sparse-support reference kernel (Method B): every
group element is materialized, its observed canonical vector is recomputed
independently by the sparse kernel, and it is compared exactly against a theorem-derived
expectation from the base member. Base canonical signatures are computed once per
admitted sequence; per-member signature invariance is proven by exact witness transport,
not by recomputing all 32 unit minima. No descriptor tensor/normalization/orbit helper
is reused; no float enters any path.
"""

import ast
import hashlib
import json
import math
import os
import subprocess
import sys

import independent_order_sensitive_descriptor_v0_1 as descriptor

N = 64

# --------------------------------------------------------------------------- #
# Frozen identities and inert manifest constants
# --------------------------------------------------------------------------- #

DESCRIPTOR_IDENTITY = {
    "path": "research/brainvision/independent_order_sensitive_descriptor_v0_1.py",
    "git_blob": "f9a369e6c7f09204092155b99638f8cec4e8b1ae",
    "raw_sha256": "cdd313a0dfc3c71b33c4b9964397a5d0710427d612b4d781a46353a4d2522be9",
}
DESCRIPTOR_TEST_IDENTITY = {
    "path": "research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py",
    "git_blob": "9054b36aebf32014053d2a877b0cb7eb42dce6fc",
    "raw_sha256": "3eed5c7e482bad65ab662941bc3b3bc04477e9669ae6e067d93bea4e524f3a94",
}
RUNNER_PATH = "research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py"
RUNNER_TEST_PATH = "research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py"

MANIFEST_PATH = (
    "research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/"
    "independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json"
)
EXTERNAL_MANIFEST_SHA256 = "05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404"
MANIFEST_PAYLOAD_SHA256 = "56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9"
FREEZE_CONFIGURATION_SHA256 = "5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263"
EXPECTED_MANIFEST_SCHEMA = (
    "torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-manifest-v0.1"
)

REQUIRED_PYTHON = "3.11.15"

RESULT_KINDS = ("SYNTHETIC_GATE_PASSED", "SYNTHETIC_GATE_FAILED", "SYNTHETIC_GATE_INVALID")
CLASSIFICATIONS = (
    "NO_DECLARED_DISTINCTION",
    "NUISANCE_ORBIT_EQUIVALENT",
    "DECLARED_THIRD_ORDER_DISTINCTION_DETECTED",
)

FAILURE_CODES = descriptor.FAILURE_CODES
_FAILURE_INDEX = {code: i for i, code in enumerate(FAILURE_CODES)}


def ordered_failures(codes):
    unique = {c for c in codes}
    for c in unique:
        if c not in _FAILURE_INDEX:
            raise ValueError("unknown failure code")
    return [c for c in FAILURE_CODES if c in unique]


# --------------------------------------------------------------------------- #
# Frozen authoritative control-plan constants and Method B generator set
# --------------------------------------------------------------------------- #

ROTATION_COUNT = 64
AFFINE_COUNT = 2048
AFFINE_COMPLEMENT_COUNT = 4096
FIXED_POSITIVE_COUNT = 1
GENERATED_POSITIVE_COUNT = 8
PASS_COUNT = 2

GENERATOR_SET = (
    ("G0", 1, 0, 1),
    ("G1", 1, 1, 1),
    ("G2", 3, 0, 1),
    ("G3", 63, 0, 1),
    ("G4", 1, 0, -1),
)

_UNITS = tuple(u for u in range(1, N) if math.gcd(u, N) == 1)
_UNIT_INV = {u: pow(u, -1, N) for u in _UNITS}
_LAG_DOMAIN = tuple((a, b) for a in range(1, N) for b in range(1, N) if a != b)
_LAG_INDEX = {ab: i for i, ab in enumerate(_LAG_DOMAIN)}
_PERM_CACHE = {}
_PLAN_CACHE = {}


def _unit_permutation(u):
    ui = _UNIT_INV[u]
    return tuple(_LAG_INDEX[((ui * a) % N, (ui * b) % N)] for (a, b) in _LAG_DOMAIN)


def _perms():
    if not _PERM_CACHE:
        _PERM_CACHE["by_unit"] = {u: _unit_permutation(u) for u in _UNITS}
    return _PERM_CACHE["by_unit"]


def authoritative_control_plan():
    """Frozen authoritative control plan (lazy, cached). Cardinalities equal the frozen
    constants and cannot be reduced through any external input."""
    if not _PLAN_CACHE:
        _PLAN_CACHE["plan"] = {
            "rotations": tuple((1, v, 1) for v in range(N)),
            "reflection": (63, 0, 1),
            "affine": tuple((u, v, 1) for u in _UNITS for v in range(N)),
            "self_orbit": tuple((u, v, s) for u in _UNITS for v in range(N) for s in (1, -1)),
            "authoritative": True,
        }
    return _PLAN_CACHE["plan"]


# --------------------------------------------------------------------------- #
# S3B machine-readable binding block (parsed from the committed S3B document)
# --------------------------------------------------------------------------- #

S3B_AUTHORIZATION_PATH = (
    "docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md"
)
BINDING_BEGIN = "BEGIN-SYNTHETIC-VALIDATION-EXECUTION-AUTHORIZATION-BINDING-v0.1"
BINDING_END = "END-SYNTHETIC-VALIDATION-EXECUTION-AUTHORIZATION-BINDING-v0.1"
BINDING_SCHEMA = (
    "torment-brainvision-independent-order-sensitive-synthetic-validation-execution-authorization-v0.1"
)
BINDING_VERSION = "0.1"
BINDING_FIELDS = (
    "authorization_schema",
    "authorization_version",
    "runner_git_blob",
    "runner_raw_sha256",
    "runner_test_git_blob",
    "runner_test_raw_sha256",
    "configuration_sha256",
)
_HEX40 = {"runner_git_blob", "runner_test_git_blob"}
_HEX64 = {"runner_raw_sha256", "runner_test_raw_sha256", "configuration_sha256"}


def _valid_hex(value, length):
    return isinstance(value, str) and len(value) == length and all(
        c in "0123456789abcdef" for c in value)


def _outside_binding_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if stripped in (BINDING_BEGIN, BINDING_END):
        return True
    if "=" not in stripped:
        return False
    key, sep, _value = stripped.partition("=")
    return sep == "=" and key.strip() in BINDING_FIELDS


def parse_binding_block(document_text):
    """Strict bounded parser for the single S3B machine-binding block.

    Returns (binding_dict_or_None, failure_codes). Rejects missing/duplicate markers,
    missing/duplicate/extra/out-of-order fields, whitespace ambiguity, invalid hex
    length, invalid schema/version, and trailing machine-binding content. Pure string
    parsing; the document is never imported, executed, or evaluated.
    """
    lines = document_text.split("\n")
    begins = [i for i, ln in enumerate(lines) if ln == BINDING_BEGIN]
    ends = [i for i, ln in enumerate(lines) if ln == BINDING_END]
    if len(begins) != 1 or len(ends) != 1 or ends[0] <= begins[0]:
        return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    outside = lines[:begins[0]] + lines[ends[0] + 1:]
    if any(_outside_binding_line(line) for line in outside):
        return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    body = lines[begins[0] + 1:ends[0]]
    if len(body) != len(BINDING_FIELDS):
        return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    parsed = {}
    for idx, line in enumerate(body):
        # exact "key=value", no surrounding whitespace, single '=' delimiter.
        if line != line.strip() or line.count("=") != 1:
            return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
        key, _, value = line.partition("=")
        if key != BINDING_FIELDS[idx]:
            return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
        if key in parsed:
            return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
        if value != value.strip() or value == "":
            return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
        parsed[key] = value
    if parsed["authorization_schema"] != BINDING_SCHEMA:
        return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    if parsed["authorization_version"] != BINDING_VERSION:
        return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    for field in _HEX40:
        if not _valid_hex(parsed[field], 40):
            return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    for field in _HEX64:
        if not _valid_hex(parsed[field], 64):
            return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    return (parsed, [])


# --------------------------------------------------------------------------- #
# Runner-owned static source boundary scanner
# --------------------------------------------------------------------------- #

def _frag(*parts):
    return "".join(parts)


def _merge_constant_sets(left, right, combiner):
    if left is None or right is None:
        return None
    out = set()
    for a in left:
        for b in right:
            try:
                out.add(combiner(a, b))
            except TypeError:
                return None
    return frozenset(out)


def _const_values(node, constants, aliases):
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes, int)):
        return frozenset({node.value})
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _merge_constant_sets(
            _const_values(node.left, constants, aliases),
            _const_values(node.right, constants, aliases),
            lambda a, b: a + b)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return _merge_constant_sets(
            _const_values(node.left, constants, aliases),
            _const_values(node.right, constants, aliases),
            lambda a, b: a % b)
    if isinstance(node, ast.JoinedStr):
        values = frozenset({""})
        for piece in node.values:
            if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                part = frozenset({piece.value})
            elif isinstance(piece, ast.FormattedValue):
                raw = _const_values(piece.value, constants, aliases)
                part = None if raw is None else frozenset(str(value) for value in raw)
            else:
                part = None
            values = _merge_constant_sets(values, part, lambda a, b: a + b)
            if values is None:
                return None
        return values
    if isinstance(node, (ast.Tuple, ast.List)):
        values = [tuple(_const_values(elt, constants, aliases) or ()) for elt in node.elts]
        if any(not item for item in values):
            return None
        out = [()]
        for item_values in values:
            out = [prefix + (item,) for prefix in out for item in item_values]
        return frozenset(out)
    if isinstance(node, ast.Dict):
        pairs = []
        for key, value in zip(node.keys, node.values):
            key_values = _const_values(key, constants, aliases)
            value_values = _const_values(value, constants, aliases)
            if key_values is None or value_values is None:
                return None
            pairs.append((tuple(key_values), tuple(value_values)))
        out = [()]
        for key_values, value_values in pairs:
            out = [prefix + ((k, v),) for prefix in out for k in key_values for v in value_values]
        return frozenset(out)
    if isinstance(node, ast.Call):
        chain = _chain_name(node.func, aliases)
        if chain == "str" and len(node.args) == 1:
            raw = _const_values(node.args[0], constants, aliases)
            return None if raw is None else frozenset(str(value) for value in raw)
        if chain in {"os.path.join", "pathlib.PurePath", "pathlib.Path", "PurePath", "Path"}:
            pieces = [_const_values(arg, constants, aliases) for arg in node.args]
            if any(piece is None for piece in pieces):
                return None
            out = frozenset({""})
            for piece in pieces:
                out = _merge_constant_sets(
                    out, piece,
                    lambda a, b: (str(b) if str(a) == "" else str(a).rstrip("/\\") + "/" + str(b).strip("/\\")))
            return out
        if isinstance(node.func, ast.Attribute) and node.func.attr == "join":
            sep_values = _const_values(node.func.value, constants, aliases)
            member_values = _const_values(node.args[0], constants, aliases) if node.args else None
            if sep_values is None or member_values is None:
                return None
            out = set()
            for sep in sep_values:
                for members in member_values:
                    if not isinstance(members, tuple):
                        return None
                    out.add(str(sep).join(str(item) for item in members))
            return frozenset(out)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            template_values = _const_values(node.func.value, constants, aliases)
            arg_values = [_const_values(arg, constants, aliases) for arg in node.args]
            if template_values is None or any(value is None for value in arg_values):
                return None
            out = set()
            for template in template_values:
                if not isinstance(template, str):
                    return None
                partial = {template}
                for values in arg_values:
                    next_partial = set()
                    for item in values:
                        for candidate in partial:
                            next_partial.add(candidate.format(item))
                    partial = next_partial
                out.update(partial)
            return frozenset(out)
    return None


def _source_text(node, constants):
    values = _const_values(node, constants, {})
    if values and len(values) == 1:
        value = next(iter(values))
        if isinstance(value, str):
            return value
    return None


def _chain_name(node, aliases, constants=None):
    constants = constants or {}
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _chain_name(node.value, aliases, constants)
        return (base + "." + node.attr) if base else node.attr
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":
        if len(node.args) >= 2:
            base = _chain_name(node.args[0], aliases, constants)
            attr_values = _const_values(node.args[1], constants, aliases)
            if base and attr_values and len(attr_values) == 1:
                attr = next(iter(attr_values))
                if isinstance(attr, str):
                    return base + "." + attr
    return None


def _enclosing_function_node(node):
    parent = getattr(node, "_parent", None)
    while parent is not None:
        if isinstance(parent, ast.FunctionDef):
            return parent
        parent = getattr(parent, "_parent", None)
    return None


def _enclosing_function(node):
    func = _enclosing_function_node(node)
    return None if func is None else func.name


_BOUNDARY_SCANNER_FUNCTIONS = frozenset({
    "_frag", "_merge_constant_sets", "_const_values", "_source_text",
    "_chain_name", "_enclosing_function_node", "_enclosing_function",
    "_chain_matches", "_normalize_repo_path", "_publication_filenames",
    "_publication_paths", "_text_leaf_values", "_append_text_findings",
    "_scan_text_values", "_scan_path_values", "_scan_import_values", "_mode_texts",
    "_function_has_identity_guard", "_open_call_allowed", "_os_call_allowed",
    "_call_path_texts", "_function_has_exact_publication_shape",
    "_subprocess_call_allowed", "_sensitive_keyword_findings",
    "_source_boundary_markers", "_source_boundary_allowed_strings", "_collect_source_boundary_context",
    "source_boundary_findings", "source_boundary_pass",
})


def _source_boundary_markers():
    return {
        "forbidden_import_roots": {
            _frag("sock", "et"), _frag("request", "s"), _frag("url", "lib"),
            _frag("ht", "tp"), _frag("import", "lib"), _frag("path", "lib"),
            _frag("cty", "pes"), _frag("num", "py"), _frag("torment_", "service"),
            _frag("kernel"), _frag("psi", "_trs"), _frag("psi", "trs"),
        },
        "forbidden_attrs": {
            _frag("envi", "ron"), _frag("get", "env"), _frag("Pop", "en"),
            _frag("url", "open"), _frag("read_text"), _frag("write_text"),
            _frag("read_bytes"), _frag("write_bytes"), _frag("capture"),
            _frag("screenshot"),
        },
        "forbidden_calls": {
            "__" + "import" + "__", _frag("ev", "al"), _frag("ex", "ec"),
            _frag("comp", "ile"),
        },
        "forbidden_text": {
            _frag("torment_", "service"), _frag("memory_", "kernel"),
            _frag("trioctamemory", "kernel"), _frag("psi", "_trs"),
            _frag("psi", "trs"), _frag("f3_", "evaluator"),
            _frag("f3_", "asymmetry"), _frag("asymmetry_", "audit"),
            _frag("algebraic_n64_", "f3"), _frag("candidate_", "478"),
            _frag("candidate_", "479"), _frag("candidate_", "480"),
            _frag("retained_", "evidence"), _frag("retained_", "family"),
            _frag("historical_", "f3"), _frag("historical", "f3"),
            _frag("camera"), _frag("screen", "capture"), _frag("screenshot"),
        },
    }


def _source_boundary_allowed_strings():
    return {
        RUNNER_PATH, RUNNER_TEST_PATH, DESCRIPTOR_IDENTITY["path"],
        DESCRIPTOR_TEST_IDENTITY["path"], S3B_AUTHORIZATION_PATH, MANIFEST_PATH,
        FINAL_DIRECTORY, STAGING_DIRECTORY, RESULT_FILENAME, ENVELOPE_FILENAME,
        SUMMARY_FILENAME, EXTERNAL_MANIFEST_SHA256, MANIFEST_PAYLOAD_SHA256,
        FREEZE_CONFIGURATION_SHA256, EXPECTED_MANIFEST_SCHEMA, BINDING_BEGIN,
        BINDING_END, BINDING_SCHEMA,
    }


def _collect_source_boundary_context(tree):
    aliases = {}
    constants = {}

    def remember(name, values):
        if values is None:
            constants[name] = None
        elif name in constants and constants[name] is not None:
            constants[name] = constants[name] | values
        else:
            constants[name] = values

    def assign_target(target, values):
        if isinstance(target, ast.Name):
            remember(target.id, values)
        elif isinstance(target, (ast.Tuple, ast.List)) and values is not None:
            tuple_values = [value for value in values if isinstance(value, tuple)
                            and len(value) == len(target.elts)]
            if not tuple_values:
                for elt in target.elts:
                    assign_target(elt, None)
                return
            for idx, elt in enumerate(target.elts):
                assign_target(elt, frozenset(value[idx] for value in tuple_values))

    def visit_body(body):
        for node in body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".")[0]] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    aliases[alias.asname or alias.name] = module + "." + alias.name
            elif isinstance(node, ast.Assign):
                value_name = _chain_name(node.value, aliases)
                value_values = _const_values(node.value, constants, aliases)
                for target in node.targets:
                    if isinstance(target, ast.Name) and value_name:
                        aliases[target.id] = value_name
                    assign_target(target, value_values)
            elif isinstance(node, ast.AnnAssign):
                value_values = _const_values(node.value, constants, aliases) if node.value else None
                assign_target(node.target, value_values)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit_body(node.body)
            elif isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                visit_body(getattr(node, "body", []))
                visit_body(getattr(node, "orelse", []))
                for handler in getattr(node, "handlers", []):
                    visit_body(handler.body)
                visit_body(getattr(node, "finalbody", []))

    visit_body(tree.body)
    return aliases, constants


def _chain_matches(low_chain, attr):
    return low_chain == attr or low_chain.endswith("." + attr)


def _normalize_repo_path(text):
    raw = str(text).replace("\\", "/")
    if raw.startswith("/") or raw.startswith("//") or (len(raw) >= 2 and raw[1] == ":"):
        return None
    parts = []
    for part in raw.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return None
        parts.append(part)
    return "/".join(parts)


def _publication_filenames():
    return frozenset({RESULT_FILENAME, ENVELOPE_FILENAME, SUMMARY_FILENAME})


def _publication_paths():
    return frozenset(
        _normalize_repo_path(os.path.join(STAGING_DIRECTORY, name))
        for name in _publication_filenames())


def _text_leaf_values(values):
    if values is None:
        return None
    out = set()

    def add(value):
        if isinstance(value, bytes):
            try:
                out.add(value.decode("utf-8"))
            except UnicodeDecodeError:
                return False
        elif isinstance(value, str):
            out.add(value)
        elif isinstance(value, int) and not isinstance(value, bool):
            out.add(str(value))
        elif isinstance(value, tuple):
            for item in value:
                if not add(item):
                    return False
        else:
            return False
        return True

    for value in values:
        if not add(value):
            return None
    return frozenset(out)


def _append_text_findings(findings, text, markers, allowed_strings):
    if text in allowed_strings:
        return 0
    before = len(findings)
    low = str(text).lower().replace("\\", "/")
    if "research/brainvision/results/" in low:
        findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", text))
    for marker in markers["forbidden_text"]:
        if marker in low:
            findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", marker))
    return len(findings) - before


def _scan_text_values(findings, values, markers, allowed_strings, unresolved_label=None):
    texts = _text_leaf_values(values)
    if texts is None:
        if unresolved_label is not None:
            findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", unresolved_label))
        return
    for text in texts:
        _append_text_findings(findings, text, markers, allowed_strings)


def _scan_path_values(findings, values, markers, allowed_strings, unresolved_label=None):
    texts = _text_leaf_values(values)
    if texts is None:
        if unresolved_label is not None:
            findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", unresolved_label))
        return
    for text in texts:
        normalized = _normalize_repo_path(text)
        if normalized is None:
            findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", text))
            continue
        if normalized in _publication_paths():
            continue
        _append_text_findings(findings, text, markers, allowed_strings)


def _scan_import_values(findings, values, markers, allowed_strings, allowed_imports, label):
    texts = _text_leaf_values(values)
    if texts is None:
        findings.append(("FORBIDDEN_IMPORT_DETECTED", label))
        return
    for text in texts:
        root = str(text).split(".")[0].lower()
        if root in markers["forbidden_import_roots"] or root not in allowed_imports:
            findings.append(("FORBIDDEN_IMPORT_DETECTED", text))
        _append_text_findings(findings, text, markers, allowed_strings)


def _mode_texts(node, constants, aliases, mode_index):
    value = None
    if len(node.args) > mode_index:
        value = node.args[mode_index]
    for kw in node.keywords:
        if kw.arg == "mode":
            value = kw.value
    if value is None:
        return frozenset({"r"})
    return _text_leaf_values(_const_values(value, constants, aliases))


def _function_has_identity_guard(func_node, arg_name):
    if func_node is None:
        return False
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Name):
            continue
        if node.left.id != arg_name:
            continue
        if not any(isinstance(op, ast.NotIn) for op in node.ops):
            continue
        for comparator in node.comparators:
            chain = _chain_name(comparator, {})
            if chain and chain.endswith("_IDENTITY_PATHS"):
                return True
    return False


def _call_path_texts(node, constants, aliases, arg_index=0):
    if len(node.args) <= arg_index:
        return None
    return _text_leaf_values(_const_values(node.args[arg_index], constants, aliases))


def _function_has_exact_publication_shape(func_node, constants, aliases):
    if func_node is None:
        return False
    saw_final_absence = False
    saw_staging_listing = False
    saw_exact_replace = False
    for item in ast.walk(func_node):
        if not isinstance(item, ast.Call):
            continue
        chain = _chain_name(item.func, aliases, constants)
        if chain == "os.path.exists":
            saw_final_absence = _call_path_texts(item, constants, aliases) == frozenset({FINAL_DIRECTORY}) \
                or saw_final_absence
        elif chain == "os.listdir":
            saw_staging_listing = _call_path_texts(item, constants, aliases) == frozenset({STAGING_DIRECTORY}) \
                or saw_staging_listing
        elif chain == "os.replace" and len(item.args) >= 2:
            src = _call_path_texts(item, constants, aliases, 0)
            dst = _call_path_texts(item, constants, aliases, 1)
            saw_exact_replace = (src == frozenset({STAGING_DIRECTORY})
                                 and dst == frozenset({FINAL_DIRECTORY})) or saw_exact_replace
    return saw_final_absence and saw_staging_listing and saw_exact_replace


def _open_call_allowed(node, constants, aliases, allowed_strings):
    func_node = _enclosing_function_node(node)
    enclosing = None if func_node is None else func_node.name
    method_call = isinstance(node.func, ast.Attribute)
    mode_index = 0 if method_call else 1
    mode_values = _mode_texts(node, constants, aliases, mode_index)
    if mode_values is None:
        return False
    read_mode = all("r" in mode and not any(flag in mode for flag in "wax+") for mode in mode_values)
    write_mode = all(mode in {"w", "wb", "x", "xb"} for mode in mode_values)
    path_node = node.func.value if method_call else (node.args[0] if node.args else None)
    path_values = _const_values(path_node, constants, aliases) if path_node is not None else None
    path_texts = _text_leaf_values(path_values)
    identity_paths = frozenset({
        RUNNER_PATH, RUNNER_TEST_PATH, DESCRIPTOR_IDENTITY["path"], DESCRIPTOR_TEST_IDENTITY["path"],
    })
    if path_texts is not None:
        normalized = frozenset(_normalize_repo_path(text) for text in path_texts)
        if None in normalized:
            return False
        if normalized.issubset(_publication_paths()):
            return (read_mode or write_mode) \
                and _function_has_exact_publication_shape(func_node, constants, aliases)
        if enclosing == "read_authorization_bytes":
            return path_texts == frozenset({S3B_AUTHORIZATION_PATH}) and read_mode
        if enclosing == "read_manifest_bytes":
            return path_texts == frozenset({MANIFEST_PATH}) and read_mode
        if enclosing == "static_boundaries_pass":
            return path_texts.issubset({RUNNER_PATH, DESCRIPTOR_IDENTITY["path"]}) and read_mode
        if enclosing == "raw_sha256":
            return path_texts.issubset(identity_paths) and read_mode
        return path_texts.issubset(allowed_strings) and read_mode
    if enclosing == "raw_sha256":
        return read_mode and _function_has_identity_guard(func_node, "path")
    if enclosing == "static_boundaries_pass":
        return read_mode
    return False


def _os_call_allowed(chain, node, constants, aliases):
    enclosing = _enclosing_function(node)
    path_values = _const_values(node.args[0], constants, aliases) if node.args else None
    path_texts = _text_leaf_values(path_values)
    normalized = None if path_texts is None else frozenset(_normalize_repo_path(text) for text in path_texts)
    exact_staging = normalized == frozenset({_normalize_repo_path(STAGING_DIRECTORY)})
    exact_final = normalized == frozenset({_normalize_repo_path(FINAL_DIRECTORY)})
    if chain == "os.path.join":
        return True
    if chain == "os.path.isdir":
        return (enclosing == "repo_root_ok" and path_texts == frozenset({".git"})) or exact_staging
    if chain == "os.path.isfile":
        return enclosing == "manifest_is_regular_file" and path_texts == frozenset({MANIFEST_PATH})
    if chain == "os.path.exists":
        return exact_final or exact_staging
    if chain == "os.makedirs":
        return exact_staging
    if chain == "os.listdir":
        return exact_staging and _function_has_exact_publication_shape(
            _enclosing_function_node(node), constants, aliases)
    if chain == "os.replace":
        if len(node.args) < 2:
            return False
        src = _call_path_texts(node, constants, aliases, 0)
        dst = _call_path_texts(node, constants, aliases, 1)
        return src == frozenset({STAGING_DIRECTORY}) and dst == frozenset({FINAL_DIRECTORY}) \
            and _function_has_exact_publication_shape(_enclosing_function_node(node), constants, aliases)
    return False


def _subprocess_call_allowed(chain, node, constants, aliases):
    if chain != "subprocess.run" or _enclosing_function(node) != "_git":
        return False
    values = _const_values(node.args[0], constants, aliases) if node.args else None
    texts = _text_leaf_values(values)
    if texts is None:
        return True
    mutating = {"add", "commit", "push", "reset", "checkout", "merge", "rebase", "clean",
                "pull", "fetch", "switch"}
    return "git" in texts and not any(text in mutating for text in texts)


def _sensitive_keyword_findings(node, findings):
    for kw in node.keywords:
        if kw.arg == "shell":
            findings.append(("PRODUCTION_BOUNDARY_VIOLATION", "shell"))
        if kw.arg in {"dir_fd", "src_dir_fd", "dst_dir_fd"}:
            findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", kw.arg))
        if kw.arg == "follow_symlinks":
            findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", kw.arg))


def source_boundary_findings(source_text, role):
    """Return canonical source-boundary findings for one source text.

    The scanner is intentionally structural. Its own marker declarations are skipped
    to avoid self-boundary false positives while direct literals and assembled routes
    elsewhere remain detectable.
    """
    tree = ast.parse(source_text)
    aliases, constants = _collect_source_boundary_context(tree)
    markers = _source_boundary_markers()
    allowed_imports = {"json", "hashlib", "math"}
    if role == "runner":
        allowed_imports = allowed_imports | {"ast", "os", "sys", "subprocess",
                                             "independent_order_sensitive_descriptor_v0_1"}
    allowed_strings = _source_boundary_allowed_strings()
    findings = []

    def inert_scanner_literal(node):
        if not isinstance(node, ast.Constant):
            return False
        parent = getattr(node, "_parent", None)
        while parent is not None:
            if isinstance(parent, ast.FunctionDef) and parent.name in _BOUNDARY_SCANNER_FUNCTIONS:
                return True
            parent = getattr(parent, "_parent", None)
        return False

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child._parent = parent

    low_level_os = {
        "os.open", "os.fdopen", "os.read", "os.write", "os.pread", "os.pwrite",
        "os.readv", "os.writev", "os.sendfile",
    }
    governed_os = low_level_os | {
        "os.rename", "os.replace", "os.link", "os.symlink", "os.unlink", "os.remove",
        "os.rmdir", "os.mkdir", "os.makedirs", "os.scandir", "os.listdir", "os.walk",
        "os.stat", "os.lstat", "os.access", "os.path.isdir", "os.path.isfile",
        "os.path.exists",
    }
    subprocess_chains = {"subprocess.run", "subprocess.check_output", "subprocess.Popen"}
    mutating_git = {"add", "commit", "push", "reset", "checkout", "merge", "rebase",
                    "clean", "pull", "fetch", "switch"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in markers["forbidden_import_roots"] or root not in allowed_imports:
                    findings.append(("FORBIDDEN_IMPORT_DETECTED", alias.name))
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level and node.level > 0:
                findings.append(("FORBIDDEN_IMPORT_DETECTED", node.module or ""))
            elif root in markers["forbidden_import_roots"] or root not in allowed_imports:
                findings.append(("FORBIDDEN_IMPORT_DETECTED", node.module or ""))
        elif isinstance(node, ast.Call):
            func = node.func
            chain = _chain_name(func, aliases, constants)
            if isinstance(func, ast.Name):
                if func.id in markers["forbidden_calls"]:
                    findings.append(("PRODUCTION_BOUNDARY_VIOLATION", func.id))
                if aliases.get(func.id) == "open":
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", func.id))
            if chain:
                low_chain = chain.lower()
                if low_chain == "__import__" or low_chain.endswith(".__import__") \
                        or low_chain == "importlib.import_module":
                    findings.append(("FORBIDDEN_IMPORT_DETECTED", chain))
                    if node.args:
                        _scan_import_values(findings, _const_values(node.args[0], constants, aliases),
                                            markers, allowed_strings, allowed_imports, chain)
                if any(part in low_chain for part in ("socket", "urlopen", "requests")):
                    findings.append(("PRODUCTION_BOUNDARY_VIOLATION", chain))
                if any(_chain_matches(low_chain, attr) for attr in markers["forbidden_attrs"]):
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", chain))
                if low_chain in subprocess_chains:
                    for arg in node.args:
                        values = _const_values(arg, constants, aliases)
                        _scan_text_values(findings, values, markers, allowed_strings)
                        texts = _text_leaf_values(values)
                        if texts and any(text in mutating_git for text in texts):
                            findings.append(("PRODUCTION_BOUNDARY_VIOLATION", chain))
                    if not _subprocess_call_allowed(low_chain, node, constants, aliases):
                        findings.append(("PRODUCTION_BOUNDARY_VIOLATION", chain))
                if any(_chain_matches(low_chain, attr)
                       for attr in ("read_text", "read_bytes", "write_text", "write_bytes")):
                    target = func.value if isinstance(func, ast.Attribute) else None
                    _scan_text_values(findings, _const_values(target, constants, aliases),
                                      markers, allowed_strings, chain)
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", chain))
                if low_chain in governed_os:
                    os_allowed = _os_call_allowed(low_chain, node, constants, aliases)
                    for arg in node.args:
                        _scan_path_values(findings, _const_values(arg, constants, aliases),
                                          markers, allowed_strings)
                    if low_chain in low_level_os or not os_allowed:
                        findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", chain))
            open_like = (isinstance(func, ast.Name) and func.id == "open") \
                or (isinstance(func, ast.Attribute) and func.attr == "open")
            if open_like:
                open_allowed = _open_call_allowed(node, constants, aliases, allowed_strings)
                path_node = func.value if isinstance(func, ast.Attribute) else (node.args[0] if node.args else None)
                _scan_path_values(findings, _const_values(path_node, constants, aliases),
                                  markers, allowed_strings, None if open_allowed else "open")
                if not open_allowed:
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", "open"))
            if isinstance(func, ast.Name) and func.id == "getattr":
                if len(node.args) >= 2:
                    attr_values = _const_values(node.args[1], constants, aliases)
                    _scan_text_values(findings, attr_values, markers, allowed_strings, "getattr")
                    attr_texts = _text_leaf_values(attr_values)
                    if attr_texts:
                        for attr in attr_texts:
                            low_attr = attr.lower()
                            if low_attr in markers["forbidden_attrs"] or low_attr in {
                                    "open", "fdopen", "read", "write", "pread", "pwrite", "run", "popen",
                                    "replace", "rename", "getenv"}:
                                findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", attr))
                chain = _chain_name(node, aliases, constants)
                if chain and any(piece in chain.lower()
                                 for piece in ("environ", "getenv", "import", "popen", "run")):
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", chain))
            if isinstance(func, ast.Name) and func.id == "setattr":
                findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", "setattr"))
                if len(node.args) >= 2:
                    _scan_text_values(findings, _const_values(node.args[1], constants, aliases),
                                      markers, allowed_strings, "setattr")
            _sensitive_keyword_findings(node, findings)
        elif isinstance(node, ast.Attribute):
            chain = _chain_name(node, aliases, constants)
            if chain:
                low_chain = chain.lower()
                if any(_chain_matches(low_chain, attr) for attr in markers["forbidden_attrs"]):
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", chain))
                if low_chain in low_level_os:
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", chain))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if inert_scanner_literal(node):
                continue
            value = node.value
            low = value.lower()
            if value in allowed_strings:
                continue
            if "research/brainvision/results/" in low:
                findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", value))
            for marker in markers["forbidden_text"]:
                if marker in low:
                    findings.append(("PROHIBITED_EVIDENCE_CONTACT_DETECTED", marker))
    return findings


def source_boundary_pass(runner_source, descriptor_source):
    return (source_boundary_findings(runner_source, "runner") == []
            and source_boundary_findings(descriptor_source, "descriptor") == [])


# --------------------------------------------------------------------------- #
# Independently computed configuration identity
# --------------------------------------------------------------------------- #

def configuration_identity():
    """Immutable canonical configuration payload built from the runner's frozen
    constants. The S3B binding records the SHA-256 of this payload."""
    return {
        "configuration_schema":
            "torment-brainvision-independent-order-sensitive-synthetic-validation-configuration-v0.1",
        "descriptor_identity": DESCRIPTOR_IDENTITY,
        "descriptor_test_identity": DESCRIPTOR_TEST_IDENTITY,
        "runner_path": RUNNER_PATH,
        "runner_test_path": RUNNER_TEST_PATH,
        "manifest_path": MANIFEST_PATH,
        "external_manifest_sha256": EXTERNAL_MANIFEST_SHA256,
        "manifest_payload_sha256": MANIFEST_PAYLOAD_SHA256,
        "freeze_configuration_sha256": FREEZE_CONFIGURATION_SHA256,
        "expected_manifest_schema": EXPECTED_MANIFEST_SCHEMA,
        "required_python": REQUIRED_PYTHON,
        "control_plan_counts": [ROTATION_COUNT, AFFINE_COUNT, AFFINE_COMPLEMENT_COUNT,
                                FIXED_POSITIVE_COUNT, GENERATED_POSITIVE_COUNT, PASS_COUNT],
        "generator_set": [[g[1], g[2], g[3]] for g in GENERATOR_SET],
        "result_kinds": list(RESULT_KINDS),
        "classifications": list(CLASSIFICATIONS),
        "failure_vocabulary": list(FAILURE_CODES),
        "s3b_authorization_path": S3B_AUTHORIZATION_PATH,
        "binding_schema": BINDING_SCHEMA,
        "binding_version": BINDING_VERSION,
        "final_directory": FINAL_DIRECTORY,
        "staging_directory": STAGING_DIRECTORY,
        "result_filename": RESULT_FILENAME,
        "envelope_filename": ENVELOPE_FILENAME,
        "summary_filename": SUMMARY_FILENAME,
        "canonical_serialization": "utf8-nobom-compact-lf-base10-int-terminal-lf",
        "one_run_contact_threshold": "first-real-manifest-byte",
    }


def configuration_sha256():
    return hashlib.sha256(canonical_bytes(configuration_identity())).hexdigest()


# --------------------------------------------------------------------------- #
# Exact sparse-support reference kernel (independent of the descriptor)
# --------------------------------------------------------------------------- #

def ref_validate(x):
    if not isinstance(x, (list, tuple)) or len(x) != N:
        return ("INPUT_LENGTH_INVALID", "input_validation")
    for value in x:
        if isinstance(value, bool) or not isinstance(value, int):
            return ("INPUT_ELEMENT_TYPE_INVALID", "input_validation")
    for value in x:
        if value != 0 and value != 1:
            return ("INPUT_BINARY_DOMAIN_INVALID", "input_validation")
    total = sum(x)
    if total == 0 or total == N:
        return ("DEGENERATE_SEQUENCE", "input_validation")
    return None


def ref_weight(x):
    return sum(x)


def ref_autocorrelation(x):
    support = [i for i in range(N) if x[i]]
    a2 = [0] * N
    for i in support:
        for j in support:
            a2[(j - i) % N] += 1
    return a2


def ref_transition_table(x):
    counts = [[0, 0], [0, 0]]
    for i in range(N):
        counts[x[i]][x[(i + 1) % N]] += 1
    return [[counts[0][0], counts[0][1]], [counts[1][0], counts[1][1]]]


def _sparse_core(x):
    """Sparse-support exact tensor/denominator for a sequence whose weight is the
    minority weight (w <= 32). Complexity O(w^2 + w^3 + 3906)."""
    w = sum(x)
    support = [i for i in range(N) if x[i]]
    a2 = [0] * N
    for i in support:
        for j in support:
            a2[(j - i) % N] += 1
    c3 = {}
    for i in support:
        rel = [(j - i) % N for j in support]
        for a in rel:
            if a == 0:
                continue
            for b in rel:
                if b == 0 or b == a:
                    continue
                key = (a, b)
                c3[key] = c3.get(key, 0) + 1
    tensor = []
    n3 = N ** 3
    n2w = N * N * w
    tail = 2 * N * w ** 3
    for (a, b) in _LAG_DOMAIN:
        val = n3 * c3.get((a, b), 0) - n2w * (a2[a] + a2[b] + a2[(b - a) % N]) + tail
        tensor.append(val)
    denominator = w * (N - w) ** 3 + (N - w) * w ** 3
    return tensor, denominator


def sparse_tensor(x):
    """Exact labeled tensor and denominator via the minority-support sparse kernel.

    For high-weight members the minority support is taken from the complement:
    y = 1 - x gives T_x = -T_y and D_x = D_y. Runner-local; never calls the descriptor.
    """
    w = sum(x)
    if w > N // 2:
        y = [1 - xi for xi in x]
        tensor_y, denominator = _sparse_core(y)
        return [-t for t in tensor_y], denominator
    return _sparse_core(x)


def ref_canonical(x):
    """Independent (denominator, gcd-reduced numerator tuple) via the sparse kernel."""
    tensor, denominator = sparse_tensor(x)
    if denominator <= 0:
        raise ValueError("NORMALIZATION_INVALID")
    g = denominator
    for t in tensor:
        if t:
            g = math.gcd(g, t if t >= 0 else -t)
    return denominator // g, tuple(t // g for t in tensor)


def _affine_only_with_witness(denominator, numerators):
    perms = _perms()
    best = None
    witness_u = None
    for u in _UNITS:
        cand = tuple(numerators[p] for p in perms[u])
        if best is None or cand < best:
            best = cand
            witness_u = u
    return (denominator, best), witness_u


def _affine_complement_with_witness(denominator, numerators):
    perms = _perms()
    best = None
    witness_u = None
    witness_s = None
    for u in _UNITS:
        permuted = tuple(numerators[p] for p in perms[u])
        for s in (1, -1):
            cand = permuted if s == 1 else tuple(-v for v in permuted)
            if best is None or cand < best:
                best = cand
                witness_u = u
                witness_s = s
    return (denominator, best), witness_u, witness_s


def ref_affine_only_signature(x):
    denom, nums = ref_canonical(x)
    return _affine_only_with_witness(denom, nums)[0]


def ref_affine_complement_signature(x):
    denom, nums = ref_canonical(x)
    return _affine_complement_with_witness(denom, nums)[0]


# --------------------------------------------------------------------------- #
# Transformations and theorem-derived expectations
# --------------------------------------------------------------------------- #

def affine_relabel(x, u, v):
    ui = _UNIT_INV[u]
    return [x[(ui * (j - v)) % N] for j in range(N)]


def complement(x):
    return [1 - xi for xi in x]


def transform(x, u, v, s):
    y = affine_relabel(x, u, v)
    return complement(y) if s == -1 else y


def theorem_expected(base_denominator, base_numerators, u, s):
    perm = _perms()[u]
    permuted = tuple(base_numerators[p] for p in perm)
    if s == -1:
        permuted = tuple(-value for value in permuted)
    return (base_denominator, permuted)


def evaluate_transform(x, u, v, s):
    base_den, base_nums = ref_canonical(x)
    y = transform(x, u, v, s)
    observed = ref_canonical(y)
    expected = theorem_expected(base_den, base_nums, u, s)
    return observed, expected, observed == expected


def _transform_failure_code(u, v, s):
    if s == -1:
        return "COMPLEMENT_ANTISYMMETRY_FAILURE"
    if u == 1:
        return "ROTATION_INVARIANCE_FAILURE"
    if u == 63 and v == 0:
        return "REFLECTION_EQUIVARIANCE_FAILURE"
    return "AFFINE_EQUIVARIANCE_FAILURE"


# --------------------------------------------------------------------------- #
# Method B nuisance controls (sparse kernel + witness transport + memoization)
# --------------------------------------------------------------------------- #

def run_nuisance_controls(x, plan):
    """Evaluate the exhaustive nuisance controls for one admitted valid sequence.

    Base canonical signatures are computed once; each materialized member's observed
    vector is recomputed by the sparse kernel and compared exactly to the theorem
    expectation, and its signature invariance is proven by exact witness transport
    (no per-member 32-unit recanonicalization). Memoization caches only byte-identical
    transformed sequences within this call. Returns an accounting dict including cost.
    """
    base_den, base_nums = ref_canonical(x)
    base_affine, uaff = _affine_only_with_witness(base_den, base_nums)
    base_ac, uac, sac = _affine_complement_with_witness(base_den, base_nums)
    perms = _perms()
    failures = set()

    cost = {
        "sparse_canonical_calls": 1,             # the base
        "full_orbit_canonicalizations": 2,       # base affine-only + base affine-plus-complement
        "dense_tensor_loops": 0,                 # sparse kernel only
        "vector_comparisons": 0,
        "memoized_hits": 0,
    }
    memo = {}

    def observed_of(y):
        key = tuple(y)
        if key in memo:
            cost["memoized_hits"] += 1
            return memo[key]
        value = ref_canonical(y)
        cost["sparse_canonical_calls"] += 1
        memo[key] = value
        return value

    def check(u, v, s):
        y = transform(x, u, v, s)
        obs_den, obs_vec = observed_of(y)
        exp_den, exp_vec = theorem_expected(base_den, base_nums, u, s)
        cost["vector_comparisons"] += 1
        if (obs_den, obs_vec) != (exp_den, exp_vec):
            failures.add(_transform_failure_code(u, v, s))
        # Affine-plus-complement signature invariance via exact witness transport.
        uy = (uac * _UNIT_INV[u]) % N
        sy = sac * s
        transported = tuple((sy * obs_vec[p]) for p in perms[uy])
        cost["vector_comparisons"] += 1
        if obs_den != base_ac[0] or transported != base_ac[1]:
            failures.add("SELF_ORBIT_CANONICALIZATION_FAILURE")
        # Affine-only signature invariance (sign +1 only) via exact witness transport.
        if s == 1:
            uya = (uaff * _UNIT_INV[u]) % N
            transported_aff = tuple(obs_vec[p] for p in perms[uya])
            cost["vector_comparisons"] += 1
            if obs_den != base_affine[0] or transported_aff != base_affine[1]:
                failures.add("SELF_ORBIT_CANONICALIZATION_FAILURE")

    for (u, v, s) in plan["rotations"]:
        check(u, v, s)
    ru, rv, rs = plan["reflection"]
    check(ru, rv, rs)
    for (u, v, s) in plan["affine"]:
        check(u, v, s)
    for (u, v, s) in plan["self_orbit"]:
        check(u, v, s)

    return {
        "rotation_checked": len(plan["rotations"]),
        "reflection_checked": 1,
        "affine_checked": len(plan["affine"]),
        "self_orbit_checked": len(plan["self_orbit"]),
        "failure_codes": ordered_failures(failures),
        "classification": None if failures else "NUISANCE_ORBIT_EQUIVALENT",
        "cost": cost,
    }


def run_generator_set_descriptor_check(x, descriptor_module=descriptor):
    """Directly evaluate the frozen descriptor on the fixed generator set G0..G4."""
    base_den, base_nums = ref_canonical(x)
    failures = set()
    for _label, u, v, s in GENERATOR_SET:
        y = transform(x, u, v, s)
        observed = descriptor_module.raw_labeled_signature(y)
        expected = theorem_expected(base_den, base_nums, u, s)
        if observed[0] != expected[0] or tuple(observed[1]) != expected[1]:
            failures.add(_transform_failure_code(u, v, s))
    return ordered_failures(failures)


# --------------------------------------------------------------------------- #
# Identity, malformed/degenerate, positive controls (injectable descriptor)
# --------------------------------------------------------------------------- #

def run_identity_control(x, descriptor_module=descriptor):
    copy = list(x)
    if (descriptor_module.raw_labeled_signature(x) != descriptor_module.raw_labeled_signature(copy)
            or descriptor_module.affine_only_signature(x) != descriptor_module.affine_only_signature(copy)
            or descriptor_module.affine_plus_complement_signature(x)
            != descriptor_module.affine_plus_complement_signature(copy)):
        return {"classification": None, "failure_codes": ["SYNTHETIC_NEGATIVE_CONTROL_FAILURE"]}
    return {"classification": "NO_DECLARED_DISTINCTION", "failure_codes": []}


def run_malformed_control(sequence, expected_code, descriptor_module=descriptor):
    payload = descriptor_module.descriptor_result(sequence)
    if payload["validation"]["valid"] or payload["ordered_failure_codes"] != [expected_code]:
        return ["SYNTHETIC_NEGATIVE_CONTROL_FAILURE"]
    return []


def _lower_order_matches(m0, m1):
    return (ref_weight(m0) == ref_weight(m1)
            and ref_autocorrelation(m0) == ref_autocorrelation(m1)
            and ref_transition_table(m0) == ref_transition_table(m1))


def run_fixed_positive(fixed_fixture, descriptor_module=descriptor):
    m0 = fixed_fixture["binary_A"]
    m1 = fixed_fixture["binary_B"]
    for member in (m0, m1):
        if ref_validate(member) is not None:
            return {"classification": None, "failure_codes": ["FROZEN_INPUT_IDENTITY_MISMATCH"]}
    if not _lower_order_matches(m0, m1):
        return {"classification": None, "failure_codes": ["LOWER_ORDER_CONTROL_MISMATCH"]}
    certs_ok = bool(fixed_fixture.get("affine_inequivalence_certificate")) \
        and bool(fixed_fixture.get("affine_complement_inequivalence_certificate")) \
        and int(fixed_fixture.get("triple_disagreement_count", 0)) > 0
    if not certs_ok:
        return {"classification": None, "failure_codes": ["SYNTHETIC_POSITIVE_CONTROL_FAILURE"]}
    affine_distinct = (descriptor_module.affine_only_signature(m0)
                       != descriptor_module.affine_only_signature(m1))
    ac_distinct = (descriptor_module.affine_plus_complement_signature(m0)
                   != descriptor_module.affine_plus_complement_signature(m1))
    if affine_distinct and ac_distinct:
        return {"classification": "DECLARED_THIRD_ORDER_DISTINCTION_DETECTED", "failure_codes": []}
    return {"classification": None, "failure_codes": ["SYNTHETIC_POSITIVE_CONTROL_FAILURE"]}


def run_eight_pair_gate(accepted_fixtures, descriptor_module=descriptor):
    if len(accepted_fixtures) != GENERATED_POSITIVE_COUNT:
        return {"distinctions": 0, "failure_codes": ["FROZEN_INPUT_IDENTITY_MISMATCH"], "records": []}
    distinctions = 0
    failures = set()
    records = []
    for fixture in accepted_fixtures:
        m0 = fixture["binary_A"]
        m1 = fixture["binary_B"]
        if ref_validate(m0) is not None or ref_validate(m1) is not None:
            failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
            continue
        if not _lower_order_matches(m0, m1):
            failures.add("LOWER_ORDER_CONTROL_MISMATCH")
            continue
        distinct = (descriptor_module.affine_plus_complement_signature(m0)
                    != descriptor_module.affine_plus_complement_signature(m1))
        if distinct:
            distinctions += 1
        records.append({"family_index": fixture.get("family_index"),
                        "affine_plus_complement_distinct": distinct})
    if not failures and distinctions != GENERATED_POSITIVE_COUNT:
        failures.add("SYNTHETIC_POSITIVE_CONTROL_FAILURE")
    return {"distinctions": distinctions, "failure_codes": ordered_failures(failures), "records": records}


# --------------------------------------------------------------------------- #
# Manifest validation (injected bytes; authoritative real read is gated to S3B)
# --------------------------------------------------------------------------- #

def canonical_bytes(obj):
    text = json.dumps(obj, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return text.encode("utf-8") + b"\n"


def sha256_hex(raw_bytes):
    return hashlib.sha256(raw_bytes).hexdigest()


def _payload_hash_of(manifest):
    payload = {k: v for k, v in manifest.items() if k != "manifest_payload_sha256"}
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def default_manifest_identity():
    return {
        "external_sha256": EXTERNAL_MANIFEST_SHA256,
        "payload_sha256": MANIFEST_PAYLOAD_SHA256,
        "schema": EXPECTED_MANIFEST_SCHEMA,
        "configuration_sha256": FREEZE_CONFIGURATION_SHA256,
    }


def validate_manifest_bytes(raw_bytes, identity=None):
    ident = identity or default_manifest_identity()
    if hashlib.sha256(raw_bytes).hexdigest() != ident["external_sha256"]:
        return (None, ["FROZEN_INPUT_IDENTITY_MISMATCH"])
    try:
        manifest = json.loads(raw_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return (None, ["SERIALIZATION_FAILURE"])
    failures = set()
    if manifest.get("manifest_payload_sha256") != ident["payload_sha256"] \
            or _payload_hash_of(manifest) != ident["payload_sha256"]:
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if manifest.get("schema") != ident["schema"]:
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if (manifest.get("configuration_identity") or {}).get("configuration_sha256") != ident["configuration_sha256"]:
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if manifest.get("family_frozen") is not True:
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if not isinstance(manifest.get("fixed_fixture"), dict):
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    accepted = manifest.get("accepted_fixtures")
    if not isinstance(accepted, list) or len(accepted) != GENERATED_POSITIVE_COUNT:
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    else:
        for fixture in accepted:
            for key in ("binary_A", "binary_B"):
                if ref_validate(fixture.get(key)) is not None:
                    failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if failures:
        return (None, ordered_failures(failures))
    return (manifest, [])


# --------------------------------------------------------------------------- #
# One-run authority state and threshold-wired real read
# --------------------------------------------------------------------------- #

class ExecutionState:
    """Explicit one-run authority state machine. Authority is consumed at the first
    real manifest-byte read and can never be reset within or across invocations."""

    PHASES = ("pre_contact", "contacted", "pass_1_complete", "pass_2_complete",
              "published", "failed_after_contact")

    def __init__(self):
        self.phase = "pre_contact"
        self.authority_consumed = False
        self.manifest_contact_count = 0

    def mark_manifest_read(self):
        if self.manifest_contact_count >= PASS_COUNT:
            raise RuntimeError("UNAUTHORIZED_EXECUTION: no third manifest read")
        self.manifest_contact_count += 1
        self.authority_consumed = True
        if self.phase == "pre_contact":
            self.phase = "contacted"

    def mark_pass_complete(self, pass_number):
        self.phase = "pass_%d_complete" % pass_number

    def mark_published(self):
        self.phase = "published"

    def mark_failed_after_contact(self):
        self.phase = "failed_after_contact"


def authoritative_manifest_read(adapter, state):
    """The single authoritative real-manifest read. Marks authority consumed at the
    exact moment before the first byte is read. Reachable only from the authoritative
    orchestration with a real IO adapter; it takes no caller-supplied path."""
    state.mark_manifest_read()
    return adapter.read_manifest_bytes()


# --------------------------------------------------------------------------- #
# Read-only Git IO adapter (real) and authoritative orchestration
# --------------------------------------------------------------------------- #

class RealIoAdapter:
    """Bounded read-only repository IO used only by the authoritative S3B path.

    All Git calls are fixed-template, read-only, shell=false, with no caller-supplied
    verb, no mutating verb, no environment-supplied identity, and no fallback source.
    Not exercised in Stage S3A (pre-contact refuses first).
    """

    _ALLOWED_GIT = ("rev-parse", "status", "symbolic-ref", "log")
    _IDENTITY_PATHS = frozenset({
        DESCRIPTOR_IDENTITY["path"], DESCRIPTOR_TEST_IDENTITY["path"],
        RUNNER_PATH, RUNNER_TEST_PATH,
    })

    def _git(self, args):
        exact = {
            ("symbolic-ref", "--short", "HEAD"),
            ("status", "--porcelain"),
            ("rev-parse", "HEAD"),
            ("rev-parse", "origin/main"),
            ("log", "-1", "--format=%H", "--", S3B_AUTHORIZATION_PATH),
        }
        identity = {("rev-parse", "HEAD:%s" % path) for path in self._IDENTITY_PATHS}
        frozen = tuple(args)
        if not frozen or frozen[0] not in self._ALLOWED_GIT or frozen not in exact | identity:
            raise ValueError("UNAUTHORIZED_EXECUTION")
        completed = subprocess.run(["git"] + list(frozen), capture_output=True, check=False)
        return completed.stdout.decode("utf-8", "replace").strip()

    def python_version(self):
        return "%d.%d.%d" % sys.version_info[:3]

    def repo_root_ok(self):
        return os.path.isdir(".git")

    def branch(self):
        return self._git(["symbolic-ref", "--short", "HEAD"])

    def clean_tree(self):
        return self._git(["status", "--porcelain"]) == ""

    def head(self):
        return self._git(["rev-parse", "HEAD"])

    def origin_main(self):
        return self._git(["rev-parse", "origin/main"])

    def authorization_latest_commit(self):
        return self._git(["log", "-1", "--format=%H", "--", S3B_AUTHORIZATION_PATH]) or None

    def git_blob(self, path):
        if path not in self._IDENTITY_PATHS:
            raise ValueError("UNAUTHORIZED_EXECUTION")
        return self._git(["rev-parse", "HEAD:%s" % path])

    def raw_sha256(self, path):
        if path not in self._IDENTITY_PATHS:
            raise ValueError("UNAUTHORIZED_EXECUTION")
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    def read_authorization_bytes(self):
        with open(S3B_AUTHORIZATION_PATH, "rb") as handle:
            return handle.read()

    def static_boundaries_pass(self):
        try:
            with open(RUNNER_PATH, "rb") as handle:
                runner_source = handle.read().decode("utf-8")
            with open(DESCRIPTOR_IDENTITY["path"], "rb") as handle:
                descriptor_source = handle.read().decode("utf-8")
            return source_boundary_pass(runner_source, descriptor_source)
        except Exception:
            return False

    def manifest_is_regular_file(self):
        return os.path.isfile(MANIFEST_PATH)

    def final_exists(self):
        return os.path.exists(FINAL_DIRECTORY)

    def staging_exists(self):
        return os.path.exists(STAGING_DIRECTORY)

    def make_staging(self):
        os.makedirs(STAGING_DIRECTORY, exist_ok=False)

    def read_manifest_bytes(self):
        with open(MANIFEST_PATH, "rb") as handle:
            return handle.read()

    def publish_files(self, files):
        publish(STAGING_DIRECTORY, FINAL_DIRECTORY, files, staging_already_created=True)


def authoritative_pre_contact(adapter, argv, stdin_data):
    """Complete fail-closed pre-contact verification. Returns (failures, binding_or_None).
    Performs no manifest read and no output creation."""
    failures = set()
    if list(argv) != []:
        failures.add("UNAUTHORIZED_EXECUTION")
    if stdin_data not in (b"", ""):
        failures.add("UNAUTHORIZED_EXECUTION")
    if adapter.python_version() != REQUIRED_PYTHON:
        failures.add("UNAUTHORIZED_EXECUTION")
    if not adapter.repo_root_ok():
        failures.add("UNAUTHORIZED_EXECUTION")
    if failures:
        # Short-circuit before any Git-dependent check: no subprocess is invoked.
        return ordered_failures(failures), None
    if adapter.branch() != "main" or not adapter.clean_tree():
        failures.add("UNAUTHORIZED_EXECUTION")
    if adapter.head() != adapter.origin_main():
        failures.add("UNAUTHORIZED_EXECUTION")
    latest = adapter.authorization_latest_commit()
    if latest is None or latest != adapter.head():
        failures.add("UNAUTHORIZED_EXECUTION")
    binding = None
    if latest is not None:
        binding, parse_failures = parse_binding_block(
            adapter.read_authorization_bytes().decode("utf-8", "replace"))
        for c in parse_failures:
            failures.add(c)
    if binding is not None and binding["configuration_sha256"] != configuration_sha256():
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    # Source identity resolution and comparison (frozen S2 + bound runner/test).
    if adapter.git_blob(DESCRIPTOR_IDENTITY["path"]) != DESCRIPTOR_IDENTITY["git_blob"] \
            or adapter.raw_sha256(DESCRIPTOR_IDENTITY["path"]) != DESCRIPTOR_IDENTITY["raw_sha256"] \
            or adapter.git_blob(DESCRIPTOR_TEST_IDENTITY["path"]) != DESCRIPTOR_TEST_IDENTITY["git_blob"] \
            or adapter.raw_sha256(DESCRIPTOR_TEST_IDENTITY["path"]) != DESCRIPTOR_TEST_IDENTITY["raw_sha256"]:
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if binding is not None:
        if adapter.git_blob(RUNNER_PATH) != binding["runner_git_blob"] \
                or adapter.raw_sha256(RUNNER_PATH) != binding["runner_raw_sha256"] \
                or adapter.git_blob(RUNNER_TEST_PATH) != binding["runner_test_git_blob"] \
                or adapter.raw_sha256(RUNNER_TEST_PATH) != binding["runner_test_raw_sha256"]:
            failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if not adapter.static_boundaries_pass():
        failures.add("PRODUCTION_BOUNDARY_VIOLATION")
    if not adapter.manifest_is_regular_file():
        failures.add("FROZEN_INPUT_IDENTITY_MISMATCH")
    if adapter.final_exists() or adapter.staging_exists():
        failures.add("UNAUTHORIZED_EXECUTION")
    return ordered_failures(failures), binding


def _run_single_pass(manifest, plan, descriptor_module):
    fixed = run_fixed_positive(manifest["fixed_fixture"], descriptor_module)
    eight = run_eight_pair_gate(manifest["accepted_fixtures"], descriptor_module)
    members = [manifest["fixed_fixture"]["binary_A"], manifest["fixed_fixture"]["binary_B"]]
    for fixture in manifest["accepted_fixtures"]:
        members.extend([fixture["binary_A"], fixture["binary_B"]])
    nuisance_failures = set()
    for member in members:
        acc = run_nuisance_controls(member, plan)
        for c in acc["failure_codes"]:
            nuisance_failures.add(c)
        identity = run_identity_control(member, descriptor_module)
        for c in identity["failure_codes"]:
            nuisance_failures.add(c)
    failures = set(fixed["failure_codes"]) | set(eight["failure_codes"]) | nuisance_failures
    bundle = {
        "schema": "torment-brainvision-independent-order-sensitive-synthetic-validation-pass-v0.1",
        "fixed_positive": fixed,
        "fixed_positive_distinction": fixed["classification"] == "DECLARED_THIRD_ORDER_DISTINCTION_DETECTED",
        "generated_positive": {
            "count": eight["distinctions"],
            "all_eight": eight["distinctions"] == GENERATED_POSITIVE_COUNT and not eight["failure_codes"],
            "records": eight["records"],
        },
        "eight_pair_distinctions": eight["distinctions"],
        "negative_nuisance_controls": {
            "members_checked": len(members),
            "failure_codes": ordered_failures(nuisance_failures),
        },
        "failure_codes": ordered_failures(failures),
    }
    return bundle, ordered_failures(failures)


def run_authoritative(adapter, plan, state, descriptor_module=descriptor, manifest_identity=None):
    """Complete future authoritative operation. Reachable only with a real IO adapter in
    production (main) or an injected adapter in bounded tests. The plan and
    manifest_identity parameters are test-only/internal seams; the CLI always supplies
    the frozen authoritative plan and the frozen real manifest identity."""
    argv = adapter_argv(adapter)
    failures, binding = authoritative_pre_contact(adapter, argv, adapter_stdin(adapter))
    if failures:
        return {"result_kind": None, "failure_codes": failures, "state": state.phase,
                "authority_consumed": state.authority_consumed}
    adapter.make_staging()   # exclusive staging created before any manifest byte is read
    bundles = []
    for pass_number in (1, 2):
        raw = authoritative_manifest_read(adapter, state)   # threshold consumed here
        manifest, mf = validate_manifest_bytes(raw, manifest_identity)
        if mf:
            state.mark_failed_after_contact()
            return {"result_kind": "SYNTHETIC_GATE_INVALID", "failure_codes": mf,
                    "state": state.phase, "authority_consumed": True}
        bundle, _ = _run_single_pass(manifest, plan, descriptor_module)
        bundles.append(bundle)
        state.mark_pass_complete(pass_number)
    if canonical_bytes(bundles[0]) != canonical_bytes(bundles[1]):
        state.mark_failed_after_contact()
        return {"result_kind": "SYNTHETIC_GATE_INVALID", "failure_codes": ["REPLAY_MISMATCH"],
                "state": state.phase, "authority_consumed": True}
    failure_codes = bundles[0]["failure_codes"]
    if failure_codes:
        result_kind = "SYNTHETIC_GATE_INVALID" if _is_invalid(failure_codes) else "SYNTHETIC_GATE_FAILED"
    elif bundles[0]["fixed_positive_distinction"] and bundles[0]["eight_pair_distinctions"] == GENERATED_POSITIVE_COUNT:
        result_kind = "SYNTHETIC_GATE_PASSED"
    else:
        result_kind = "SYNTHETIC_GATE_FAILED"
    try:
        files = build_authoritative_artifacts(adapter, binding, bundles, result_kind, failure_codes, state)
        adapter.publish_files(files)
    except Exception:
        state.mark_failed_after_contact()
        return {"result_kind": "SYNTHETIC_GATE_INVALID",
                "failure_codes": ["SERIALIZATION_FAILURE"],
                "state": state.phase, "authority_consumed": True}
    state.mark_published()
    return {"result_kind": result_kind, "failure_codes": failure_codes,
            "state": state.phase, "authority_consumed": True}


_INVALID_CODES = frozenset({
    "FROZEN_INPUT_IDENTITY_MISMATCH", "SERIALIZATION_FAILURE", "REPLAY_MISMATCH",
    "PRODUCTION_BOUNDARY_VIOLATION", "FORBIDDEN_IMPORT_DETECTED",
    "PROHIBITED_EVIDENCE_CONTACT_DETECTED", "LOWER_ORDER_CONTROL_MISMATCH",
    "UNAUTHORIZED_EXECUTION", "NONFINITE_DIAGNOSTIC",
})


def _is_invalid(failure_codes):
    return any(c in _INVALID_CODES for c in failure_codes)


def adapter_argv(adapter):
    return getattr(adapter, "argv", [])


def adapter_stdin(adapter):
    return getattr(adapter, "stdin_data", b"")


# --------------------------------------------------------------------------- #
# Serialization, summary, publication
# --------------------------------------------------------------------------- #

FINAL_DIRECTORY = "research/brainvision/results/independent_order_sensitive_synthetic_validation_v0_1"
STAGING_DIRECTORY = "research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_1.staging"
RESULT_FILENAME = "independent_order_sensitive_synthetic_validation_result_v0_1.json"
ENVELOPE_FILENAME = "independent_order_sensitive_synthetic_validation_execution_envelope_v0_1.json"
SUMMARY_FILENAME = "independent_order_sensitive_synthetic_validation_summary_v0_1.txt"


def _pass_identity(bundle):
    return sha256_hex(canonical_bytes(bundle))


def _build_result_object(bundles, result_kind, failure_codes):
    pass_1_sha = _pass_identity(bundles[0])
    pass_2_sha = _pass_identity(bundles[1])
    return {
        "schema": "torment-brainvision-independent-order-sensitive-synthetic-validation-result-v0.1",
        "version": "0.1",
        "operation_identity": {
            "runner_path": RUNNER_PATH,
            "runner_test_path": RUNNER_TEST_PATH,
            "s3b_authorization_path": S3B_AUTHORIZATION_PATH,
            "manifest_path": MANIFEST_PATH,
            "configuration_sha256": CONFIGURATION_SHA256,
        },
        "result_kind": result_kind,
        "ordered_failures": list(failure_codes),
        "pass_1": {"identity_sha256": pass_1_sha, "gate_summary": bundles[0]},
        "pass_2": {"identity_sha256": pass_2_sha, "gate_summary": bundles[1]},
        "replay_comparison": {
            "byte_equal": pass_1_sha == pass_2_sha,
            "pass_1_sha256": pass_1_sha,
            "pass_2_sha256": pass_2_sha,
        },
        "fixed_positive_outcome": bundles[0]["fixed_positive"],
        "generated_positive_outcome": bundles[0]["generated_positive"],
        "negative_nuisance_control_summary": bundles[0]["negative_nuisance_controls"],
        "configuration_identity": configuration_identity(),
        "manifest_identity": default_manifest_identity(),
    }


def _build_envelope_object(adapter, binding, result, state, result_bytes):
    runner_identity = {
        "git_blob": binding["runner_git_blob"],
        "raw_sha256": binding["runner_raw_sha256"],
    }
    runner_test_identity = {
        "git_blob": binding["runner_test_git_blob"],
        "raw_sha256": binding["runner_test_raw_sha256"],
    }
    failure_codes = result["ordered_failures"]
    return {
        "schema": "torment-brainvision-independent-order-sensitive-synthetic-validation-envelope-v0.1",
        "version": "0.1",
        "repository_execution_head": adapter.head(),
        "python_version": adapter.python_version(),
        "s3b_authorization_path": S3B_AUTHORIZATION_PATH,
        "binding_identity_sha256": sha256_hex(canonical_bytes(binding)),
        "descriptor_identity": {
            "git_blob": DESCRIPTOR_IDENTITY["git_blob"],
            "raw_sha256": DESCRIPTOR_IDENTITY["raw_sha256"],
        },
        "descriptor_test_identity": {
            "git_blob": DESCRIPTOR_TEST_IDENTITY["git_blob"],
            "raw_sha256": DESCRIPTOR_TEST_IDENTITY["raw_sha256"],
        },
        "runner_identity": runner_identity,
        "runner_test_identity": runner_test_identity,
        "configuration_sha256": CONFIGURATION_SHA256,
        "manifest_identity": default_manifest_identity(),
        "pre_contact_status": "passed",
        "manifest_contact_count": state.manifest_contact_count,
        "authority_consumed": state.authority_consumed,
        "pass_statuses": ["pass_1_complete", "pass_2_complete"],
        "replay_status": "byte_equal" if result["replay_comparison"]["byte_equal"] else "mismatch",
        "result_kind": result["result_kind"],
        "failure_stage": None if not failure_codes else "synthetic_validation",
        "failure_code": None if not failure_codes else failure_codes[0],
        "publication_status": "published_after_atomic_promotion",
        "artifact_sha256": {RESULT_FILENAME: sha256_hex(result_bytes)},
    }


def summary_lines(result_kind, failure_codes=None, envelope=None):
    if isinstance(result_kind, dict):
        result = result_kind
        failure_codes = result["ordered_failures"]
        lines = [
            "summary_schema=torment-brainvision-independent-order-sensitive-synthetic-validation-summary-v0.1",
            "result_kind=%s" % result["result_kind"],
            "failure_codes=%s" % (",".join(failure_codes) if failure_codes else ""),
            "manifest_contact_count=%s" % envelope["manifest_contact_count"],
            "authority_consumed=%s" % str(envelope["authority_consumed"]).lower(),
            "publication_status=%s" % envelope["publication_status"],
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")
    lines = [
        "summary_schema=torment-brainvision-independent-order-sensitive-synthetic-validation-summary-v0.1",
        "result_kind=%s" % result_kind,
        "failure_codes=%s" % (",".join(failure_codes or []) if failure_codes else ""),
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_authoritative_artifacts(adapter, binding, bundles, result_kind, failure_codes, state):
    if getattr(adapter, "force_artifact_serialization_failure", False):
        raise ValueError("SERIALIZATION_FAILURE")
    result = _build_result_object(bundles, result_kind, failure_codes)
    result_bytes = canonical_bytes(result)
    envelope = _build_envelope_object(adapter, binding, result, state, result_bytes)
    envelope_bytes = canonical_bytes(envelope)
    summary_bytes = summary_lines(result, envelope=envelope)
    return {
        RESULT_FILENAME: result_bytes,
        ENVELOPE_FILENAME: envelope_bytes,
        SUMMARY_FILENAME: summary_bytes,
    }


def publish(staging_dir, final_dir, files, staging_already_created=False):
    expected = {RESULT_FILENAME, ENVELOPE_FILENAME, SUMMARY_FILENAME}
    if staging_dir != STAGING_DIRECTORY or final_dir != FINAL_DIRECTORY:
        raise ValueError("UNAUTHORIZED_EXECUTION")
    if set(files.keys()) != expected:
        raise ValueError("publication file set mismatch")
    if os.path.exists(FINAL_DIRECTORY):
        raise FileExistsError("final directory exists")
    if staging_already_created:
        if not os.path.isdir(STAGING_DIRECTORY):
            raise FileNotFoundError("staging directory absent")
        if os.listdir(STAGING_DIRECTORY):
            raise FileExistsError("staging directory not empty")
    else:
        os.makedirs(STAGING_DIRECTORY, exist_ok=False)

    result_data = files[RESULT_FILENAME]
    envelope_data = files[ENVELOPE_FILENAME]
    summary_data = files[SUMMARY_FILENAME]
    with open(os.path.join(STAGING_DIRECTORY, RESULT_FILENAME), "wb") as handle:
        handle.write(result_data)
    with open(os.path.join(STAGING_DIRECTORY, ENVELOPE_FILENAME), "wb") as handle:
        handle.write(envelope_data)
    with open(os.path.join(STAGING_DIRECTORY, SUMMARY_FILENAME), "wb") as handle:
        handle.write(summary_data)

    with open(os.path.join(STAGING_DIRECTORY, RESULT_FILENAME), "rb") as handle:
        result_back = handle.read()
    with open(os.path.join(STAGING_DIRECTORY, ENVELOPE_FILENAME), "rb") as handle:
        envelope_back = handle.read()
    with open(os.path.join(STAGING_DIRECTORY, SUMMARY_FILENAME), "rb") as handle:
        summary_back = handle.read()
    if result_back != result_data or sha256_hex(result_back) != sha256_hex(result_data):
        raise ValueError("HASH_IDENTITY_FAILURE")
    if envelope_back != envelope_data or sha256_hex(envelope_back) != sha256_hex(envelope_data):
        raise ValueError("HASH_IDENTITY_FAILURE")
    if summary_back != summary_data or sha256_hex(summary_back) != sha256_hex(summary_data):
        raise ValueError("HASH_IDENTITY_FAILURE")
    if set(os.listdir(STAGING_DIRECTORY)) != set(files.keys()):
        raise ValueError("staging set mismatch")
    os.replace(STAGING_DIRECTORY, FINAL_DIRECTORY)


# --------------------------------------------------------------------------- #
# Static authoritative cost estimate
# --------------------------------------------------------------------------- #

def authoritative_cost_estimate():
    """Deterministic structural cost estimate for the authoritative reference path.

    Reports counts only; runs nothing. The reference path performs no dense 64x3906
    tensor loop and no per-transform 32-unit recanonicalization, so the classification
    is HIGH_BUT_EXECUTABLE rather than BLOCKING.
    """
    admitted = 2 * FIXED_POSITIVE_COUNT + 2 * GENERATED_POSITIVE_COUNT   # 18 members
    positive_transformations = ROTATION_COUNT + 1 + AFFINE_COUNT + (AFFINE_COMPLEMENT_COUNT // 2)
    negative_transformations = AFFINE_COMPLEMENT_COUNT // 2
    transforms_per_base = positive_transformations + negative_transformations
    comparisons_per_base = (positive_transformations * 3) + (negative_transformations * 2)
    unique_before_memo = AFFINE_COMPLEMENT_COUNT   # rotations/affine are subsets of the self-orbit
    two_pass_checks = transforms_per_base * admitted * PASS_COUNT
    return {
        "admitted_base_sequences": admitted,
        "materialized_transformations_per_base": transforms_per_base,
        "unique_transformed_sequences_before_memo": unique_before_memo,
        "maximum_unique_transformed_sequences_per_base": unique_before_memo,
        "two_pass_materialized_checks": two_pass_checks,
        "sparse_ops_per_member": "O(w^2 + w^3 + 3906), w <= 32 via complement",
        "complete_vector_comparisons_per_base_per_pass": comparisons_per_base,
        "complete_vector_comparisons_two_pass_total": comparisons_per_base * admitted * PASS_COUNT,
        "complete_3906_entry_vectors_computed": "up to %d" % (
            (unique_before_memo + 1) * admitted * PASS_COUNT),
        "base_canonicalizations": admitted * PASS_COUNT,
        "full_orbit_canonicalizations_per_base": 2,
        "base_canonicalizations_per_base_per_pass": 2,
        "dense_tensor_loops": 0,
        "peak_memoization": "up to 4096 complete 3906-entry reduced vectors for one base sequence",
        "cache_scope": "one base sequence within one pass; fresh for pass 2",
        "likely_peak_memory": "hundreds-of-megabytes class depending on orbit uniqueness",
        "two_pass_multiplier": PASS_COUNT,
        "classification": "HIGH_BUT_EXECUTABLE",
    }


# --------------------------------------------------------------------------- #
# CLI entry point (S3A: S3B document absent -> fail-closed at pre-contact)
# --------------------------------------------------------------------------- #

def main(argv=None, stdin_data=b""):
    """Authoritative CLI. Constructs the real IO adapter and runs the complete future
    operation with the frozen authoritative plan. In Stage S3A the S3B authorization
    document is absent, so pre-contact refuses before any real manifest byte is read.
    No runtime configuration is accepted; the frozen control-plan constants are used."""
    argv = [] if argv is None else list(argv)
    adapter = RealIoAdapter()
    adapter.argv = argv
    adapter.stdin_data = stdin_data
    state = ExecutionState()
    try:
        outcome = run_authoritative(adapter, authoritative_control_plan(), state)
    except Exception:   # any unresolved fault before contact is a fail-closed refusal
        sys.stderr.write("SYNTHETIC_VALIDATION_REFUSED UNAUTHORIZED_EXECUTION\n")
        return 2
    if not state.authority_consumed:
        sys.stderr.write("SYNTHETIC_VALIDATION_REFUSED %s\n"
                         % " ".join(outcome["failure_codes"] or ["UNAUTHORIZED_EXECUTION"]))
        return 2
    if outcome["result_kind"] == "SYNTHETIC_GATE_PASSED":
        return 0
    if outcome["result_kind"] == "SYNTHETIC_GATE_FAILED":
        return 1
    return 3


# Independently computed configuration identity (recorded by the later S3B binding).
CONFIGURATION_SHA256 = configuration_sha256()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], sys.stdin.buffer.read() if not sys.stdin.isatty() else b""))
