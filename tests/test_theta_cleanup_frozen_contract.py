"""Immutable Phase 2C observations for ordered theta selection only.

The inert fixture is the authority. Production HEAD, source bytes and AST shape
are deliberately NOT acceptance conditions. No capture/regeneration mode exists.
"""
from contextlib import contextmanager
import dataclasses
import hashlib
import importlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import struct
import sys
import warnings

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / 'torment_service' / 'kernel'
FIXTURES = Path(__file__).parent / 'fixtures' / 'theta_cleanup_phase2c'
FIXTURE_SHA256 = 'ad0f439cebc5419bd14adc414489941334c2131267f7e36927529a240145dd8c'
MISSING = object()


def _read_fixture():
    raw = (FIXTURES / 'theta_fixture.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256, 'immutable theta fixture changed'
    fixture = json.loads(raw)
    assert fixture['schema'] == 'TORMENT_PHASE2C_THETA_PRODUCTION_BEFORE_v1'
    assert len(fixture['cases']) == 88
    assert len({case['id'] for case in fixture['cases']}) == 88
    return fixture


FROZEN = _read_fixture()
BY_ID = {case['id']: case for case in FROZEN['cases']}


def typename(value):
    return type(value).__module__ + '.' + type(value).__qualname__


def f64(value):
    value = float(value)
    return {'decimal': repr(value), 'hex': value.hex(),
            'binary64_bits_be': struct.pack('>d', value).hex()}


def describe(value):
    if isinstance(value, np.ndarray):
        return {'type': typename(value), 'dtype': value.dtype.str,
                'shape': list(value.shape), 'strides': list(value.strides),
                'writeable': bool(value.flags.writeable), 'owndata': bool(value.flags.owndata),
                'base_type': None if value.base is None else typename(value.base),
                'c_contiguous': bool(value.flags.c_contiguous),
                'f_contiguous': bool(value.flags.f_contiguous),
                'bytes_c_order_hex': value.tobytes(order='C').hex(),
                'values': [describe(item) for item in value.flat]}
    if isinstance(value, np.generic):
        data = {'type': typename(value), 'dtype': value.dtype.str,
                'native_bytes_hex': value.tobytes().hex()}
        if np.issubdtype(value.dtype, np.complexfloating):
            data.update(real=f64(value.real), imag=f64(value.imag))
        elif np.issubdtype(value.dtype, np.floating):
            data.update(f64(value))
        else:
            data['value'] = value.item()
        return data
    if isinstance(value, float):
        return {'type': typename(value), **f64(value)}
    if isinstance(value, complex):
        return {'type': typename(value), 'real': f64(value.real), 'imag': f64(value.imag)}
    if dataclasses.is_dataclass(value):
        return {'type': typename(value), 'fields': {
            field.name: describe(getattr(value, field.name)) for field in dataclasses.fields(value)}}
    if isinstance(value, (tuple, list)):
        return {'type': typename(value), 'items': [describe(item) for item in value]}
    if isinstance(value, dict):
        return {'type': typename(value), 'items': {str(k): describe(v) for k, v in value.items()}}
    if value is None or isinstance(value, (str, int, bool)):
        return {'type': typename(value), 'value': value}
    # Never include a process-specific object address.
    return {'type': typename(value)}


def error_record(error):
    return {'type': typename(error), 'message': str(error)}


def alpha_value(name):
    if name == 'default':
        return MISSING
    cases = {
        'zero_int': lambda: 0, 'negative_zero': lambda: -0.0,
        'quarter': lambda: 0.25, 'half': lambda: 0.5, 'two_int': lambda: 2,
        'negative_one': lambda: -1, 'np_float32': lambda: np.float32(0.25),
        'np_float64': lambda: np.float64(0.5), 'np_int64': lambda: np.int64(2),
        'bool': lambda: True, 'complex': lambda: 1 + 2j,
        'array_0d': lambda: np.array(0.5),
        'array_vector3': lambda: np.array([0.25, 0.5, 2.0]),
        'array_row': lambda: np.array([[0.25, 0.5, 2.0]]),
        'array_column': lambda: np.array([[0.25], [2.0]]),
        'array_matrix': lambda: np.array([[0.0, -0.0, 1.0], [0.25, 0.5, 2.0]]),
        'array_float32': lambda: np.array([0.25, 0.5, 2.0], dtype=np.float32),
        'array_noncontiguous': lambda: np.arange(6., dtype=np.float64)[::2],
        'array_empty': lambda: np.empty((0, 3)),
        'array_nonfinite': lambda: np.array([float('inf'), -float('inf'), float('nan')]),
        'list3': lambda: [0.25, 0.5, 2.0], 'tuple3': lambda: (0.25, 0.5, 2.0),
        'pos_inf': lambda: float('inf'), 'neg_inf': lambda: -float('inf'),
        'nan': lambda: float('nan'), 'none': lambda: None, 'string': lambda: 'bad-alpha',
        'dict': lambda: {'alpha': 1.0}, 'object': object,
        'array_bad_shape': lambda: np.array([1., 2.]),
        'matrix_bad_shape': lambda: np.ones((2, 2)),
    }
    if name == 'array_readonly':
        result = np.array([0.25, 0.5, 2.0])
        result.flags.writeable = False
        return result
    return cases[name]()


ALPHAS = [
    'default', 'zero_int', 'negative_zero', 'quarter', 'half', 'two_int', 'negative_one',
    'np_float32', 'np_float64', 'np_int64', 'bool', 'complex', 'array_0d', 'array_vector3',
    'array_row', 'array_column', 'array_matrix', 'array_float32', 'array_readonly',
    'array_noncontiguous', 'array_empty', 'array_nonfinite', 'list3', 'tuple3',
    'pos_inf', 'neg_inf', 'nan', 'none', 'string', 'dict', 'object',
    'array_bad_shape', 'matrix_bad_shape',
]


class NumpyObserver:
    """Only the selector's local np binding is replaced; NumPy itself is untouched."""
    def __init__(self, original, events):
        self.original, self.events = original, events

    def __getattr__(self, name):
        original = getattr(self.original, name)
        if name not in ('array', 'sqrt'):
            return original
        def observed(*args, **kwargs):
            event = {'operation': 'np.' + name}
            self.events.append(event)
            try:
                result = original(*args, **kwargs)
                event['returned'] = True
                return result
            except Exception as error:
                event['exception'] = error_record(error)
                raise
        return observed


@contextmanager
def instrument(module, *, failure=None, first_theta=MISSING, wrong_tuple=None):
    getter, theta, numpy = module.get_core_constants, module.theta_value, module.np
    events, downstream, getter_objects = [], [], []
    index = 0
    def observed_getter():
        event = {'call': 'get_core_constants'}
        events.append(event)
        if failure == 'getter':
            error = RuntimeError('Phase2C injected failure: getter')
            event['exception'] = error_record(error)
            raise error
        result = getter()
        getter_objects.append(result)
        event['return'] = describe(result)
        return result

    def observed_theta(Ci, Cj):
        nonlocal index
        index += 1
        event = {'call': 'theta_value', 'pair_index': index,
                 'arguments': [describe(Ci), describe(Cj)]}
        events.append(event)
        if failure == f'theta{index}':
            error = RuntimeError(f'Phase2C injected failure: theta{index}')
            event['exception'] = error_record(error)
            raise error
        result = theta(Ci, Cj)
        if index == 1 and first_theta is not MISSING:
            result = first_theta
        if wrong_tuple is not None:
            result = wrong_tuple[index - 1]
        event['return'] = describe(result)
        return result

    module.get_core_constants = observed_getter
    module.theta_value = observed_theta
    module.np = NumpyObserver(numpy, downstream)
    try:
        yield events, downstream, getter_objects
    finally:
        module.get_core_constants, module.theta_value, module.np = getter, theta, numpy


def observe(module, operation, *, projection=lambda x: x, alpha=MISSING, **instrumentation):
    before = None if alpha is MISSING else describe(alpha)
    raw = result = MISSING
    exception = None
    with instrument(module, **instrumentation) as (events, downstream, getter_objects):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            try:
                raw = operation()
                result = projection(raw)
            except Exception as error:
                exception = error_record(error)
    record = {
        'returned': raw is not MISSING,
        'result': None if result is MISSING else describe(result),
        'exception': exception,
        'warnings': [{'category': warning.category.__module__ + '.' + warning.category.__qualname__,
                      'message': str(warning.message)} for warning in caught],
        'prefix_events': events, 'downstream_events': downstream,
        'getter_call_count': sum(event['call'] == 'get_core_constants' for event in events),
        'theta_call_count': sum(event['call'] == 'theta_value' for event in events),
        'partial_result_returned': False if raw is MISSING else None,
        'alpha_unchanged': None if alpha is MISSING else describe(alpha) == before,
        'shares_memory_with_alpha': bool(np.shares_memory(result, alpha))
            if isinstance(result, np.ndarray) and isinstance(alpha, np.ndarray) else None,
    }
    return record, result, getter_objects, raw


def repeated_case(case_id, group, module, operation, *, alpha=MISSING,
                  inputs=None, projection=lambda x: x, **instrumentation):
    first, a, ga, raw_a = observe(module, operation, alpha=alpha, projection=projection, **instrumentation)
    second, b, gb, raw_b = observe(module, operation, alpha=alpha, projection=projection, **instrumentation)
    # Repeated observations must be exact before any expected fixture is admitted.
    assert first == second, f'Nonrepeatable observation within capture: {case_id}'
    ownership = None
    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        ownership = {'distinct_objects': a is not b, 'shares_memory': bool(np.shares_memory(a, b)),
                     'mutation_of_first_leaves_second_unchanged': None}
        if a.size and a.flags.writeable:
            before = describe(b)
            a.flat[0] = 123.456
            ownership['mutation_of_first_leaves_second_unchanged'] = describe(b) == before
    return {'id': case_id, 'group': group, 'inputs': inputs or {}, 'observation': first,
            'second_invocation_exact_match': True, 'repeat_allocation': ownership,
            'getter_instances_fresh_across_invocations':
                (ga[0] is not gb[0]) if ga and gb else None}


def ordered(module):
    c = module.get_core_constants()
    return (module.theta_value(c.sqrt3, c.phi), module.theta_value(c.pi, c.e),
            module.theta_value(c.phi, c.e))


def case_set(selector, model, bare, oracle):
    cases = []
    add = cases.append
    add(repeated_case('ordered.production_theta_calls', 'ordered', selector,
                      lambda: ordered(selector)))
    for name in ALPHAS:
        alpha = alpha_value(name)
        kwargs = {} if alpha is MISSING else {'alpha': alpha}
        add(repeated_case('soft.' + name, 'public_soft', selector,
            lambda kwargs=kwargs: selector.theta_soft_triplet(**kwargs), alpha=alpha,
            inputs={'alpha_case': name, 'alpha': None if alpha is MISSING else describe(alpha)}))
    add(repeated_case('scaled.default', 'public_scaled', selector, selector.theta_triplet_scaled))

    for profile in ('soft', 'scaled'):
        operation = selector.theta_soft_triplet if profile == 'soft' else selector.theta_triplet_scaled
        for failure in ('getter', 'theta1', 'theta2', 'theta3'):
            add(repeated_case(f'failure.{profile}.{failure}', 'injected_failure', selector,
                operation, failure=failure, inputs={'failure_at': failure}))

    guard_values = [('normal', MISSING), ('positive_zero', 0.0), ('negative_zero', -0.0),
                    ('negative', -1.0), ('pos_inf', float('inf')), ('neg_inf', -float('inf')),
                    ('nan', float('nan')), ('tiny_positive', 1e-320),
                    ('numpy_zero', np.float64(0.0)), ('numpy_negative_zero', np.float64(-0.0))]
    for profile in ('soft', 'scaled'):
        operation = selector.theta_soft_triplet if profile == 'soft' else selector.theta_triplet_scaled
        for name, value in guard_values:
            add(repeated_case(f'guard.{profile}.{name}', 'base_guard', selector, operation,
                first_theta=value, inputs={'first_theta_case': name,
                    'first_theta': None if value is MISSING else describe(value)}))

    add(repeated_case('dispatch.default', 'dispatch', selector, selector.default_k_triplet))
    for mode in ('simple', 'theta_soft', 'theta_scaled', 'scaled', 'unknown_selector', ''):
        for alpha_name in ('quarter', 'object'):
            alpha = alpha_value(alpha_name)
            add(repeated_case(f'dispatch.{mode or "empty"}.{alpha_name}', 'dispatch', selector,
                lambda mode=mode, alpha=alpha: selector.default_k_triplet(mode=mode, alpha=alpha),
                alpha=alpha, inputs={'mode': mode, 'alpha_case': alpha_name, 'alpha': describe(alpha)}))

    for name, module in [('package', selector), ('bare', bare)]:
        for profile in ('soft', 'scaled'):
            operation = module.theta_soft_triplet if profile == 'soft' else module.theta_triplet_scaled
            add(repeated_case(f'import.{name}.{profile}', 'import_compatibility', module, operation))
    for name, module, cls in [('package', selector, model.ModelParams), ('oracle_bare', bare, oracle.ModelParams)]:
        add(repeated_case(f'factory.{name}.default', 'model_params', module, cls,
                          projection=lambda value: value.k_vals))
        # Observe original supplied identity and bypass; do not mutate the supplied input.
        for explicit_name, supplied in [('array', np.array([7., 8., 9.])),
                                        ('list', [7., 8., 9.]), ('none', None)]:
            before = describe(supplied)
            record, k, getter_objects, params = observe(module,
                lambda cls=cls, supplied=supplied: cls(k_vals=supplied),
                projection=lambda value: value.k_vals, failure='getter')
            add({'id': f'factory.{name}.explicit_{explicit_name}', 'group': 'model_params',
                 'inputs': {'explicit_k': before}, 'observation': record,
                 'supplied_identity_preserved': params.k_vals is supplied,
                 'supplied_unchanged': describe(supplied) == before,
                 'factory_bypassed_even_with_failing_getter': record['getter_call_count'] == 0})
    return cases


def first_difference(expected, actual, path='$'):
    if type(expected) is not type(actual):
        return {'path': path, 'expected': expected, 'actual': actual}
    if isinstance(expected, dict):
        if set(expected) != set(actual):
            return {'path': path, 'expected_keys': sorted(expected), 'actual_keys': sorted(actual)}
        for key in expected:
            difference = first_difference(expected[key], actual[key], path + '.' + key)
            if difference:
                return difference
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return {'path': path, 'expected_length': len(expected), 'actual_length': len(actual)}
        for index, (a, b) in enumerate(zip(expected, actual)):
            difference = first_difference(a, b, path + f'[{index}]')
            if difference:
                return difference
    elif expected != actual:
        return {'path': path, 'expected': expected, 'actual': actual}
    return None



_PURE_NAMES = ('constants_selector', 'su3_basis', 'phase_triad_sync',
               'latent_foreclosure', 'identity_rules')


class _PureImportsOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        forbidden = ('sqlite3', '_sqlite3', 'sentence_transformers', 'transformers',
                     'openai', 'ollama', 'torch', 'requests', 'httpx',
                     'trioctagon_historical_kernel', 'kernel_physics', 'kernel_TO')
        if any(fullname == name or fullname.startswith(name + '.') for name in forbidden):
            raise AssertionError('out-of-scope dependency: ' + fullname)
        allowed = {'torment_service.kernel', 'torment_service.kernel.model_core',
                   *('torment_service.kernel.' + name for name in _PURE_NAMES)}
        if fullname.startswith('torment_service.') and fullname not in allowed:
            raise AssertionError('out-of-scope production dependency: ' + fullname)
        return None


@pytest.fixture(scope='module')
def pure_modules():
    guard = _PureImportsOnly()
    bare_names = (*_PURE_NAMES, 'theta_cleanup_original_model_oracle')
    previous = {name: sys.modules.get(name, MISSING) for name in bare_names}
    for name in bare_names:
        sys.modules.pop(name, None)
    sys.meta_path.insert(0, guard)
    try:
        with pytest.MonkeyPatch.context() as patch, np.errstate(
                divide='warn', over='warn', under='ignore', invalid='warn'):
            patch.syspath_prepend(str(ROOT))
            patch.syspath_prepend(str(KERNEL))
            patch.setattr(sys, 'dont_write_bytecode', True)
            selector = importlib.import_module('torment_service.kernel.constants_selector')
            model = importlib.import_module('torment_service.kernel.model_core')
            bare = importlib.import_module('constants_selector')
            spec = importlib.util.spec_from_file_location('theta_cleanup_original_model_oracle',
                ROOT / 'tests' / 'oracles' / 'model_core_v4_0_original.py')
            oracle = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = oracle
            spec.loader.exec_module(oracle)
            # Import location and binding checks, never source identity/hash checks.
            for module in (selector, bare):
                assert Path(module.__file__).resolve() == (KERNEL / 'constants_selector.py').resolve()
            assert model.ModelParams.__dataclass_fields__['k_vals'].default_factory is selector.default_k_triplet
            assert oracle.ModelParams.__dataclass_fields__['k_vals'].default_factory is bare.default_k_triplet
            yield selector, model, bare, oracle
    finally:
        sys.meta_path.remove(guard)
        for name, original in previous.items():
            if original is MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


@pytest.fixture(scope='module')
def actual_cases(pure_modules):
    # Observations only. No expected output is computed by this function.
    records = case_set(*pure_modules)
    assert [record['id'] for record in records] == list(BY_ID)
    return {record['id']: record for record in records}


def _assert_frozen(expected, actual):
    difference = first_difference(expected, actual)
    assert difference is None, 'frozen theta behavior mismatch: ' + repr(difference)


@pytest.mark.parametrize('case_id', list(BY_ID))
def test_frozen_theta_case(case_id, actual_cases):
    _assert_frozen(BY_ID[case_id], actual_cases[case_id])


@pytest.mark.parametrize('mutation', ['swap_pair2_pair3', 'duplicate_pair2'])
@pytest.mark.parametrize('profile', ['soft', 'scaled'])
def test_negative_control_rejects_wrong_shared_tuple(pure_modules, mutation, profile):
    selector = pure_modules[0]
    events = BY_ID['ordered.production_theta_calls']['observation']['prefix_events'][1:]
    # Deliberate wrong tuples are built ONLY from the inert production-before bits.
    triple = tuple(struct.unpack('>d', bytes.fromhex(event['return']['binary64_bits_be']))[0]
                   for event in events)
    wrong = ((triple[0], triple[2], triple[1]) if mutation == 'swap_pair2_pair3'
             else (triple[0], triple[1], triple[1]))
    function = selector.theta_soft_triplet if profile == 'soft' else selector.theta_triplet_scaled
    key = 'soft.default' if profile == 'soft' else 'scaled.default'
    expected = BY_ID[key]['observation']
    bindings_before = (selector.get_core_constants, selector.theta_value, selector.np)
    actual, _, _, _ = observe(selector, function, wrong_tuple=wrong)
    assert (selector.get_core_constants, selector.theta_value, selector.np) == bindings_before
    with pytest.raises(AssertionError, match='frozen theta behavior mismatch'):
        _assert_frozen(expected, actual)
    with pytest.raises(AssertionError, match='frozen theta behavior mismatch'):
        _assert_frozen(expected['prefix_events'], actual['prefix_events'])
    # Restoration is behavioral as well as binding identity; expected stays frozen.
    restored, _, _, _ = observe(selector, function)
    _assert_frozen(expected, restored)


def test_fixture_integrity_and_admission_policy():
    assert _read_fixture() == FROZEN
    provenance = json.loads((FIXTURES / 'provenance.json').read_text(encoding='utf-8'))
    assert provenance['fixture_sha256'] == FIXTURE_SHA256
    assert provenance['expected_output_policy'] == 'IMMUTABLE_PRODUCTION_BEFORE_VALUES'
    assert provenance['source_identity_policy'] == 'PROVENANCE_ONLY_NOT_TEST_CONDITION'
