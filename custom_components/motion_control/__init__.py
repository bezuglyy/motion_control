from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time as dt_time, timedelta
import logging
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .config_flow import merge_entry_payload, normalize_entry_payload
from .const import (
    ATTR_ACTIVE_OFF_SENSORS,
    ATTR_ACTIVE_ON_SENSORS,
    ATTR_LAST_ACTION,
    ATTR_LAST_ACTION_AT,
    ATTR_LAST_LUX,
    ATTR_LAST_REASON,
    ATTR_NEXT_OFF_AT,
    ATTR_STATUS,
    ATTR_TARGET_STATE,
    COLOR_HS_MAP,
    COLOR_KEEP,
    CONF_ENABLED,
    CONF_ILLUMINANCE_SENSOR,
    CONF_LIGHT,
    CONF_MOTION_SENSORS,
    CONF_OFF_ENABLED,
    CONF_OFF_SENSORS,
    CONF_ON_ENABLED,
    CONF_ON_SENSORS,
    CONF_TARGET_ENTITY,
    CONF_TRIGGER_SENSORS,
    CONF_USE_ILLUMINANCE,
    CTRL_COLOR,
    CTRL_END_TIME,
    CTRL_ILLUMINANCE_BLOCK_LUX,
    CTRL_MAX_BRIGHTNESS_PCT,
    CTRL_MAX_LUX,
    CTRL_MIN_BRIGHTNESS_PCT,
    CTRL_MIN_LUX,
    CTRL_OFF_DELAY_MIN,
    CTRL_START_TIME,
    DEFAULT_CTRL_VALUES,
    DEFAULT_ENABLED,
    DEFAULT_OFF_ENABLED,
    DEFAULT_ON_ENABLED,
    DOMAIN,
    EVENT_UPDATE,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class Runner:
    hass: HomeAssistant
    entry: ConfigEntry
    ctrl: dict[str, Any] = field(default_factory=dict)
    listeners: list[Callable[[], None]] = field(default_factory=list)
    unsubscribers: list[Callable[[], None]] = field(default_factory=list)
    off_handle: Callable[[], None] | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def cfg(self) -> dict[str, Any]:
        return merge_entry_payload(self.entry.data, self.entry.options)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_time(value: Any, fallback: dt_time) -> dt_time:
    if isinstance(value, dt_time):
        return value
    try:
        parts = str(value).split(":")
        hh = int(parts[0])
        mm = int(parts[1])
        ss = int(parts[2]) if len(parts) > 2 else 0
        return dt_time(hh, mm, ss)
    except Exception:
        return fallback


def _within_schedule(start: dt_time, end: dt_time, now_t: dt_time) -> bool:
    if start <= end:
        return start <= now_t <= end
    return now_t >= start or now_t <= end


def _is_on_state(state: str | None) -> bool:
    return state in {"on", "open", "opening", "motion", "detected", "true", "home", "occupied"}


def _active_entities(hass: HomeAssistant, entities: list[str]) -> list[str]:
    active: list[str] = []
    for ent in entities:
        st = hass.states.get(ent)
        if st and _is_on_state(st.state.lower() if isinstance(st.state, str) else st.state):
            active.append(ent)
    return active


def _calc_brightness_pct(min_lux: float, max_lux: float, min_pct: float, max_pct: float, lux: float) -> int:
    min_pct = max(1.0, min(100.0, min_pct))
    max_pct = max(1.0, min(100.0, max_pct))
    if max_pct < min_pct:
        min_pct, max_pct = max_pct, min_pct
    if max_lux <= min_lux:
        return round(max_pct)
    if lux <= min_lux:
        return round(max_pct)
    if lux >= max_lux:
        return round(min_pct)
    ratio = (lux - min_lux) / (max_lux - min_lux)
    value = max_pct - ratio * (max_pct - min_pct)
    return round(max(min_pct, min(max_pct, value)))


@callback
def get_runner(hass: HomeAssistant, entry_id: str) -> Runner | None:
    return hass.data.get(DOMAIN, {}).get(entry_id)


@callback
def _emit_update(runner: Runner) -> None:
    runner.hass.bus.async_fire(EVENT_UPDATE, {"entry_id": runner.entry.entry_id})
    for listener in list(runner.listeners):
        try:
            listener()
        except Exception:
            _LOGGER.debug("Entity listener failed", exc_info=True)


@callback
def async_register_entity_update_listener(hass: HomeAssistant, entry_id: str, listener: Callable[[], None]) -> Callable[[], None]:
    runner = get_runner(hass, entry_id)
    if runner is None:
        return lambda: None
    runner.listeners.append(listener)

    @callback
    def _remove() -> None:
        if listener in runner.listeners:
            runner.listeners.remove(listener)

    return _remove


@callback
def _clear_runtime_subscriptions(runner: Runner) -> None:
    for unsub in runner.unsubscribers:
        try:
            unsub()
        except Exception:
            _LOGGER.debug("Failed to unsubscribe", exc_info=True)
    runner.unsubscribers.clear()


@callback
def _install_runtime_subscriptions(runner: Runner) -> None:
    hass = runner.hass
    cfg = runner.cfg

    @callback
    def _state_listener(_event) -> None:
        hass.async_create_task(async_reconcile(hass, runner.entry.entry_id, reason="state_changed"))

    tracked = set(cfg.get(CONF_ON_SENSORS, []))
    tracked.update(cfg.get(CONF_OFF_SENSORS, []))
    if cfg.get(CONF_ILLUMINANCE_SENSOR):
        tracked.add(cfg[CONF_ILLUMINANCE_SENSOR])
    if cfg.get(CONF_TARGET_ENTITY):
        tracked.add(cfg[CONF_TARGET_ENTITY])

    if tracked:
        runner.unsubscribers.append(async_track_state_change_event(hass, list(tracked), _state_listener))

    @callback
    def _periodic_listener(_now) -> None:
        hass.async_create_task(async_reconcile(hass, runner.entry.entry_id, reason="periodic"))

    runner.unsubscribers.append(async_track_time_interval(hass, _periodic_listener, timedelta(minutes=1)))


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = dict(entry.data)
    if entry.version < 8:
        if CONF_ON_SENSORS not in data:
            data[CONF_ON_SENSORS] = data.get(CONF_TRIGGER_SENSORS) or data.get(CONF_MOTION_SENSORS) or []
        if CONF_TARGET_ENTITY not in data and CONF_LIGHT in data:
            data[CONF_TARGET_ENTITY] = data.get(CONF_LIGHT)
        data = normalize_entry_payload(data)
        hass.config_entries.async_update_entry(entry, data=data, title=data.get("name", entry.title), version=8)
        _LOGGER.info("Migrated %s entry %s to version 8", DOMAIN, entry.entry_id)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    cfg = merge_entry_payload(entry.data, entry.options)
    ctrl = dict(DEFAULT_CTRL_VALUES)
    ctrl[CTRL_OFF_DELAY_MIN] = cfg.get(CTRL_OFF_DELAY_MIN, DEFAULT_CTRL_VALUES[CTRL_OFF_DELAY_MIN])
    runner = Runner(hass=hass, entry=entry, ctrl=ctrl)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runner

    _install_runtime_subscriptions(runner)

    async def _handle_update(hass: HomeAssistant, updated_entry: ConfigEntry) -> None:
        cur = hass.data[DOMAIN].get(updated_entry.entry_id)
        if cur is None:
            return
        cur.entry = updated_entry
        merged = merge_entry_payload(updated_entry.data, updated_entry.options)
        cur.ctrl[CTRL_OFF_DELAY_MIN] = merged.get(CTRL_OFF_DELAY_MIN, cur.ctrl.get(CTRL_OFF_DELAY_MIN, 1))
        _clear_runtime_subscriptions(cur)
        _install_runtime_subscriptions(cur)
        await async_reconcile(hass, updated_entry.entry_id, reason="entry_updated")

    entry.async_on_unload(entry.add_update_listener(_handle_update))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_reconcile(hass, entry.entry_id, reason="setup")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    runner: Runner | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if runner:
        if runner.off_handle:
            runner.off_handle()
            runner.off_handle = None
        _clear_runtime_subscriptions(runner)
    return unload_ok


async def async_set_ctrl_value(hass: HomeAssistant, entry_id: str, field: str, value: Any) -> None:
    runner = get_runner(hass, entry_id)
    if runner is None:
        return
    runner.ctrl[field] = value
    await async_reconcile(hass, entry_id, reason=f"ctrl:{field}")


async def _turn_on_target(runner: Runner, target_entity: str, lux: float, reason: str) -> None:
    target_domain = target_entity.split(".", 1)[0]
    service_data: dict[str, Any] = {ATTR_ENTITY_ID: target_entity}
    if target_domain == "light":
        service_data["brightness_pct"] = _calc_brightness_pct(
            _safe_float(runner.ctrl.get(CTRL_MIN_LUX), 0.0),
            _safe_float(runner.ctrl.get(CTRL_MAX_LUX), 200.0),
            _safe_float(runner.ctrl.get(CTRL_MIN_BRIGHTNESS_PCT), 10.0),
            _safe_float(runner.ctrl.get(CTRL_MAX_BRIGHTNESS_PCT), 100.0),
            lux,
        )
        color_name = runner.ctrl.get(CTRL_COLOR, COLOR_KEEP)
        if color_name in COLOR_HS_MAP:
            service_data["hs_color"] = COLOR_HS_MAP[color_name]
    await runner.hass.services.async_call(target_domain, SERVICE_TURN_ON, service_data, blocking=False)
    runner.data[ATTR_LAST_ACTION] = "turn_on"
    runner.data[ATTR_LAST_ACTION_AT] = dt_util.now().isoformat()
    runner.data[ATTR_LAST_REASON] = reason
    runner.data[ATTR_STATUS] = "on"


async def _turn_off_now(runner: Runner, target_entity: str, reason: str) -> None:
    target_domain = target_entity.split(".", 1)[0]
    await runner.hass.services.async_call(target_domain, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: target_entity}, blocking=False)
    runner.data[ATTR_LAST_ACTION] = "turn_off"
    runner.data[ATTR_LAST_ACTION_AT] = dt_util.now().isoformat()
    runner.data[ATTR_LAST_REASON] = reason
    runner.data[ATTR_STATUS] = "off"
    runner.data[ATTR_NEXT_OFF_AT] = None


async def _schedule_or_turn_off(runner: Runner, target_entity: str, immediate: bool, reason: str) -> None:
    if runner.off_handle:
        runner.off_handle()
        runner.off_handle = None
    delay_min = int(_safe_float(runner.ctrl.get(CTRL_OFF_DELAY_MIN), 1))
    if immediate or delay_min <= 0:
        await _turn_off_now(runner, target_entity, reason)
        return

    off_at = dt_util.now() + timedelta(minutes=delay_min)
    runner.data[ATTR_NEXT_OFF_AT] = off_at.isoformat()
    runner.data[ATTR_STATUS] = "delayed_off"
    runner.data[ATTR_LAST_REASON] = reason

    @callback
    def _do_off(_now) -> None:
        runner.off_handle = None
        runner.hass.async_create_task(_turn_off_now(runner, target_entity, reason))
        _emit_update(runner)

    runner.off_handle = async_call_later(runner.hass, delay_min * 60, _do_off)


async def async_reconcile(hass: HomeAssistant, entry_id: str, reason: str = "manual") -> None:
    runner = get_runner(hass, entry_id)
    if runner is None:
        return
    cfg = runner.cfg
    target_entity = cfg.get(CONF_TARGET_ENTITY)
    if not target_entity:
        runner.data[ATTR_STATUS] = "missing_target"
        runner.data[ATTR_LAST_REASON] = f"{reason}:missing_target"
        _emit_update(runner)
        return

    on_entities = list(cfg.get(CONF_ON_SENSORS, [])) if cfg.get(CONF_ON_ENABLED, DEFAULT_ON_ENABLED) else []
    off_entities = list(cfg.get(CONF_OFF_SENSORS, [])) if cfg.get(CONF_OFF_ENABLED, DEFAULT_OFF_ENABLED) else []
    illum_entity = cfg.get(CONF_ILLUMINANCE_SENSOR)
    use_illuminance = bool(cfg.get(CONF_USE_ILLUMINANCE, False))

    active_on = _active_entities(hass, on_entities)
    active_off = _active_entities(hass, off_entities)

    lux = 0.0
    if illum_entity and hass.states.get(illum_entity):
        lux = _safe_float(hass.states.get(illum_entity).state, 0.0)

    start_t = _parse_time(runner.ctrl.get(CTRL_START_TIME), dt_time(0, 0, 0))
    end_t = _parse_time(runner.ctrl.get(CTRL_END_TIME), dt_time(23, 59, 59))
    now_t = dt_util.now().time()
    in_schedule = _within_schedule(start_t, end_t, now_t)

    runner.data[ATTR_LAST_LUX] = lux
    runner.data[ATTR_ACTIVE_ON_SENSORS] = active_on
    runner.data[ATTR_ACTIVE_OFF_SENSORS] = active_off
    st = hass.states.get(target_entity)
    runner.data[ATTR_TARGET_STATE] = st.state if st else None

    if not cfg.get(CONF_ENABLED, DEFAULT_ENABLED):
        await _schedule_or_turn_off(runner, target_entity, immediate=True, reason=f"{reason}:integration_disabled")
        _emit_update(runner)
        return

    if target_entity.split(".", 1)[0] not in {"light", "switch"}:
        runner.data[ATTR_STATUS] = "unsupported_target"
        runner.data[ATTR_LAST_REASON] = f"{reason}:unsupported_target"
        _emit_update(runner)
        return

    if runner.off_handle and active_on and not active_off:
        runner.off_handle()
        runner.off_handle = None
        runner.data[ATTR_NEXT_OFF_AT] = None

    if not in_schedule:
        await _schedule_or_turn_off(runner, target_entity, immediate=True, reason=f"{reason}:out_of_schedule")
        _emit_update(runner)
        return

    if active_off:
        await _schedule_or_turn_off(runner, target_entity, immediate=False, reason=f"{reason}:off_sensor")
        _emit_update(runner)
        return

    if active_on:
        if use_illuminance and illum_entity:
            limit = _safe_float(runner.ctrl.get(CTRL_ILLUMINANCE_BLOCK_LUX), 100.0)
            if lux > limit:
                runner.data[ATTR_STATUS] = "blocked_by_illuminance"
                runner.data[ATTR_LAST_REASON] = f"{reason}:lux>{limit}"
                _emit_update(runner)
                return
        await _turn_on_target(runner, target_entity, lux, reason=f"{reason}:on_sensor")
        _emit_update(runner)
        return

    await _schedule_or_turn_off(runner, target_entity, immediate=False, reason=f"{reason}:inactive")
    _emit_update(runner)
