from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry

from . import async_set_ctrl_value, get_runner
from .const import CTRL_END_TIME, CTRL_START_TIME, DEFAULT_END_TIME, DEFAULT_START_TIME, DOMAIN
from .entity_base import MotionControlRestoreBase


def _parse(value: str, fallback: dt_time) -> dt_time:
    try:
        parts = (value or "").split(":")
        hh = int(parts[0])
        mm = int(parts[1])
        ss = int(parts[2]) if len(parts) > 2 else 0
        return dt_time(hh, mm, ss)
    except Exception:
        return fallback


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities(
        [
            MotionControlTime(hass, entry, CTRL_START_TIME, "Время начала", _parse(DEFAULT_START_TIME, dt_time(0, 0, 0)), "mdi:clock-start"),
            MotionControlTime(hass, entry, CTRL_END_TIME, "Время окончания", _parse(DEFAULT_END_TIME, dt_time(23, 59, 59)), "mdi:clock-end"),
        ]
    )


class MotionControlTime(MotionControlRestoreBase, TimeEntity):
    def __init__(self, hass, entry: ConfigEntry, field: str, label: str, default: dt_time, icon: str) -> None:
        super().__init__(hass, entry)
        self._field = field
        self._attr_unique_id = f"{DOMAIN}_{self._entry_id}_{field}"
        self._attr_name = label
        self._attr_native_value = default
        self._attr_icon = icon

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unknown", "unavailable"):
            self._attr_native_value = _parse(last.state, self._attr_native_value)
        await async_set_ctrl_value(self.hass, self._entry_id, self._field, self._attr_native_value)

    def _apply_runtime_state(self) -> None:
        runner = get_runner(self.hass, self._entry_id)
        if runner:
            self._attr_native_value = _parse(str(runner.ctrl.get(self._field)), self._attr_native_value)

    async def async_set_value(self, value: dt_time) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
        await async_set_ctrl_value(self.hass, self._entry_id, self._field, value)
