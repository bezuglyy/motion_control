from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry

from . import get_runner
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
    DOMAIN,
    build_device_info,
)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([ScenarioStateBinarySensor(hass, entry)])


class ScenarioStateBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Статус сценария"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:motion-sensor"
    _attr_should_poll = False

    def __init__(self, hass, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_scenario_state"
        self._unsub = None

    @property
    def device_info(self):
        return build_device_info(self.entry.entry_id, self.entry.title)

    async def async_added_to_hass(self) -> None:
        from . import async_register_entity_update_listener
        self._unsub = async_register_entity_update_listener(self.hass, self.entry.entry_id, self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @property
    def is_on(self):
        runner = get_runner(self.hass, self.entry.entry_id)
        if not runner:
            return False
        return bool(runner.data.get(ATTR_ACTIVE_ON_SENSORS)) or runner.data.get(ATTR_STATUS) in {"on", "delayed_off"}

    @property
    def extra_state_attributes(self):
        runner = get_runner(self.hass, self.entry.entry_id)
        if not runner:
            return None
        return {
            ATTR_STATUS: runner.data.get(ATTR_STATUS),
            ATTR_LAST_REASON: runner.data.get(ATTR_LAST_REASON),
            ATTR_LAST_ACTION: runner.data.get(ATTR_LAST_ACTION),
            ATTR_LAST_ACTION_AT: runner.data.get(ATTR_LAST_ACTION_AT),
            ATTR_LAST_LUX: runner.data.get(ATTR_LAST_LUX),
            ATTR_ACTIVE_ON_SENSORS: runner.data.get(ATTR_ACTIVE_ON_SENSORS),
            ATTR_ACTIVE_OFF_SENSORS: runner.data.get(ATTR_ACTIVE_OFF_SENSORS),
            ATTR_TARGET_STATE: runner.data.get(ATTR_TARGET_STATE),
            ATTR_NEXT_OFF_AT: runner.data.get(ATTR_NEXT_OFF_AT),
        }
