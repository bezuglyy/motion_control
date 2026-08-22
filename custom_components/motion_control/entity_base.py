from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.restore_state import RestoreEntity

from . import async_register_entity_update_listener, get_runner
from .const import build_device_info


class MotionControlRestoreBase(RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, hass, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._entry_id = entry.entry_id
        self._unsub_runtime = None

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_info(self):
        return build_device_info(self._entry_id, self._entry.title)

    async def async_added_to_hass(self):
        self._unsub_runtime = async_register_entity_update_listener(self.hass, self._entry_id, self._handle_runtime_update)

    async def async_will_remove_from_hass(self):
        if self._unsub_runtime:
            self._unsub_runtime()
            self._unsub_runtime = None

    def _handle_runtime_update(self) -> None:
        self._apply_runtime_state()
        self.async_write_ha_state()

    def _apply_runtime_state(self) -> None:
        _ = get_runner(self.hass, self._entry_id)
