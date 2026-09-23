from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.helpers import selector

from .const import (
    CONF_ENABLED,
    CONF_ILLUMINANCE_SENSOR,
    CONF_LIGHT,
    CONF_MOTION_SENSORS,
    CONF_NAME,
    CONF_OFF_ENABLED,
    CONF_OFF_SENSORS,
    CONF_ON_ENABLED,
    CONF_ON_SENSORS,
    CONF_RESET_OPTIONS,
    CONF_TARGET_ENTITY,
    CONF_TRIGGER_SENSORS,
    CONF_TRIGGER_TYPE,
    CONF_USE_ILLUMINANCE,
    CTRL_OFF_DELAY_MIN,
    DEFAULT_ENABLED,
    DEFAULT_NAME,
    DEFAULT_OFF_DELAY_MIN,
    DEFAULT_OFF_ENABLED,
    DEFAULT_ON_ENABLED,
    DEFAULT_TRIGGER_TYPE,
    DEFAULT_USE_ILLUMINANCE,
    DOMAIN,
    TRIGGER_TYPE_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


def _clean_entity(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value or value.lower() == "none":
        return ""
    return value


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() == "none":
            return []
        return [value]
    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        for item in value:
            ent = _clean_entity(item)
            if ent:
                result.append(ent)
        return result
    return []


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_entry_payload(data: dict | None) -> dict:
    data = dict(data or {})
    on_sensors = data.get(CONF_ON_SENSORS)
    if on_sensors is None:
        on_sensors = data.get(CONF_TRIGGER_SENSORS)
    if on_sensors is None:
        on_sensors = data.get(CONF_MOTION_SENSORS)

    return {
        CONF_NAME: str(data.get(CONF_NAME) or DEFAULT_NAME),
        CONF_ENABLED: _as_bool(data.get(CONF_ENABLED), DEFAULT_ENABLED),
        CONF_TRIGGER_TYPE: str(data.get(CONF_TRIGGER_TYPE) or DEFAULT_TRIGGER_TYPE),
        CONF_ON_ENABLED: _as_bool(data.get(CONF_ON_ENABLED), DEFAULT_ON_ENABLED),
        CONF_ON_SENSORS: _as_list(on_sensors),
        CONF_OFF_ENABLED: _as_bool(data.get(CONF_OFF_ENABLED), DEFAULT_OFF_ENABLED),
        CONF_OFF_SENSORS: _as_list(data.get(CONF_OFF_SENSORS)),
        CONF_USE_ILLUMINANCE: _as_bool(data.get(CONF_USE_ILLUMINANCE), DEFAULT_USE_ILLUMINANCE),
        CONF_ILLUMINANCE_SENSOR: _clean_entity(data.get(CONF_ILLUMINANCE_SENSOR)),
        CONF_TARGET_ENTITY: _clean_entity(data.get(CONF_TARGET_ENTITY) or data.get(CONF_LIGHT)),
        CTRL_OFF_DELAY_MIN: _as_int(data.get(CTRL_OFF_DELAY_MIN), DEFAULT_OFF_DELAY_MIN),
    }


def merge_entry_payload(data: dict | None, options: dict | None) -> dict:
    """Слить data и options записи.

    Options применяются только если реально заданы: пустой options не должен
    затирать data дефолтами (иначе запись «теряет» устройство и сенсоры).
    """
    merged = normalize_entry_payload(data)
    if options:
        merged.update(normalize_entry_payload(options))
    return merged


def _validate(data: dict) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not data.get(CONF_TARGET_ENTITY):
        errors[CONF_TARGET_ENTITY] = "missing_target_entity"
        return errors
    if data.get(CONF_ENABLED, DEFAULT_ENABLED) and data.get(CONF_ON_ENABLED, DEFAULT_ON_ENABLED) and not data.get(CONF_ON_SENSORS):
        errors["base"] = "need_on_sensors"
        return errors
    if data.get(CONF_USE_ILLUMINANCE, DEFAULT_USE_ILLUMINANCE) and not data.get(CONF_ILLUMINANCE_SENSOR):
        errors["base"] = "missing_illuminance_sensor"
    return errors


def _multi_binary_sensor_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=["binary_sensor"], multiple=True))


def _single_sensor_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor"], multiple=False))


def _single_target_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=["light", "switch"], multiple=False))


def build_schema(data: dict, *, include_reset: bool) -> vol.Schema:
    data = normalize_entry_payload(data)
    fields: dict[Any, Any] = {
        vol.Required(CONF_NAME, default=data[CONF_NAME]): str,
        vol.Optional(CONF_ENABLED, default=data[CONF_ENABLED]): selector.BooleanSelector(),
        vol.Optional(CONF_TRIGGER_TYPE, default=data[CONF_TRIGGER_TYPE]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=TRIGGER_TYPE_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key=CONF_TRIGGER_TYPE,
            )
        ),
        vol.Optional(CONF_ON_ENABLED, default=data[CONF_ON_ENABLED]): selector.BooleanSelector(),
        vol.Optional(CONF_ON_SENSORS, default=data[CONF_ON_SENSORS]): _multi_binary_sensor_selector(),
        vol.Optional(CONF_OFF_ENABLED, default=data[CONF_OFF_ENABLED]): selector.BooleanSelector(),
        vol.Optional(CONF_OFF_SENSORS, default=data[CONF_OFF_SENSORS]): _multi_binary_sensor_selector(),
        vol.Optional(CONF_USE_ILLUMINANCE, default=data[CONF_USE_ILLUMINANCE]): selector.BooleanSelector(),
        (vol.Optional(CONF_ILLUMINANCE_SENSOR, default=data[CONF_ILLUMINANCE_SENSOR]) if data[CONF_ILLUMINANCE_SENSOR] else vol.Optional(CONF_ILLUMINANCE_SENSOR)): _single_sensor_selector(),
        vol.Optional(CTRL_OFF_DELAY_MIN, default=data[CTRL_OFF_DELAY_MIN]): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=240, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        (vol.Required(CONF_TARGET_ENTITY, default=data[CONF_TARGET_ENTITY]) if data[CONF_TARGET_ENTITY] else vol.Required(CONF_TARGET_ENTITY)): _single_target_selector(),
    }
    if include_reset:
        fields[vol.Optional(CONF_RESET_OPTIONS, default=False)] = selector.BooleanSelector()
    return vol.Schema(fields)


class MotionControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 8

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                cleaned = normalize_entry_payload(user_input)
                errors = _validate(cleaned)
                if not errors:
                    await self.async_set_unique_id(f"{DOMAIN}:{cleaned[CONF_TARGET_ENTITY]}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=cleaned[CONF_NAME], data=cleaned)
                user_input = cleaned
            except data_entry_flow.AbortFlow:
                # AbortFlow — управляющее исключение Home Assistant, его нельзя
                # глотать общим except (иначе форма просто показывается заново).
                raise
            except Exception:
                _LOGGER.exception("Config flow validation failed")
                errors["base"] = "internal_error"
        return self.async_show_form(step_id="user", data_schema=build_schema(user_input or {}, include_reset=False), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return MotionControlOptionsFlow()


class MotionControlOptionsFlow(config_entries.OptionsFlow):
    # ``config_entry`` — свойство базового класса (HA 2024.11+), задавать его
    # в __init__ нельзя: у свойства нет сеттера (options flow падал).
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                reset = bool(user_input.pop(CONF_RESET_OPTIONS, False))
                if reset:
                    self.hass.config_entries.async_update_entry(self.config_entry, title=self.config_entry.title)
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    return self.async_create_entry(title="", data={})

                cleaned = normalize_entry_payload(user_input)
                errors = _validate(cleaned)
                if not errors:
                    self.hass.config_entries.async_update_entry(self.config_entry, title=cleaned[CONF_NAME])
                    return self.async_create_entry(title="", data=cleaned)
                user_input = cleaned
            except Exception:
                _LOGGER.exception("Options flow validation failed")
                errors["base"] = "internal_error"

        merged = merge_entry_payload(
            self.config_entry.data, self.config_entry.options
        )
        if user_input:
            merged.update(normalize_entry_payload(user_input))
        return self.async_show_form(step_id="init", data_schema=build_schema(merged, include_reset=True), errors=errors)
