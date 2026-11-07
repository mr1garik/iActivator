"""Tiny, fail-safe translator for backend strings.

The Russian text is the key: when the language is "ru" (default) t() returns the
original string unchanged, so Russian behaviour is byte-for-byte identical and the
activation code is never at risk. For "en" it returns the English template below.
t() never raises — a missing translation or a bad placeholder falls back to the
Russian text — so wrapping a log line can never break activation.
"""
from __future__ import annotations

import threading

_lock = threading.Lock()
_lang = "ru"


def set_lang(code: str) -> None:
    global _lang
    with _lock:
        _lang = "en" if code == "en" else "ru"


def get_lang() -> str:
    return _lang


def t(s: str, **kw) -> str:
    tpl = EN.get(s, s) if _lang == "en" else s
    if not kw:
        return tpl
    try:
        return tpl.format(**kw)
    except Exception:
        try:
            return s.format(**kw)
        except Exception:
            return s


# Russian source -> English. Placeholders use {named} fields filled at call sites.
EN: dict[str, str] = {
    # ---- language names (phone language dropdown) ----
    "Украинский": "Ukrainian", "Русский": "Russian", "Английский (США)": "English (US)",
    "Английский (Великобритания)": "English (UK)", "Польский": "Polish", "Немецкий": "German",
    "Французский": "French", "Испанский": "Spanish", "Итальянский": "Italian",
    "Португальский (Бразилия)": "Portuguese (Brazil)", "Турецкий": "Turkish", "Румынский": "Romanian",
    "Чешский": "Czech", "Словацкий": "Slovak", "Венгерский": "Hungarian", "Казахский": "Kazakh",
    "Иврит": "Hebrew", "Арабский": "Arabic", "Китайский (упрощ.)": "Chinese (Simplified)",
    "Китайский (традиц.)": "Chinese (Traditional)", "Японский": "Japanese", "Корейский": "Korean",
    # ---- region names ----
    "Украина": "Ukraine", "Польша": "Poland", "Германия": "Germany", "Чехия": "Czechia",
    "Молдова": "Moldova", "Румыния": "Romania", "Казахстан": "Kazakhstan", "Грузия": "Georgia",
    "Турция": "Turkey", "Великобритания": "United Kingdom", "Франция": "France", "Италия": "Italy",
    "Испания": "Spain", "Израиль": "Israel", "ОАЭ": "UAE", "США": "United States",
    "Канада": "Canada", "Китай": "China",
    # ---- Wi-Fi security labels ----
    "Авто (WPA2/WPA3)": "Auto (WPA2/WPA3)", "Без пароля": "Open (no password)",
    # ---- activation state words ----
    "активирован": "activated", "не активирован": "not activated",
    # ---- step names ----
    "Активация": "Activation", "Язык и регион": "Language & region",
    "Пропуск настроек": "Skip setup", "Wi-Fi": "Wi-Fi",
    # ---- check / lock names ----
    "Устройство": "Device", "Перезагрузки (panic)": "Reboots (panic)",
    "Локатор (блокировка активации)": "Find My (Activation Lock)",
    "MDM (удалённое управление)": "MDM (remote management)", "Профили": "Profiles",
    "Ограничения": "Restrictions", "Батарея": "Battery", "Ёмкость батареи": "Battery capacity",
    "Циклы зарядки": "Charge cycles", "Температура батареи": "Battery temperature",
    "Зарядка": "Charging", "Wi-Fi модуль": "Wi-Fi module", "Bluetooth": "Bluetooth",
    "Модем": "Modem", "Память": "Storage",
    # ---- check / lock details ----
    "нет доступа — разблокируйте iPhone": "no access — unlock the iPhone",
    "Проверка отложена — идёт активация": "Check deferred — activation in progress",
    "Устройство привязано к Apple ID. Нужен пароль владельца или отвязка на icloud.com/find":
        "Device is tied to an Apple ID. The owner's password is needed, or remove it at icloud.com/find",
    "Блокировки нет": "No lock",
    "Сервер Apple не дал однозначного ответа": "Apple's server gave no clear answer",
    "Устройство уже активировано — по USB статус не узнать. "
    "Проверьте на iPhone: Настройки → [имя] → Локатор. "
    "Перед продажей/сбросом его нужно выключить":
        "Device is already activated — the status can't be read over USB. "
        "Check on the iPhone: Settings → [name] → Find My. Turn it off before selling/resetting.",
    "Под контролем этого компьютера (iActivator)": "Supervised by this computer (iActivator)",
    "Не управляется (только пропуск экранов настройки)": "Not managed (setup-screen skipping only)",
    "Не управляется": "Not managed",
    "Запрещена установка/удаление приложений": "Installing/removing apps is blocked",
    "Устройство не сообщило ёмкость": "The device didn't report capacity",
    "Адрес отсутствует — модуль не определяется": "No address — the module isn't detected",
    "Нет версии прошивки модема — модем не запустился": "No modem firmware version — the modem didn't start",
    "IMEI не читается": "IMEI can't be read",
    # ---- check / lock detail templates ----
    "Не удалось проверить (нужен интернет): {e}": "Couldn't check (internet needed): {e}",
    "Не удалось прочитать: {e}": "Couldn't read: {e}",
    "Устройство в корпоративной программе (Apple Business Manager): {org}. "
    "Удалить может только владелец организации":
        "Device is enrolled in a corporate program (Apple Business Manager): {org}. "
        "Only the organization owner can remove it",
    "организация неизвестна": "organization unknown", "неизвестная организация": "unknown organization",
    "Контролируемый режим: {org} (снимается стиранием)": "Supervised mode: {org} (removed by erasing)",
    "Неудаляемые профили: {list}": "Non-removable profiles: {list}",
    "Установлены профили: {list}": "Installed profiles: {list}",
    "Нет доступа к диагностике (разблокируйте iPhone): {e}":
        "No access to diagnostics (unlock the iPhone): {e}",
    "{h}% ({full} из {design} мАч) — {note}": "{h}% ({full} of {design} mAh) — {note}",
    "в норме": "healthy", "износ заметен": "noticeable wear", "рекомендуется замена": "replacement recommended",
    "{t} °C": "{t} °C",
    "Кабель подключён, но заряд ({level}%) не идёт — проверьте кабель, порт или контроллер зарядки":
        "Cable connected, but charge ({level}%) isn't rising — check the cable, port or charging controller",
    "прошивка {v}": "firmware {v}",
    "свободно {free} из {total} ГБ ({pct}%)": "{free} of {total} GB free ({pct}%)",
    "Не удалось прочитать журналы: {e}": "Couldn't read the logs: {e}",
    # ---- panic / crash ----
    "Сбоев за {days} дней нет": "No crashes in {days} days",
    "Прочее: {line}": "Other: {line}", "Неизвестная причина": "Unknown cause",
    "{n} сбоев за {days} дней (последний {when}). {list}":
        "{n} crashes in {days} days (last {when}). {list}",
    # crash-signature hints
    "Не найден датчик — чаще всего шлейф зарядки, микрофон или датчик на шлейфе кнопок":
        "Sensor not found — usually the charge flex, microphone or a sensor on the button flex",
    "Датчик температуры не отвечает — шлейф зарядки/кнопок, батарея или плата":
        "Temperature sensor not responding — charge/button flex, battery or board",
    "Контроллер питания (SMC) — батарея, шлейф зарядки или плата":
        "Power controller (SMC) — battery, charge flex or board",
    "Сопроцессор датчиков (AOP) — датчики, шлейфы или плата":
        "Sensor coprocessor (AOP) — sensors, flex cables or board",
    "Ошибка шины I2C — шлейф или компонент на плате": "I2C bus error — a flex or a board component",
    "Модем — проблема со связью / платой модема": "Modem — radio / modem-board problem",
    "Память (NAND) — неисправность накопителя": "Storage (NAND) — drive failure",
    "Контроллер памяти (ANS) — неисправность накопителя": "Storage controller (ANS) — drive failure",
    "Графический процессор": "Graphics processor (GPU)",
    "Устройство зависло и перезагрузилось (watchdog) — ПО или плата":
        "Device froze and rebooted (watchdog) — software or board",
    # ---- activation / run log ----
    "Подключение к устройству… (если появится «Доверять этому компьютеру?» — нажмите «Доверять»)":
        "Connecting to the device… (if “Trust this computer?” appears, tap “Trust”)",
    "Устройство: {pt} iOS {pv}, состояние: {st}": "Device: {pt} iOS {pv}, state: {st}",
    "ℹ «Пропустить все экраны настройки» выключено — экраны на iPhone нужно пройти вручную.":
        "ℹ “Skip all setup screens” is off — the screens on the iPhone must be completed by hand.",
    "📱 Проведите вверх по экрану iPhone — он перейдёт на главный экран без настроек. "
    "Wi-Fi установлю сразу после этого.":
        "📱 Swipe up on the iPhone screen — it goes to the Home screen without setup. "
        "Wi-Fi will be installed right after.",
    "⚠ iPhone не завершил настройку за 10 минут. Wi-Fi не установлен — "
    "нажмите «Только Wi-Fi», когда iPhone будет на главном экране.":
        "⚠ The iPhone didn't finish setup within 10 minutes. Wi-Fi wasn't installed — "
        "press “Wi-Fi only” once the iPhone is on the Home screen.",
    "не установлен — нажмите «Только Wi-Fi» на главном экране":
        "not installed — press “Wi-Fi only” on the Home screen",
    "✅ Готово. Если iPhone ещё на экране «Привет» — проведите вверх.":
        "✅ Done. If the iPhone is still on the “Hello” screen, swipe up.",
    "iPhone завершил настройку.": "The iPhone finished setup.",
    "Активация не требуется (состояние: {state}).": "Activation not required (state: {state}).",
    "Активация через серверы Apple (интернет компьютера)…":
        "Activating through Apple's servers (computer's internet)…",
    "На устройстве включена Блокировка активации (Найти iPhone). "
    "Введите Apple ID владельца на самом iPhone или снимите устройство с аккаунта "
    "на icloud.com/find. Программа не обходит эту блокировку.":
        "Activation Lock (Find My) is on. Enter the owner's Apple ID on the iPhone itself, or remove "
        "the device from the account at icloud.com/find. This app does not bypass that lock.",
    "Устройство активировано.": "Device activated.",
    "Язык: {language}, регион/локаль: {locale}, часовой пояс: {timezone}":
        "Language: {language}, region/locale: {locale}, time zone: {timezone}",
    "часовой пояс": "time zone", "24-часовой формат": "24-hour format",
    "  ⚠ не удалось установить {what}: {e}": "  ⚠ couldn't set {what}: {e}",
    "Конфигурация уже применена этим компьютером — пропускаю.":
        "Configuration already applied by this computer — skipping.",
    "Пропуск экранов уже настроен — пропускаю.": "Screen skipping already configured — skipping.",
    "Применяю конфигурацию: пропуск экранов настройки": "Applying configuration: skip setup screens",
    " + контролируемый режим…": " + supervised mode…",
    "iPhone уже получил свою конфигурацию настройки (он выходил в интернет во время "
    "настройки, или его настраивали 3uTools / Apple Configurator), и iOS не даёт её заменить. "
    "Нажмите «Стереть…», затем «Запустить» — после стирания экраны будут пропущены.":
        "The iPhone already received its setup configuration (it went online during setup, or was set up "
        "by 3uTools / Apple Configurator), and iOS won't let it be replaced. Press “Erase…”, then "
        "“Run” — after erasing, the screens will be skipped.",
    "Экраны настройки будут пропущены.": "The setup screens will be skipped.",
    "Wi-Fi: «{ssid}», защита {security}, {hidden}{mac}":
        "Wi-Fi: “{ssid}”, security {security}, {hidden}{mac}",
    "скрытая, ": "hidden, ",
    "без случайного MAC": "no random MAC", "частный MAC": "private MAC",
    "  📱 На iPhone: Настройки → «Профиль загружен» (вверху) → Установить. "
    "Чтобы Wi-Fi ставился без нажатий, включите «Контролируемый режим» "
    "(на сброшенном iPhone).":
        "  📱 On the iPhone: Settings → “Profile Downloaded” (top) → Install. "
        "To install Wi-Fi without taps, turn on “Supervised mode” (on a reset iPhone).",
    "  Профиль Wi-Fi установлен и подтверждён устройством.":
        "  Wi-Fi profile installed and confirmed by the device.",
    "устройство не показало профиль после установки":
        "the device didn't show the profile after installation",
    "  попытка {attempt} не удалась: {e}; повтор…": "  attempt {attempt} failed: {e}; retrying…",
    "Не удалось установить профиль Wi-Fi: {e}": "Couldn't install the Wi-Fi profile: {e}",
    "Устройство не контролируется этим компьютером — профиль потребует подтверждения на iPhone.":
        "The device isn't supervised by this computer — the profile will need confirmation on the iPhone.",
    "Стираю устройство (все данные будут удалены)…": "Erasing the device (all data will be removed)…",
    "Команда стирания отправлена. Дождитесь перезагрузки iPhone.":
        "Erase command sent. Wait for the iPhone to reboot.",
    # ---- validation (UserFacingError) ----
    "Не указано имя Wi-Fi сети (SSID).": "No Wi-Fi network name (SSID) given.",
    "В имени сети есть пробелы в начале/конце — уберите их, иначе iPhone не найдёт сеть.":
        "The network name has leading/trailing spaces — remove them, or the iPhone won't find the network.",
    "Пароль WPA/WPA2/WPA3 должен быть от 8 до 63 символов.":
        "A WPA/WPA2/WPA3 password must be 8 to 63 characters.",
    # ---- webui status / journal ----
    "❌ Ошибка: ": "❌ Error: ",
    "✅ {action}: готово за {secs} с": "✅ {action}: done in {secs} s",
    "неисправностей {bad}, замечаний {warn}": "{bad} faults, {warn} warnings",
    "без замечаний": "no issues", "Без замечаний": "No issues",
    "Не удалось получить список устройств: {e}": "Couldn't get the device list: {e}",
    "Введите имя сети": "Enter a network name",
    "Сеть «{ssid}» сохранена (защита {security}{hidden})": "Network “{ssid}” saved (security {security}{hidden})",
    ", скрытая": ", hidden",
    "Сеть «{ssid}» удалена": "Network “{ssid}” removed",
    "Автозапуск с Windows: {state}": "Launch with Windows: {state}",
    "включён": "on", "выключен": "off",
    "Тема оформления: {theme}": "Theme: {theme}",
    "❌ Импорт настроек: {e}": "❌ Settings import: {e}",
    "Не удалось загрузить настройки: {e}": "Couldn't load settings: {e}",
    "✅ Настройки загружены из «{name}»": "✅ Settings loaded from “{name}”",
    "файла": "file",
    "Не выбрано устройство": "No device selected",
    "Язык, регион и режимы": "Language, region and modes",
    # ---- action labels ----
    "Настройка": "Setup", "Стирание": "Erase", "Чтение данных": "Reading data",
    "Локатор и MDM": "Find My and MDM", "Диагностика": "Diagnostics",
    "PDF-отчёт": "PDF report", "Языки устройства": "Device languages", "Проверка данных": "Data check",
    "▶ {action}": "▶ {action}", "▶ {action}: {detail}": "▶ {action}: {detail}",
    "❌ Ошибка: ": "❌ Error: ",
    "✅ Настройки сохранены в файл: {path}": "✅ Settings saved to file: {path}",
    ", история: устройств {n}": ", history: {n} devices",
    "⚠ Не удалось сохранить сеть: {e}": "⚠ Couldn't save the network: {e}",
    # ---- theme names (for the journal line above) ----
    "Как в системе": "System", "Светлая": "Light", "Тёмная": "Dark",
    # ---- PDF report ----
    "Норма": "OK", "Внимание": "Warning", "Неисправность": "Fault", "Инфо": "Info",
    "Готово": "Done", "С замечанием": "With a note", "Ошибка": "Error", "Пропущено": "Skipped",
    "Отчёт о проверке iPhone": "iPhone inspection report",
    "Дата и время проверки": "Inspection date and time",
    "Найдены неисправности: {n}": "Faults found: {n}", "Есть замечания: {n}": "Warnings: {n}",
    "Неисправностей не найдено": "No faults found",
    "Устройство": "Device", "Серийный номер": "Serial number", "IMEI 2": "IMEI 2",
    "Модель": "Model", "Память": "Storage", "Модем": "Modem",
    "Батарея": "Battery", "Ёмкость (здоровье)": "Capacity (health)",
    "Текущая / заводская": "Current / design", "Циклы зарядки": "Charge cycles", "Заряд сейчас": "Charge now",
    "Ход активации (последний запуск)": "Activation run (last run)", "Проверка": "Checks",
    "Создано в iActivator {ver} · {stamp}": "Made with iActivator {ver} · {stamp}",
    "стр. {n}": "p. {n}",
    "мАч": "mAh",
}
