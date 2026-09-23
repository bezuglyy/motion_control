from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from . import get_runner
from .const import (
    ATTR_LAST_ACTION,
    ATTR_LAST_ACTION_AT,
    ATTR_LAST_LUX,
    ATTR_LAST_REASON,
    ATTR_NEXT_OFF_AT,
    ATTR_STATUS,
    DIAG_ENTITY_CATEGORY,
    DOMAIN,
    build_device_info,
)


@dataclass(frozen=True, kw_only=True)
class Desc(SensorEntityDescription):
    data_key: str


SENSORS: tuple[Desc, ...] = (
    Desc(key="status", name="Статус", icon="mdi:state-machine", data_key=ATTR_STATUS, entity_category=DIAG_ENTITY_CATEGORY),
    Desc(key="last_action", name="Последнее действие", icon="mdi:flash", data_key=ATTR_LAST_ACTION, entity_category=DIAG_ENTITY_CATEGORY),
    Desc(key="last_action_at", name="Время последнего действия", icon="mdi:clock-outline", data_key=ATTR_LAST_ACTION_AT, device_class="timestamp", entity_category=DIAG_ENTITY_CATEGORY),
    Desc(key="last_reason", name="Причина последнего решения", icon="mdi:comment-question", data_key=ATTR_LAST_REASON, entity_category=DIAG_ENTITY_CATEGORY),
    Desc(key="last_lux", name="Текущая освещённость", icon="mdi:brightness-6", data_key=ATTR_LAST_LUX, native_unit_of_measurement="lx", entity_category=DIAG_ENTITY_CATEGORY),
    Desc(key="next_off_at", name="Запланированное выключение", icon="mdi:timer-stop-outline", data_key=ATTR_NEXT_OFF_AT, device_class="timestamp", entity_category=DIAG_ENTITY_CATEGORY),
)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([DiagSensor(hass, entry, desc) for desc in SENSORS])


class DiagSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass, entry: ConfigEntry, desc: Desc) -> None:
        self.hass = hass
        self.entry = entry
        self.entity_description = desc
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{desc.key}"
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
    def native_value(self):
        runner = get_runner(self.hass, self.entry.entry_id)
        if not runner:
            return None
        value = runner.data.get(self.entity_description.data_key)
        # Сенсоры с device_class=timestamp должны отдавать datetime, а не строку
        # (иначе HA падает: "'str' object has no attribute 'tzinfo'").
        if self.entity_description.device_class == "timestamp" and isinstance(value, str):
            return dt_util.parse_datetime(value)
        return value
