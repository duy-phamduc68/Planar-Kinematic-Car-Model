# ─────────────────────────────────────────────────────────────────────────────
# Module: longitudinal
# Path: model6/longitudinal/__init__.py
# Purpose: Registry/factory for supported longitudinal engines.
# ─────────────────────────────────────────────────────────────────────────────

from longitudinal.long1 import Long1Engine
from longitudinal.long3 import Long3Engine
from longitudinal.long5 import Long5Engine


ENGINE_REGISTRY = {
    1: Long1Engine,
    3: Long3Engine,
    5: Long5Engine,
}

ENGINE_CHOICES = tuple((eid, ENGINE_REGISTRY[eid].label) for eid in sorted(ENGINE_REGISTRY.keys()))


def get_longitudinal_engine(engine_id):
    """Create a longitudinal engine by id; defaults to Long.1 when unknown."""
    engine_cls = ENGINE_REGISTRY.get(engine_id, Long1Engine)
    return engine_cls()


def supported_engine_ids():
    return tuple(sorted(ENGINE_REGISTRY.keys()))


def get_engine_choices():
    return ENGINE_CHOICES


def get_engine_label(engine_id):
    engine_cls = ENGINE_REGISTRY.get(engine_id, Long1Engine)
    return engine_cls.label
