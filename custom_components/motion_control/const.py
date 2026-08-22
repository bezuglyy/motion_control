from __future__ import annotations

from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "motion_control"
PLATFORMS = ["binary_sensor", "number", "select", "sensor", "time"]

CONF_NAME = "name"
CONF_ENABLED = "enabled"
CONF_TRIGGER_TYPE = "trigger_type"
CONF_ON_ENABLED = "on_enabled"
CONF_ON_SENSORS = "on_sensors"
CONF_OFF_ENABLED = "off_enabled"
CONF_OFF_SENSORS = "off_sensors"
CONF_USE_ILLUMINANCE = "use_illuminance"
CONF_ILLUMINANCE_SENSOR = "illuminance_sensor"
CONF_TARGET_ENTITY = "target_entity"
CONF_RESET_OPTIONS = "reset_options"

# legacy keys
CONF_TRIGGER_SENSORS = "trigger_sensors"
CONF_MOTION_SENSORS = "motion_sensors"
CONF_LIGHT = "light"

TRIGGER_MOTION = "motion"
TRIGGER_OPENING = "opening"
TRIGGER_ANY = "any"
TRIGGER_TYPE_OPTIONS = [TRIGGER_MOTION, TRIGGER_OPENING, TRIGGER_ANY]

DEFAULT_NAME = "Включение по движению"
DEFAULT_ENABLED = True
DEFAULT_ON_ENABLED = True
DEFAULT_OFF_ENABLED = True
DEFAULT_USE_ILLUMINANCE = False
DEFAULT_TRIGGER_TYPE = TRIGGER_MOTION
DEFAULT_OFF_DELAY_MIN = 1
DEFAULT_MIN_LUX = 0.0
DEFAULT_MAX_LUX = 200.0
DEFAULT_MIN_BRIGHTNESS_PCT = 10.0
DEFAULT_MAX_BRIGHTNESS_PCT = 100.0
DEFAULT_ILLUMINANCE_BLOCK_LUX = 100.0
DEFAULT_START_TIME = "00:00:00"
DEFAULT_END_TIME = "23:59:59"

CTRL_OFF_DELAY_MIN = "off_delay_min"
CTRL_MIN_LUX = "min_lux"
CTRL_MAX_LUX = "max_lux"
CTRL_MIN_BRIGHTNESS_PCT = "min_brightness_pct"
CTRL_MAX_BRIGHTNESS_PCT = "max_brightness_pct"
CTRL_START_TIME = "start_time"
CTRL_END_TIME = "end_time"
CTRL_COLOR = "color"
CTRL_ILLUMINANCE_BLOCK_LUX = "illuminance_block_lux"

COLOR_KEEP = "Не менять"
COLOR_WARM = "Тёплый"
COLOR_NEUTRAL = "Нейтральный"
COLOR_COOL = "Холодный"
COLOR_RED = "Красный"
COLOR_GREEN = "Зелёный"
COLOR_BLUE = "Синий"
COLOR_PURPLE = "Фиолетовый"
COLOR_PINK = "Розовый"

COLOR_OPTIONS = [
    COLOR_KEEP,
    COLOR_WARM,
    COLOR_NEUTRAL,
    COLOR_COOL,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_PURPLE,
    COLOR_PINK,
]

COLOR_HS_MAP = {
    COLOR_WARM: (30.0, 70.0),
    COLOR_NEUTRAL: (45.0, 25.0),
    COLOR_COOL: (200.0, 40.0),
    COLOR_RED: (0.0, 100.0),
    COLOR_GREEN: (120.0, 100.0),
    COLOR_BLUE: (240.0, 100.0),
    COLOR_PURPLE: (275.0, 80.0),
    COLOR_PINK: (330.0, 70.0),
}

DEFAULT_CTRL_VALUES = {
    CTRL_OFF_DELAY_MIN: DEFAULT_OFF_DELAY_MIN,
    CTRL_MIN_LUX: DEFAULT_MIN_LUX,
    CTRL_MAX_LUX: DEFAULT_MAX_LUX,
    CTRL_MIN_BRIGHTNESS_PCT: DEFAULT_MIN_BRIGHTNESS_PCT,
    CTRL_MAX_BRIGHTNESS_PCT: DEFAULT_MAX_BRIGHTNESS_PCT,
    CTRL_START_TIME: DEFAULT_START_TIME,
    CTRL_END_TIME: DEFAULT_END_TIME,
    CTRL_COLOR: COLOR_KEEP,
    CTRL_ILLUMINANCE_BLOCK_LUX: DEFAULT_ILLUMINANCE_BLOCK_LUX,
}

DATA_RUNTIME = "runtime"
EVENT_UPDATE = f"{DOMAIN}_update"

ATTR_STATUS = "status"
ATTR_LAST_REASON = "last_reason"
ATTR_LAST_ACTION = "last_action"
ATTR_LAST_ACTION_AT = "last_action_at"
ATTR_LAST_LUX = "last_lux"
ATTR_ACTIVE_ON_SENSORS = "active_on_sensors"
ATTR_ACTIVE_OFF_SENSORS = "active_off_sensors"
ATTR_TARGET_STATE = "target_state"
ATTR_NEXT_OFF_AT = "next_off_at"

INTEGRATION_MANUFACTURER = "Bezuglyy"
INTEGRATION_MODEL = "Включение по движению"
INTEGRATION_SW_VERSION = "3.1.0"

DIAG_ENTITY_CATEGORY = EntityCategory.DIAGNOSTIC


def build_device_info(entry_id: str, entry_title: str | None = None) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=entry_title or DEFAULT_NAME,
        manufacturer=INTEGRATION_MANUFACTURER,
        model=INTEGRATION_MODEL,
        sw_version=INTEGRATION_SW_VERSION,
    )
