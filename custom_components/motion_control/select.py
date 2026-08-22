from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry

from . import async_set_ctrl_value, get_runner
from .const import COLOR_KEEP, COLOR_OPTIONS, CTRL_COLOR, DOMAIN
from .entity_base import MotionControlRestoreBase


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([ColorSelect(hass, entry)])


class ColorSelect(MotionControlRestoreBase, SelectEntity):
    _attr_options = COLOR_OPTIONS
    _attr_icon = "mdi:palette"

    def __init__(self, hass, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._entry_id}_{CTRL_COLOR}"
        self._attr_name = "Цвет"
        self._attr_current_option = COLOR_KEEP

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self._attr_options:
            self._attr_current_option = last.state
        await async_set_ctrl_value(self.hass, self._entry_id, CTRL_COLOR, self._attr_current_option)

    def _apply_runtime_state(self) -> None:
        runner = get_runner(self.hass, self._entry_id)
        if runner:
            option = runner.ctrl.get(CTRL_COLOR, COLOR_KEEP)
            if option in self._attr_options:
                self._attr_current_option = option

    @property
    def current_option(self):
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            return
        self._attr_current_option = option
        self.async_write_ha_state()
        await async_set_ctrl_value(self.hass, self._entry_id, CTRL_COLOR, option)
