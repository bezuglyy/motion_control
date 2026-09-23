# Включение по движению
![Release](https://img.shields.io/github/v/release/bezuglyy/motion_control?label=Release&style=flat-square) ![HACS](https://img.shields.io/badge/HACS-Custom%20Repository-purple?style=flat-square) ![License](https://img.shields.io/github/license/bezuglyy/motion_control?style=flat-square) ![HA](https://img.shields.io/badge/HA-2025.1%2B-2ea44f?style=flat-square)
Кастомная интеграция для [Home Assistant](https://www.home-assistant.io) · версия **1.0.1**.
![icon](custom_components/motion_control/brand/icon.png)
| | |
|---|---|
| Домен | `motion_control` |
| Версия | 1.0.1 |
| Тип | custom integration |
## Описание
Включение устройств (освещения) по датчику движения с учётом времени суток.
### Возможности
- Бинарные датчики (движение, контакты и т.п.)
- Числовые настройки и параметры
- Выбор режимов и опций
- Сенсоры и мониторинг состояния
- Таймеры и расписания
### Установка
1. Скопируйте папку `custom_components/motion_control/` в каталог `custom_components/` конфигурации Home Assistant.
2. Перезапустите Home Assistant.
3. Настройки → Устройства и службы → Добавить интеграцию → **Включение по движению**.
> Установка через HACS: добавьте репозиторий `https://github.com/bezuglyy/motion_control` как Custom repository (категория Integration).
---
## Description
Turn devices (lights) on by motion sensor with day/night awareness.
### Features
- Binary sensors (motion, contacts, etc.)
- Number settings and parameters
- Mode and option selectors
- Sensors and state monitoring
- Timers and schedules
### Installation
1. Copy the `custom_components/motion_control/` folder into the `custom_components/` directory of your Home Assistant configuration.
2. Restart Home Assistant.
3. Settings → Devices & Services → Add Integration → **Включение по движению**.
> HACS: add `https://github.com/bezuglyy/motion_control` as a Custom repository (category Integration).
---
## Изменения 1.0.2 (23.09.2026)

Исправлены 4 дефекта, из-за которых интеграция могла не работать:

1. **Настройки записи терялись.** При пустом `options` данные записи затирались
   значениями по умолчанию (в диагностике `status = missing_target`, устройство и
   сенсоры «пропадали») — слияние `data` и `options` переписано.
2. **Окно настроек (Options) не открывалось** — `AttributeError: property 'config_entry'
   has no setter` (в Home Assistant 2024.11+ `config_entry` — свойство базового класса).
3. **Сбои при первом действии** — `datetime.now(hass.config.time_zone)`: в современных
   версиях HA `time_zone` — строка, теперь используется `dt_util.now()`.
4. **Диагностические сенсоры времени падали** (`device_class: timestamp` получал строку) —
   теперь отдаётся корректный `datetime`.

Дополнительно: `AbortFlow` больше не проглатывается общим `except` — повторное добавление
той же записи корректно отбрасывается. Добавлены HA-тесты (6 проверок).

### Changes 1.0.2
Fixed 4 defects: entry settings were overwritten by defaults when `options` was empty;
the options dialog failed to open on Home Assistant 2024.11+; `datetime.now(config.time_zone)`
raised `TypeError`; timestamp diagnostic sensors crashed. `AbortFlow` is no longer swallowed.

---
**Автор / Author:**
![Bezuglyj E.N.](logo-bezuglyj.png)
## License / Лицензия
MIT
