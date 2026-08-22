from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry

from . import async_set_ctrl_value, get_runner
from .const import (
    CTRL_ILLUMINANCE_BLOCK_LUX,
    CTRL_MAX_BRIGHTNESS_PCT,
    CTRL_MAX_LUX,
    CTRL_MIN_BRIGHTNESS_PCT,
    CTRL_MIN_LUX,
    CTRL_OFF_DELAY_MIN,
    DEFAULT_ILLUMINANCE_BLOCK_LUX,
    DEFAULT_MAX_BRIGHTNESS_PCT,
    DEFAULT_MAX_LUX,
    DEFAULT_MIN_BRIGHTNESS_PCT,
    DEFAULT_MIN_LUX,
    DEFAULT_OFF_DELAY_MIN,
    DOMAIN,
)
from .entity_base import MotionControlRestoreBase


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities(
        [
            CtrlNumber(hass, entry, CTRL_ILLUMINANCE_BLOCK_LUX, "Порог освещённости", DEFAULT_ILLUMINANCE_BLOCK_LUX, 0, 5000, 1, "lx", "mdi:brightness-6"),
            CtrlNumber(hass, entry, CTRL_MIN_LUX, "Минимум освещённости", DEFAULT_MIN_LUX, 0, 2000, 1, "lx", "mdi:brightness-5"),
            CtrlNumber(hass, entry, CTRL_MAX_LUX, "Максимум освещённости", DEFAULT_MAX_LUX, 1, 20000, 1, "lx", "mdi:brightness-7"),
            CtrlNumber(hass, entry, CTRL_MIN_BRIGHTNESS_PCT, "Минимальная яркость", DEFAULT_MIN_BRIGHTNESS_PCT, 1, 100, 1, "%", "mdi:lightbulb-on-10"),
            CtrlNumber(hass, entry, CTRL_MAX_BRIGHTNESS_PCT, "Максимальная яркость", DEFAULT_MAX_BRIGHTNESS_PCT, 1, 100, 1, "%", "mdi:lightbulb-on"),
            CtrlNumber(hass, entry, CTRL_OFF_DELAY_MIN, "Задержка выключения", DEFAULT_OFF_DELAY_MIN, 0, 240, 1, "min", "mdi:timer-outline"),
        ]
    )


class CtrlNumber(MotionControlRestoreBase, NumberEntity):
    def __init__(self, hass, entry: ConfigEntry, field: str, label: str, default: float, min_v: float, max_v: float, step: float, unit: str | None, icon: str):
        super().__init__(hass, entry)
        self._field = field
        self._default = float(default)
        self._attr_unique_id = f"{DOMAIN}_{self._entry_id}_{field}"
        self._attr_name = label
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = float(default)
        self._attr_icon = icon
        self._attr_mode = "slider"

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state not in ("unknown", "unavailable"):
            try:
                self._attr_native_value = float(last.state)
            except ValueError:
                self._attr_native_value = self._default
        runner = get_runner(self.hass, self._entry_id)
        if runner and self._field == CTRL_OFF_DELAY_MIN:
            self._attr_native_value = float(runner.cfg.get(CTRL_OFF_DELAY_MIN, self._attr_native_value))
        await async_set_ctrl_value(self.hass, self._entry_id, self._field, int(self._attr_native_value) if self._field == CTRL_OFF_DELAY_MIN else self._attr_native_value)

    def _apply_runtime_state(self) -> None:
        runner = get_runner(self.hass, self._entry_id)
        if not runner:
            return
        value = runner.ctrl.get(self._field, self._default)
        self._attr_native_value = float(value)

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = float(value)
        self.async_write_ha_state()
        await async_set_ctrl_value(self.hass, self._entry_id, self._field, int(value) if self._field == CTRL_OFF_DELAY_MIN else float(value))
