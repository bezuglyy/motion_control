# Включение по движению

Кастомная интеграция для [Home Assistant](https://www.home-assistant.io) · версия **1.0.1**.

![icon](custom_components/motion_control/brand/icon.png)

| | |
|---|---|
| Домен | `motion_control` |
| Версия | 1.0.1 |
| Тип | custom integration |

## Описание

Включение устройств (освещения) по датчику движения с учётом времени суток.

## Возможности

- Бинарные датчики (движение, контакты и т.п.)
- Числовые настройки и параметры
- Выбор режимов и опций
- Сенсоры и мониторинг состояния
- Таймеры и расписания

## Установка

1. Скопируйте папку `custom_components/{domain}/` в каталог `custom_components/` конфигурации Home Assistant.
2. Перезапустите Home Assistant.
3. Настройки → Устройства и службы → Добавить интеграцию → **{mname}**.

> Установка через HACS: добавьте репозиторий `https://github.com/bezuglyy/{repo}` как Custom repository (категория Integration).

## Лицензия

MIT
