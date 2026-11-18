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


LANGS = ("ru", "en", "uk", "pl", "es", "de")


def set_lang(code: str) -> None:
    global _lang
    with _lock:
        _lang = code if code in LANGS else "ru"


def get_lang() -> str:
    return _lang


def t(s: str, **kw) -> str:
    table = TABLES.get(_lang)
    if table is None:
        tpl = s                       # Russian: the key is the text
    else:
        tpl = table.get(s)
        if tpl is None:
            tpl = EN.get(s, s)        # a newer language falls back to English, then to Russian
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
    # verdict
    "Годен": "Pass", "Не годен": "Fail", "Годен с замечаниями": "Pass with notes",
    # self-update
    "Автообновление доступно только в установленной программе.": "Auto-update is only available in the installed app.",
    "Нет доступного обновления.": "No update available.",
    "Загружаю обновление…": "Downloading the update…",
    "Устанавливаю обновление и перезапускаю…": "Installing the update and restarting…",
    "Не удалось найти установленную программу для замены.": "Couldn't find the installed app to replace.",
    # ---- legacy activation (iOS < 10) ----
    "Старая iOS ({pv}): активация через lockdown (без сессии).":
        "Old iOS ({pv}): activating through lockdown (no session).",
    "iPhone не выдал данные для активации: {e}. Разблокируйте экран, проверьте кабель и что в телефон вставлена SIM-карта, затем повторите.":
        "The iPhone did not provide its activation data: {e}. Unlock the screen, check the cable and that a SIM card is inserted, then try again.",
    "  ⚠ SIM-карта не обнаружена. Старые iPhone обычно не активируются без SIM.":
        "  ⚠ No SIM card detected. Old iPhones usually cannot be activated without a SIM.",
    "Сервер Apple не выдал запись активации для этого устройства.":
        "Apple's server did not return an activation record for this device.",
    "Вставьте рабочую SIM-карту и повторите.":
        "Insert a working SIM card and try again.",
    "⚠ Старая iOS не приняла пропуск экранов ({e}) — пройдите их на iPhone вручную.":
        "⚠ This old iOS did not accept skipping the setup screens ({e}) — go through them on the iPhone manually.",
    "не поддерживается этой версией iOS":
        "not supported by this iOS version",
    # ---- journal, diagnostics, history: strings that were left untranslated ----
    "Прочее: ": "Other: ",
    "{n} сбоев за {days} дней (последний {last}). ": "{n} crashes in {days} days (latest {last}). ",
    "Неудаляемые профили: ": "Non-removable profiles: ",
    "Установлены профили: ": "Installed profiles: ",
    "прошивка {fw}": "firmware {fw}",
    "Замечания": "Warnings",
    "Успешно": "Success",
    "Дата и время": "Date and time",
    "Действие": "Action",
    "Подробности": "Details",
    "Результат": "Result",
    "Серийный №": "Serial no.",
    "iPhone SE (1-го поколения)": "iPhone SE (1st generation)",
    "iPhone SE (2-го поколения)": "iPhone SE (2nd generation)",
    "iPhone SE (3-го поколения)": "iPhone SE (3rd generation)",
    "{n} ГБ": "{n} GB",
    "{n} ТБ": "{n} TB",
    "Отчёты": "Reports",
    "Это не файл настроек iActivator": "This is not an iActivator settings file",
    " (без паролей)": " (without passwords)",
    " (с паролями: {n})": " (with passwords: {n})",
    "Сети Wi-Fi: {n}": "Wi-Fi networks: {n}",
    "Тема оформления": "Theme",
    "Ключ контролируемого режима": "Supervision key",
    "⚠ Ключ контролируемого режима не заменён: на этом компьютере уже есть свой": "⚠ Supervision key not replaced: this computer already has its own",
    "История: устройств {n}": "History: {n} devices",
    "Показать окно": "Show window",
    "Выход": "Quit",
    "Проверка обновлений не удалась: {kind}: {e}": "Update check failed: {kind}: {e}",
    "Диагностика: проверяю…": "Diagnostics: checking…",
    "📄 Отчёт сохранён: {path}": "📄 Report saved: {path}",
    ", батарея {h}%": ", battery {h}%",
    "Подключение": "Connection",
    "Подключён {model}": "Connected {model}",
    "Уже выполняется другая операция": "Another operation is already running",
    "как в системе": "same as system",
    "светлая": "light",
    "тёмная": "dark",
    "iActivator-настройки-{date}.json": "iActivator-settings-{date}.json",
    "❌ Не удалось сохранить настройки: {e}": "❌ Could not save the settings: {e}",
    "Не удалось сохранить файл: {e}": "Could not save the file: {e}",
    "  Сети Wi-Fi: {n}": "  Wi-Fi networks: {n}",
    ", без паролей": ", without passwords",
    ", с паролями": ", with passwords",
    ", ключ контролируемого режима": ", supervision key",
    "-без-номеров": "-no-numbers",
    "iActivator-журнал{suffix}-{date}.txt": "iActivator-journal{suffix}-{date}.txt",
    "=== iActivator — журнал для диагностики ===": "=== iActivator — journal for diagnosis ===",
    "Создан: {when}": "Created: {when}",
    "Версия: {v}   Система: {sys}   Python: {py}   pymobiledevice3: {pmd}": "Version: {v}   System: {sys}   Python: {py}   pymobiledevice3: {pmd}",
    "Серийные номера, IMEI и UDID скрыты (***); история устройств не включена.": "Serial numbers, IMEI and UDID are hidden (***); device history is not included.",
    "=== ЗАПИСИ ЖУРНАЛА (файлов: {n}) ===": "=== JOURNAL ENTRIES (files: {n}) ===",
    "(не удалось прочитать: {e})": "(could not read: {e})",
    "=== ЗАПИСЕЙ ЖУРНАЛА ПОКА НЕТ ===": "=== NO JOURNAL ENTRIES YET ===",
    "=== ИСТОРИЯ УСТРОЙСТВ (JSON) ===": "=== DEVICE HISTORY (JSON) ===",
    "❌ Не удалось сохранить журнал: {e}": "❌ Could not save the journal: {e}",
    "✅ Журнал сохранён в файл: {path}": "✅ Journal saved to file: {path}",
    "iActivator {v} запущен · {sys} · Python {py}": "iActivator {v} started · {sys} · Python {py}",
    # ---- self-update: verification and backup ----
    "❌ Обновление не установлено: {e}. Программа осталась прежней.": "❌ Update not installed: {e}. The app was left unchanged.",
    "Загрузка оборвалась ({got} из {total} байт). Повторите позже.": "The download was cut off ({got} of {total} bytes). Try again later.",
    "Скачанный файл слишком мал и не похож на программу.": "The downloaded file is too small to be the app.",
    "Скачанный файл повреждён (контрольная сумма не совпала).": "The downloaded file is damaged (checksum mismatch).",
    "Скачанный файл не является программой Windows.": "The downloaded file is not a Windows program.",
    "Скачанный архив повреждён.": "The downloaded archive is damaged.",
    "Предыдущая версия будет сохранена в: {path}": "The previous version will be kept in: {path}",
    "Предыдущая версия сохранена в: {path}": "The previous version was saved to: {path}",
    "⚠ Не удалось сохранить предыдущую версию: {e}": "⚠ Could not save the previous version: {e}",
    "Обновление распаковалось неправильно — программа не тронута.": "The update did not unpack correctly — the app was left unchanged.",
    # ---- Apple driver (Windows) ----
    "На этой системе отдельный драйвер не нужен.": "No separate driver is needed on this system.",
    "Драйвер Apple не установлен. Установите приложение «Apple Devices» из Microsoft Store (или iTunes), затем перезапустите iActivator.": "The Apple driver is not installed. Install the “Apple Devices” app from the Microsoft Store (or iTunes), then restart iActivator.",
    "Apple Devices из Microsoft Store": "Apple Devices from the Microsoft Store",
    "Служба Apple ({source}) не отвечает. Перезапустите её — Windows попросит разрешение администратора.": "The Apple service ({source}) is not responding. Restart it — Windows will ask for administrator permission.",
    "Windows видит iPhone, но драйвер работает с ошибкой ({name}: {status}). Переустановите драйвер iPhone.": "Windows sees the iPhone, but its driver reports an error ({name}: {status}). Reinstall the iPhone driver.",
    "Windows видит iPhone, но служба Apple — нет: у телефона не тот драйвер. Переустановите драйвер iPhone.": "Windows sees the iPhone, but the Apple service doesn't: the phone has the wrong driver. Reinstall the iPhone driver.",
    "Драйвер Apple работает ({source}), iPhone виден.": "The Apple driver works ({source}); the iPhone is visible.",
    "Драйвер Apple работает ({source}). Подключите iPhone кабелем и разблокируйте его.": "The Apple driver works ({source}). Connect the iPhone with a cable and unlock it.",
    "Windows не завершил операцию вовремя. Перезагрузите компьютер и повторите.": "Windows did not finish in time. Restart the computer and try again.",
    "Нужно разрешение администратора — операция отменена.": "Administrator permission is needed — the operation was cancelled.",
    "Не удалось выполнить операцию.": "The operation failed.",
    "Доступно только на Windows.": "Available on Windows only.",
    "Драйвер Apple: {action}…": "Apple driver: {action}…",
    "✅ Драйвер Apple: {action} — готово": "✅ Apple driver: {action} — done",
    "❌ Драйвер Apple: {e}": "❌ Apple driver: {e}",
    "Драйвер Apple: {message}": "Apple driver: {message}",
    "установка Apple Devices": "installing Apple Devices",
    "перезапуск службы": "restarting the service",
    "переустановка драйвера iPhone": "reinstalling the iPhone driver",
    # ---- SIM and carrier lock ----
    "SIM-карта": "SIM card",
    "Привязка к оператору": "Carrier lock",
    "Не вставлена": "Not inserted",
    "Вставьте SIM-карту, чтобы проверить привязку к оператору": "Insert a SIM card to check the carrier lock",
    "iPhone не принимает эту SIM ({carrier})": "The iPhone does not accept this SIM ({carrier})",
    "Похоже, iPhone привязан к другому оператору (SIM-lock). Проверьте по IMEI у оператора или продавца": "The iPhone seems to be locked to another carrier (SIM lock). Check the IMEI with the carrier or the seller",
    "Работает · {carrier} · ICCID {tail}": "Working · {carrier} · ICCID {tail}",
    "С этой SIM телефон работает. Полностью проверить привязку по USB нельзя: вставьте SIM другого оператора — если iPhone привязан, здесь будет предупреждение": "The phone works with this SIM. The lock can't be fully checked over USB: insert a SIM from another carrier — if the iPhone is locked, a warning will appear here",
    "Заблокирована PIN-кодом — введите PIN на iPhone": "Locked with a PIN — enter the PIN on the iPhone",
    "Заблокирована PUK-кодом — нужен PUK от оператора": "Locked with a PUK — get the PUK from the carrier",
    "Ещё не готова — подождите немного и проверьте снова": "Not ready yet — wait a moment and check again",
    "Ошибка SIM-карты — проверьте SIM или лоток": "SIM card error — check the SIM or the tray",
    "SIM-карта заблокирована оператором": "The SIM card is blocked by the carrier",
    "Включён режим разрешённых номеров (FDN)": "Fixed dialing (FDN) is on",
    "Состояние: {state}": "Status: {state}",
    # ---- replaced parts ----
    "Системная плата": "Logic board",
    "Дисплей": "Display",
    "Основная камера": "Main camera",
    "Сверхширокоугольная камера": "Ultra-wide camera",
    "Телекамера": "Telephoto camera",
    "Фронтальная камера": "Front camera",
    "Face ID": "Face ID",
    "Touch ID": "Touch ID",
    "Детали": "Parts",
    "Эта версия iOS не сообщает серийные номера деталей по USB": "This iOS version doesn't report part serial numbers over USB",
    "Записаны серийные номера: {parts}. При следующих проверках программа сообщит, если какую-то из этих деталей заменят": "Serial numbers recorded: {parts}. Later checks will report if any of these parts is replaced",
    "Заменено после проверки {date}: {parts}": "Replaced since the check on {date}: {parts}",
    "Нечего сравнить с прошлой проверкой — записаны: {parts}": "Nothing to compare with the earlier check — recorded: {parts}",
    "Не менялись с проверки {date} ({parts})": "Unchanged since the check on {date} ({parts})",
    # ---- several iPhones ----
    "Очередь: {label} отключён — пропускаю": "Queue: {label} was unplugged — skipping",
    "Авто-режим: {label} — в очереди ({n})": "Auto mode: {label} — waiting ({n})",
    "Авто-режим: {label} уже активирован — пропускаю": "Auto mode: {label} is already activated — skipping",
    "⛔ Авто-режим остановлен: {reason}": "⛔ Auto mode stopped: {reason}",
    "Нет ответа от iPhone или службы Apple за {n} с": "No answer from the iPhone or the Apple service in {n} s",
    # ---- colour themes ----
    "синяя ночь": "blue night",
    "мятная": "mint",
    "графит": "graphite",
    "Обновление установится и программа откроется снова через несколько секунд.": "The update will install and the app will open again in a few seconds.",
    "Автозапуск: путь к программе обновлён": "Start-up with Windows: path to the app updated",
    "Имя": "Name",
    "Событий нет": "No events",
    "Впервые подключён": "First connected",
    "Последний раз": "Last seen",
    "Серийные номера деталей (записаны {time})": "Part serial numbers (recorded {time})",
    "События ({n})": "Events ({n})",
    "Создано в iActivator {time}": "Made with iActivator {time}",
    "Этого устройства нет в истории.": "This device is not in the history.",
    "TXT-файлы сохранены: {n}": "TXT files saved: {n}",
    "Удалено файлов: {n}, освобождено {size}": "Files deleted: {n}, freed {size}",
    "{n} КБ": "{n} KB",
    "{n} МБ": "{n} MB",
    "Батарея (здоровье)": "Battery (health)",
    "История очищена: устройств {d}, файлов {n}, освобождено {size}": "History cleared: {d} devices, {n} files, {size} freed",
    "Нет связи с сервером Apple — проверьте интернет на компьютере: {e}": "No connection to Apple's server — check the computer's internet: {e}",
    "iPhone не дал проверить ({e}). Проверьте после активации: Настройки → [имя] → Локатор": "The iPhone didn't allow the check ({e}). Check after activation: Settings → [name] → Find My",
    "До активации этот iPhone не даёт прочитать — проверьте после активации": "This iPhone doesn't allow reading it before activation — check after activation",
    "новая батарея: ёмкость выше заводской, это нормально": "new battery: capacity above the factory rating, this is normal",
    "новая батарея": "new battery",
    "Заметка": "Note",
    "{action}: готово": "{action}: done",
    "{action}: ошибка": "{action}: error",
    "Автоочистка (старше {days} дн.): устройств {d}, файлов {n}, освобождено {size}": "Auto cleanup (older than {days} days): {d} devices, {n} files, {size} freed",
    "Наклейка": "Sticker",
    "Наклейки": "Stickers",
    "Не удалось сделать наклейку: {e}": "Couldn't make the sticker: {e}",
    "🏷 Наклейки сохранены: {n} · {name}": "🏷 Stickers saved: {n} · {name}",
    "Не найден шрифт с кириллицей для PDF": "No font with Cyrillic found for the PDF",
    "Вход прерван. Начните заново.": "The sign-in was interrupted. Start again.",
    "Apple просит подтверждение, но не прислала полей для ввода. Повторите вход владельца на самом iPhone.": "Apple asks for confirmation but sent no fields to fill in. Sign in as the owner on the iPhone itself.",
    "Apple вернула неожиданный ответ. Повторите позже.": "Apple returned an unexpected response. Try again later.",
    "Дождитесь окончания текущей операции.": "Wait for the current operation to finish.",
    "Вход владельца Apple ID для снятия блокировки активации…": "Owner Apple ID sign-in to clear Activation Lock…",
    "Вход владельца Apple ID": "Owner Apple ID sign-in",
    "✅ Блокировка активации снята входом владельца.": "✅ Activation Lock cleared by the owner's sign-in.",
    "Вход Apple ID": "Apple ID sign-in",
    "Не удалось открыть браузер. Ссылка: {url}": "Could not open the browser. Link: {url}",
    "Устройство привязано к Apple ID. Снимается входом владельца: пароль Apple ID (кнопка ниже), или на самом iPhone «Разблокировать с помощью код-пароля?» и старый код-пароль устройства (iOS 15.2+), или отвязка на icloud.com/find": "This device is tied to an Apple ID. Clear it by the owner signing in: the Apple ID password (button below), or on the iPhone itself \"Unlock with Passcode?\" and the device's old passcode (iOS 15.2+), or remove it at icloud.com/find",
    "На этой iOS статус Локатора до активации по USB не читается. Проверьте после активации на iPhone: Настройки → [имя] → Локатор": "On this iOS the Find My / Activation Lock status cannot be read over USB before activation. Check after activation on the iPhone: Settings → [name] → Find My",
    "Введите название профиля.": "Enter a profile name.",
    "Профиль сохранён: {name}": "Profile saved: {name}",
    "Создано в iActivator": "Made with iActivator",
    "Акт приёма устройства": "Device intake report",
    "Акт выдачи устройства": "Device handover report",
    "Гарантийный талон": "Warranty certificate",
    "Документ": "Document",
    "Дата": "Date",
    "Клиент": "Customer",
    "Состояние / дефекты": "Condition / defects",
    "Выполненные работы": "Work done",
    "Стоимость": "Price",
    "Гарантия": "Warranty",
    "{n} мес. (до {date})": "{n} mo. (until {date})",
    "Гарантия не распространяется на механические повреждения, попадание жидкости и следы самостоятельного ремонта. Сохраняйте этот талон.": "The warranty does not cover mechanical damage, liquid ingress or signs of self-repair. Keep this certificate.",
    "Сдал (клиент)": "Handed in (customer)",
    "Получил (клиент)": "Received (customer)",
    "Принял (сервис)": "Accepted (service)",
    "Выдал (сервис)": "Issued (service)",
    "Сервис": "Service",
    "Не удалось создать документ: {e}": "Could not create the document: {e}",
    "📄 Документ сохранён: {name}": "📄 Document saved: {name}",
}

# Russian source -> Ukrainian.
UK: dict[str, str] = {
    # language names
    "Украинский": "Українська", "Русский": "Російська", "Английский (США)": "Англійська (США)",
    "Английский (Великобритания)": "Англійська (Велика Британія)", "Польский": "Польська", "Немецкий": "Німецька",
    "Французский": "Французька", "Испанский": "Іспанська", "Итальянский": "Італійська",
    "Португальский (Бразилия)": "Португальська (Бразилія)", "Турецкий": "Турецька", "Румынский": "Румунська",
    "Чешский": "Чеська", "Словацкий": "Словацька", "Венгерский": "Угорська", "Казахский": "Казахська",
    "Иврит": "Іврит", "Арабский": "Арабська", "Китайский (упрощ.)": "Китайська (спрощ.)",
    "Китайский (традиц.)": "Китайська (традиц.)", "Японский": "Японська", "Корейский": "Корейська",
    # region names
    "Украина": "Україна", "Польша": "Польща", "Германия": "Німеччина", "Чехия": "Чехія",
    "Молдова": "Молдова", "Румыния": "Румунія", "Казахстан": "Казахстан", "Грузия": "Грузія",
    "Турция": "Туреччина", "Великобритания": "Велика Британія", "Франция": "Франція", "Италия": "Італія",
    "Испания": "Іспанія", "Израиль": "Ізраїль", "ОАЭ": "ОАЕ", "США": "США",
    "Канада": "Канада", "Китай": "Китай",
    # Wi-Fi security
    "Авто (WPA2/WPA3)": "Авто (WPA2/WPA3)", "Без пароля": "Без пароля",
    # activation state words
    "активирован": "активований", "не активирован": "не активований",
    # step names
    "Активация": "Активація", "Язык и регион": "Мова і регіон",
    "Пропуск настроек": "Пропуск налаштувань", "Wi-Fi": "Wi-Fi",
    # check / lock names
    "Устройство": "Пристрій", "Перезагрузки (panic)": "Перезавантаження (panic)",
    "Локатор (блокировка активации)": "Локатор (блокування активації)",
    "MDM (удалённое управление)": "MDM (віддалене керування)", "Профили": "Профілі",
    "Ограничения": "Обмеження", "Батарея": "Батарея", "Ёмкость батареи": "Ємність батареї",
    "Циклы зарядки": "Цикли заряджання", "Температура батареи": "Температура батареї",
    "Зарядка": "Заряджання", "Wi-Fi модуль": "Wi-Fi модуль", "Bluetooth": "Bluetooth",
    "Модем": "Модем", "Память": "Пам'ять",
    # check / lock details
    "нет доступа — разблокируйте iPhone": "немає доступу — розблокуйте iPhone",
    "Проверка отложена — идёт активация": "Перевірку відкладено — триває активація",
    "Устройство привязано к Apple ID. Нужен пароль владельца или отвязка на icloud.com/find":
        "Пристрій прив'язаний до Apple ID. Потрібен пароль власника або від'єднання на icloud.com/find",
    "Блокировки нет": "Блокування немає",
    "Сервер Apple не дал однозначного ответа": "Сервер Apple не дав однозначної відповіді",
    "Устройство уже активировано — по USB статус не узнать. "
    "Проверьте на iPhone: Настройки → [имя] → Локатор. "
    "Перед продажей/сбросом его нужно выключить":
        "Пристрій уже активований — через USB статус не дізнатися. "
        "Перевірте на iPhone: Налаштування → [ім'я] → Локатор. Перед продажем/скиданням його потрібно вимкнути",
    "Под контролем этого компьютера (iActivator)": "Під контролем цього комп'ютера (iActivator)",
    "Не управляется (только пропуск экранов настройки)": "Не керується (лише пропуск екранів налаштування)",
    "Не управляется": "Не керується",
    "Запрещена установка/удаление приложений": "Заборонено встановлення/видалення додатків",
    "Устройство не сообщило ёмкость": "Пристрій не повідомив ємність",
    "Адрес отсутствует — модуль не определяется": "Адреса відсутня — модуль не визначається",
    "Нет версии прошивки модема — модем не запустился": "Немає версії прошивки модема — модем не запустився",
    "IMEI не читается": "IMEI не читається",
    # detail templates
    "Не удалось проверить (нужен интернет): {e}": "Не вдалося перевірити (потрібен інтернет): {e}",
    "Не удалось прочитать: {e}": "Не вдалося прочитати: {e}",
    "Устройство в корпоративной программе (Apple Business Manager): {org}. "
    "Удалить может только владелец организации":
        "Пристрій у корпоративній програмі (Apple Business Manager): {org}. "
        "Видалити може лише власник організації",
    "организация неизвестна": "організація невідома", "неизвестная организация": "невідома організація",
    "Контролируемый режим: {org} (снимается стиранием)": "Контрольований режим: {org} (знімається стиранням)",
    "Неудаляемые профили: {list}": "Профілі, що не видаляються: {list}",
    "Установлены профили: {list}": "Встановлено профілі: {list}",
    "Нет доступа к диагностике (разблокируйте iPhone): {e}":
        "Немає доступу до діагностики (розблокуйте iPhone): {e}",
    "{h}% ({full} из {design} мАч) — {note}": "{h}% ({full} з {design} мА·год) — {note}",
    "в норме": "в нормі", "износ заметен": "знос помітний", "рекомендуется замена": "рекомендується заміна",
    "{t} °C": "{t} °C",
    "Кабель подключён, но заряд ({level}%) не идёт — проверьте кабель, порт или контроллер зарядки":
        "Кабель підключено, але заряд ({level}%) не йде — перевірте кабель, порт або контролер заряджання",
    "прошивка {v}": "прошивка {v}",
    "свободно {free} из {total} ГБ ({pct}%)": "вільно {free} з {total} ГБ ({pct}%)",
    "Не удалось прочитать журналы: {e}": "Не вдалося прочитати журнали: {e}",
    # panic / crash
    "Сбоев за {days} дней нет": "Збоїв за {days} днів немає",
    "Прочее: {line}": "Інше: {line}", "Неизвестная причина": "Невідома причина",
    "{n} сбоев за {days} дней (последний {when}). {list}":
        "{n} збоїв за {days} днів (останній {when}). {list}",
    "Не найден датчик — чаще всего шлейф зарядки, микрофон или датчик на шлейфе кнопок":
        "Не знайдено датчик — найчастіше шлейф заряджання, мікрофон або датчик на шлейфі кнопок",
    "Датчик температуры не отвечает — шлейф зарядки/кнопок, батарея или плата":
        "Датчик температури не відповідає — шлейф заряджання/кнопок, батарея або плата",
    "Контроллер питания (SMC) — батарея, шлейф зарядки или плата":
        "Контролер живлення (SMC) — батарея, шлейф заряджання або плата",
    "Сопроцессор датчиков (AOP) — датчики, шлейфы или плата":
        "Співпроцесор датчиків (AOP) — датчики, шлейфи або плата",
    "Ошибка шины I2C — шлейф или компонент на плате": "Помилка шини I2C — шлейф або компонент на платі",
    "Модем — проблема со связью / платой модема": "Модем — проблема зі зв'язком / платою модема",
    "Память (NAND) — неисправность накопителя": "Пам'ять (NAND) — несправність накопичувача",
    "Контроллер памяти (ANS) — неисправность накопителя": "Контролер пам'яті (ANS) — несправність накопичувача",
    "Графический процессор": "Графічний процесор",
    "Устройство зависло и перезагрузилось (watchdog) — ПО или плата":
        "Пристрій завис і перезавантажився (watchdog) — ПЗ або плата",
    # activation / run log
    "Подключение к устройству… (если появится «Доверять этому компьютеру?» — нажмите «Доверять»)":
        "Підключення до пристрою… (якщо з'явиться «Довіряти цьому комп'ютеру?» — натисніть «Довіряти»)",
    "Устройство: {pt} iOS {pv}, состояние: {st}": "Пристрій: {pt} iOS {pv}, стан: {st}",
    "ℹ «Пропустить все экраны настройки» выключено — экраны на iPhone нужно пройти вручную.":
        "ℹ «Пропустити всі екрани налаштування» вимкнено — екрани на iPhone потрібно пройти вручну.",
    "📱 Проведите вверх по экрану iPhone — он перейдёт на главный экран без настроек. "
    "Wi-Fi установлю сразу после этого.":
        "📱 Проведіть угору по екрану iPhone — він перейде на головний екран без налаштувань. "
        "Wi-Fi встановлю одразу після цього.",
    "⚠ iPhone не завершил настройку за 10 минут. Wi-Fi не установлен — "
    "нажмите «Только Wi-Fi», когда iPhone будет на главном экране.":
        "⚠ iPhone не завершив налаштування за 10 хвилин. Wi-Fi не встановлено — "
        "натисніть «Лише Wi-Fi», коли iPhone буде на головному екрані.",
    "не установлен — нажмите «Только Wi-Fi» на главном экране":
        "не встановлено — натисніть «Лише Wi-Fi» на головному екрані",
    "✅ Готово. Если iPhone ещё на экране «Привет» — проведите вверх.":
        "✅ Готово. Якщо iPhone ще на екрані «Привіт» — проведіть угору.",
    "iPhone завершил настройку.": "iPhone завершив налаштування.",
    "Активация не требуется (состояние: {state}).": "Активація не потрібна (стан: {state}).",
    "Активация через серверы Apple (интернет компьютера)…":
        "Активація через сервери Apple (інтернет комп'ютера)…",
    "На устройстве включена Блокировка активации (Найти iPhone). "
    "Введите Apple ID владельца на самом iPhone или снимите устройство с аккаунта "
    "на icloud.com/find. Программа не обходит эту блокировку.":
        "На пристрої ввімкнено Блокування активації (Знайти iPhone). "
        "Введіть Apple ID власника на самому iPhone або зніміть пристрій з акаунта "
        "на icloud.com/find. Програма не обходить це блокування.",
    "Устройство активировано.": "Пристрій активовано.",
    "Язык: {language}, регион/локаль: {locale}, часовой пояс: {timezone}":
        "Мова: {language}, регіон/локаль: {locale}, часовий пояс: {timezone}",
    "часовой пояс": "часовий пояс", "24-часовой формат": "24-годинний формат",
    "  ⚠ не удалось установить {what}: {e}": "  ⚠ не вдалося встановити {what}: {e}",
    "Конфигурация уже применена этим компьютером — пропускаю.":
        "Конфігурацію вже застосовано цим комп'ютером — пропускаю.",
    "Пропуск экранов уже настроен — пропускаю.": "Пропуск екранів уже налаштовано — пропускаю.",
    "Применяю конфигурацию: пропуск экранов настройки": "Застосовую конфігурацію: пропуск екранів налаштування",
    " + контролируемый режим…": " + контрольований режим…",
    "iPhone уже получил свою конфигурацию настройки (он выходил в интернет во время "
    "настройки, или его настраивали 3uTools / Apple Configurator), и iOS не даёт её заменить. "
    "Нажмите «Стереть…», затем «Запустить» — после стирания экраны будут пропущены.":
        "iPhone уже отримав свою конфігурацію налаштування (він виходив в інтернет під час "
        "налаштування, або його налаштовували 3uTools / Apple Configurator), і iOS не дає її замінити. "
        "Натисніть «Стерти…», потім «Запустити» — після стирання екрани буде пропущено.",
    "Экраны настройки будут пропущены.": "Екрани налаштування буде пропущено.",
    "Wi-Fi: «{ssid}», защита {security}, {hidden}{mac}":
        "Wi-Fi: «{ssid}», захист {security}, {hidden}{mac}",
    "скрытая, ": "прихована, ",
    "без случайного MAC": "без випадкового MAC", "частный MAC": "приватний MAC",
    "  📱 На iPhone: Настройки → «Профиль загружен» (вверху) → Установить. "
    "Чтобы Wi-Fi ставился без нажатий, включите «Контролируемый режим» "
    "(на сброшенном iPhone).":
        "  📱 На iPhone: Налаштування → «Профіль завантажено» (вгорі) → Встановити. "
        "Щоб Wi-Fi встановлювався без натискань, увімкніть «Контрольований режим» (на скинутому iPhone).",
    "  Профиль Wi-Fi установлен и подтверждён устройством.":
        "  Профіль Wi-Fi встановлено й підтверджено пристроєм.",
    "устройство не показало профиль после установки":
        "пристрій не показав профіль після встановлення",
    "  попытка {attempt} не удалась: {e}; повтор…": "  спроба {attempt} не вдалася: {e}; повтор…",
    "Не удалось установить профиль Wi-Fi: {e}": "Не вдалося встановити профіль Wi-Fi: {e}",
    "Устройство не контролируется этим компьютером — профиль потребует подтверждения на iPhone.":
        "Пристрій не контролюється цим комп'ютером — профіль потребуватиме підтвердження на iPhone.",
    "Стираю устройство (все данные будут удалены)…": "Стираю пристрій (усі дані буде видалено)…",
    "Команда стирания отправлена. Дождитесь перезагрузки iPhone.":
        "Команду стирання надіслано. Дочекайтеся перезавантаження iPhone.",
    # validation
    "Не указано имя Wi-Fi сети (SSID).": "Не вказано ім'я Wi-Fi мережі (SSID).",
    "В имени сети есть пробелы в начале/конце — уберите их, иначе iPhone не найдёт сеть.":
        "В імені мережі є пробіли на початку/в кінці — приберіть їх, інакше iPhone не знайде мережу.",
    "Пароль WPA/WPA2/WPA3 должен быть от 8 до 63 символов.":
        "Пароль WPA/WPA2/WPA3 має бути від 8 до 63 символів.",
    # webui status / journal
    "❌ Ошибка: ": "❌ Помилка: ",
    "✅ {action}: готово за {secs} с": "✅ {action}: готово за {secs} с",
    "неисправностей {bad}, замечаний {warn}": "несправностей {bad}, зауважень {warn}",
    "без замечаний": "без зауважень", "Без замечаний": "Без зауважень",
    "Не удалось получить список устройств: {e}": "Не вдалося отримати список пристроїв: {e}",
    "Введите имя сети": "Введіть ім'я мережі",
    "Сеть «{ssid}» сохранена (защита {security}{hidden})": "Мережу «{ssid}» збережено (захист {security}{hidden})",
    ", скрытая": ", прихована",
    "Сеть «{ssid}» удалена": "Мережу «{ssid}» видалено",
    "Автозапуск с Windows: {state}": "Автозапуск із Windows: {state}",
    "включён": "увімкнено", "выключен": "вимкнено",
    "Тема оформления: {theme}": "Тема оформлення: {theme}",
    "❌ Импорт настроек: {e}": "❌ Імпорт налаштувань: {e}",
    "Не удалось загрузить настройки: {e}": "Не вдалося завантажити налаштування: {e}",
    "✅ Настройки загружены из «{name}»": "✅ Налаштування завантажено з «{name}»",
    "файла": "файлу",
    "Не выбрано устройство": "Не вибрано пристрій",
    "Язык, регион и режимы": "Мова, регіон і режими",
    # action labels
    "Настройка": "Налаштування", "Стирание": "Стирання", "Чтение данных": "Читання даних",
    "Локатор и MDM": "Локатор і MDM", "Диагностика": "Діагностика",
    "PDF-отчёт": "PDF-звіт", "Языки устройства": "Мови пристрою", "Проверка данных": "Перевірка даних",
    "▶ {action}": "▶ {action}", "▶ {action}: {detail}": "▶ {action}: {detail}",
    "✅ Настройки сохранены в файл: {path}": "✅ Налаштування збережено у файл: {path}",
    ", история: устройств {n}": ", історія: пристроїв {n}",
    "⚠ Не удалось сохранить сеть: {e}": "⚠ Не вдалося зберегти мережу: {e}",
    # theme names
    "Как в системе": "Як у системі", "Светлая": "Світла", "Тёмная": "Темна",
    # PDF report
    "Норма": "Норма", "Внимание": "Увага", "Неисправность": "Несправність", "Инфо": "Інфо",
    "Готово": "Готово", "С замечанием": "Із зауваженням", "Ошибка": "Помилка", "Пропущено": "Пропущено",
    "Отчёт о проверке iPhone": "Звіт про перевірку iPhone",
    "Дата и время проверки": "Дата й час перевірки",
    "Найдены неисправности: {n}": "Знайдено несправності: {n}", "Есть замечания: {n}": "Є зауваження: {n}",
    "Неисправностей не найдено": "Несправностей не знайдено",
    "Серийный номер": "Серійний номер", "IMEI 2": "IMEI 2",
    "Модель": "Модель",
    "Ёмкость (здоровье)": "Ємність (здоров'я)",
    "Текущая / заводская": "Поточна / заводська", "Заряд сейчас": "Заряд зараз",
    "Ход активации (последний запуск)": "Хід активації (останній запуск)", "Проверка": "Перевірка",
    "Создано в iActivator {ver} · {stamp}": "Створено в iActivator {ver} · {stamp}",
    "стр. {n}": "с. {n}",
    "мАч": "мА·год",
    # verdict
    "Годен": "Придатний", "Не годен": "Непридатний", "Годен с замечаниями": "Придатний із зауваженнями",
    # self-update
    "Автообновление доступно только в установленной программе.": "Автооновлення доступне лише у встановленій програмі.",
    "Нет доступного обновления.": "Немає доступного оновлення.",
    "Загружаю обновление…": "Завантажую оновлення…",
    "Устанавливаю обновление и перезапускаю…": "Встановлюю оновлення та перезапускаю…",
    "Не удалось найти установленную программу для замены.": "Не вдалося знайти встановлену програму для заміни.",
    # ---- legacy activation (iOS < 10) ----
    "Старая iOS ({pv}): активация через lockdown (без сессии).":
        "Стара iOS ({pv}): активація через lockdown (без сесії).",
    "iPhone не выдал данные для активации: {e}. Разблокируйте экран, проверьте кабель и что в телефон вставлена SIM-карта, затем повторите.":
        "iPhone не видав дані для активації: {e}. Розблокуйте екран, перевірте кабель і що в телефон вставлена SIM-картка, потім повторіть.",
    "  ⚠ SIM-карта не обнаружена. Старые iPhone обычно не активируются без SIM.":
        "  ⚠ SIM-картку не виявлено. Старі iPhone зазвичай не активуються без SIM.",
    "Сервер Apple не выдал запись активации для этого устройства.":
        "Сервер Apple не видав запис активації для цього пристрою.",
    "Вставьте рабочую SIM-карту и повторите.":
        "Вставте робочу SIM-картку і повторіть.",
    "⚠ Старая iOS не приняла пропуск экранов ({e}) — пройдите их на iPhone вручную.":
        "⚠ Стара iOS не прийняла пропуск екранів ({e}) — пройдіть їх на iPhone вручну.",
    "не поддерживается этой версией iOS":
        "не підтримується цією версією iOS",
    # ---- journal, diagnostics, history: strings that were left untranslated ----
    "Прочее: ": "Інше: ",
    "{n} сбоев за {days} дней (последний {last}). ": "{n} збоїв за {days} днів (останній {last}). ",
    "Неудаляемые профили: ": "Невидалювані профілі: ",
    "Установлены профили: ": "Встановлені профілі: ",
    "прошивка {fw}": "прошивка {fw}",
    "Замечания": "Зауваження",
    "Успешно": "Успішно",
    "Дата и время": "Дата і час",
    "Действие": "Дія",
    "Подробности": "Подробиці",
    "Результат": "Результат",
    "Серийный №": "Серійний №",
    "iPhone SE (1-го поколения)": "iPhone SE (1-го покоління)",
    "iPhone SE (2-го поколения)": "iPhone SE (2-го покоління)",
    "iPhone SE (3-го поколения)": "iPhone SE (3-го покоління)",
    "{n} ГБ": "{n} ГБ",
    "{n} ТБ": "{n} ТБ",
    "Отчёты": "Звіти",
    "Это не файл настроек iActivator": "Це не файл налаштувань iActivator",
    " (без паролей)": " (без паролів)",
    " (с паролями: {n})": " (з паролями: {n})",
    "Сети Wi-Fi: {n}": "Мережі Wi-Fi: {n}",
    "Тема оформления": "Тема оформлення",
    "Ключ контролируемого режима": "Ключ контрольованого режиму",
    "⚠ Ключ контролируемого режима не заменён: на этом компьютере уже есть свой": "⚠ Ключ контрольованого режиму не замінено: на цьому комп'ютері вже є свій",
    "История: устройств {n}": "Історія: пристроїв {n}",
    "Показать окно": "Показати вікно",
    "Выход": "Вихід",
    "Проверка обновлений не удалась: {kind}: {e}": "Перевірка оновлень не вдалася: {kind}: {e}",
    "Диагностика: проверяю…": "Діагностика: перевіряю…",
    "📄 Отчёт сохранён: {path}": "📄 Звіт збережено: {path}",
    ", батарея {h}%": ", батарея {h}%",
    "Подключение": "Підключення",
    "Подключён {model}": "Підключено {model}",
    "Уже выполняется другая операция": "Уже виконується інша операція",
    "как в системе": "як у системі",
    "светлая": "світла",
    "тёмная": "темна",
    "iActivator-настройки-{date}.json": "iActivator-налаштування-{date}.json",
    "❌ Не удалось сохранить настройки: {e}": "❌ Не вдалося зберегти налаштування: {e}",
    "Не удалось сохранить файл: {e}": "Не вдалося зберегти файл: {e}",
    "  Сети Wi-Fi: {n}": "  Мережі Wi-Fi: {n}",
    ", без паролей": ", без паролів",
    ", с паролями": ", з паролями",
    ", ключ контролируемого режима": ", ключ контрольованого режиму",
    "-без-номеров": "-без-номерів",
    "iActivator-журнал{suffix}-{date}.txt": "iActivator-журнал{suffix}-{date}.txt",
    "=== iActivator — журнал для диагностики ===": "=== iActivator — журнал для діагностики ===",
    "Создан: {when}": "Створено: {when}",
    "Версия: {v}   Система: {sys}   Python: {py}   pymobiledevice3: {pmd}": "Версія: {v}   Система: {sys}   Python: {py}   pymobiledevice3: {pmd}",
    "Серийные номера, IMEI и UDID скрыты (***); история устройств не включена.": "Серійні номери, IMEI та UDID приховано (***); історію пристроїв не включено.",
    "=== ЗАПИСИ ЖУРНАЛА (файлов: {n}) ===": "=== ЗАПИСИ ЖУРНАЛУ (файлів: {n}) ===",
    "(не удалось прочитать: {e})": "(не вдалося прочитати: {e})",
    "=== ЗАПИСЕЙ ЖУРНАЛА ПОКА НЕТ ===": "=== ЗАПИСІВ ЖУРНАЛУ ПОКИ НЕМАЄ ===",
    "=== ИСТОРИЯ УСТРОЙСТВ (JSON) ===": "=== ІСТОРІЯ ПРИСТРОЇВ (JSON) ===",
    "❌ Не удалось сохранить журнал: {e}": "❌ Не вдалося зберегти журнал: {e}",
    "✅ Журнал сохранён в файл: {path}": "✅ Журнал збережено у файл: {path}",
    "iActivator {v} запущен · {sys} · Python {py}": "iActivator {v} запущено · {sys} · Python {py}",
    # ---- self-update: verification and backup ----
    "❌ Обновление не установлено: {e}. Программа осталась прежней.": "❌ Оновлення не встановлено: {e}. Програма залишилася попередньою.",
    "Загрузка оборвалась ({got} из {total} байт). Повторите позже.": "Завантаження обірвалося ({got} з {total} байт). Повторіть пізніше.",
    "Скачанный файл слишком мал и не похож на программу.": "Завантажений файл замалий і не схожий на програму.",
    "Скачанный файл повреждён (контрольная сумма не совпала).": "Завантажений файл пошкоджено (контрольна сума не збіглася).",
    "Скачанный файл не является программой Windows.": "Завантажений файл не є програмою Windows.",
    "Скачанный архив повреждён.": "Завантажений архів пошкоджено.",
    "Предыдущая версия будет сохранена в: {path}": "Попередню версію буде збережено в: {path}",
    "Предыдущая версия сохранена в: {path}": "Попередню версію збережено в: {path}",
    "⚠ Не удалось сохранить предыдущую версию: {e}": "⚠ Не вдалося зберегти попередню версію: {e}",
    "Обновление распаковалось неправильно — программа не тронута.": "Оновлення розпакувалося неправильно — програму не змінено.",
    # ---- Apple driver (Windows) ----
    "На этой системе отдельный драйвер не нужен.": "На цій системі окремий драйвер не потрібен.",
    "Драйвер Apple не установлен. Установите приложение «Apple Devices» из Microsoft Store (или iTunes), затем перезапустите iActivator.": "Драйвер Apple не встановлено. Встановіть застосунок «Apple Devices» з Microsoft Store (або iTunes), потім перезапустіть iActivator.",
    "Apple Devices из Microsoft Store": "Apple Devices з Microsoft Store",
    "Служба Apple ({source}) не отвечает. Перезапустите её — Windows попросит разрешение администратора.": "Служба Apple ({source}) не відповідає. Перезапустіть її — Windows попросить дозвіл адміністратора.",
    "Windows видит iPhone, но драйвер работает с ошибкой ({name}: {status}). Переустановите драйвер iPhone.": "Windows бачить iPhone, але драйвер працює з помилкою ({name}: {status}). Перевстановіть драйвер iPhone.",
    "Windows видит iPhone, но служба Apple — нет: у телефона не тот драйвер. Переустановите драйвер iPhone.": "Windows бачить iPhone, а служба Apple — ні: у телефона не той драйвер. Перевстановіть драйвер iPhone.",
    "Драйвер Apple работает ({source}), iPhone виден.": "Драйвер Apple працює ({source}), iPhone видно.",
    "Драйвер Apple работает ({source}). Подключите iPhone кабелем и разблокируйте его.": "Драйвер Apple працює ({source}). Підключіть iPhone кабелем і розблокуйте його.",
    "Windows не завершил операцию вовремя. Перезагрузите компьютер и повторите.": "Windows не завершив операцію вчасно. Перезавантажте комп'ютер і повторіть.",
    "Нужно разрешение администратора — операция отменена.": "Потрібен дозвіл адміністратора — операцію скасовано.",
    "Не удалось выполнить операцию.": "Не вдалося виконати операцію.",
    "Доступно только на Windows.": "Доступно лише на Windows.",
    "Драйвер Apple: {action}…": "Драйвер Apple: {action}…",
    "✅ Драйвер Apple: {action} — готово": "✅ Драйвер Apple: {action} — готово",
    "❌ Драйвер Apple: {e}": "❌ Драйвер Apple: {e}",
    "Драйвер Apple: {message}": "Драйвер Apple: {message}",
    "установка Apple Devices": "встановлення Apple Devices",
    "перезапуск службы": "перезапуск служби",
    "переустановка драйвера iPhone": "перевстановлення драйвера iPhone",
    # ---- SIM and carrier lock ----
    "SIM-карта": "SIM-картка",
    "Привязка к оператору": "Прив'язка до оператора",
    "Не вставлена": "Не вставлена",
    "Вставьте SIM-карту, чтобы проверить привязку к оператору": "Вставте SIM-картку, щоб перевірити прив'язку до оператора",
    "iPhone не принимает эту SIM ({carrier})": "iPhone не приймає цю SIM ({carrier})",
    "Похоже, iPhone привязан к другому оператору (SIM-lock). Проверьте по IMEI у оператора или продавца": "Схоже, iPhone прив'язаний до іншого оператора (SIM-lock). Перевірте за IMEI в оператора або продавця",
    "Работает · {carrier} · ICCID {tail}": "Працює · {carrier} · ICCID {tail}",
    "С этой SIM телефон работает. Полностью проверить привязку по USB нельзя: вставьте SIM другого оператора — если iPhone привязан, здесь будет предупреждение": "З цією SIM телефон працює. Повністю перевірити прив'язку через USB не можна: вставте SIM іншого оператора — якщо iPhone прив'язаний, тут буде попередження",
    "Заблокирована PIN-кодом — введите PIN на iPhone": "Заблокована PIN-кодом — введіть PIN на iPhone",
    "Заблокирована PUK-кодом — нужен PUK от оператора": "Заблокована PUK-кодом — потрібен PUK від оператора",
    "Ещё не готова — подождите немного и проверьте снова": "Ще не готова — зачекайте трохи й перевірте знову",
    "Ошибка SIM-карты — проверьте SIM или лоток": "Помилка SIM-картки — перевірте SIM або лоток",
    "SIM-карта заблокирована оператором": "SIM-картку заблоковано оператором",
    "Включён режим разрешённых номеров (FDN)": "Увімкнено режим дозволених номерів (FDN)",
    "Состояние: {state}": "Стан: {state}",
    # ---- replaced parts ----
    "Системная плата": "Системна плата",
    "Дисплей": "Дисплей",
    "Основная камера": "Основна камера",
    "Сверхширокоугольная камера": "Надширококутна камера",
    "Телекамера": "Телекамера",
    "Фронтальная камера": "Фронтальна камера",
    "Face ID": "Face ID",
    "Touch ID": "Touch ID",
    "Детали": "Деталі",
    "Эта версия iOS не сообщает серийные номера деталей по USB": "Ця версія iOS не повідомляє серійні номери деталей через USB",
    "Записаны серийные номера: {parts}. При следующих проверках программа сообщит, если какую-то из этих деталей заменят": "Записано серійні номери: {parts}. Під час наступних перевірок програма повідомить, якщо якусь із цих деталей замінять",
    "Заменено после проверки {date}: {parts}": "Замінено після перевірки {date}: {parts}",
    "Нечего сравнить с прошлой проверкой — записаны: {parts}": "Немає з чим порівняти попередню перевірку — записано: {parts}",
    "Не менялись с проверки {date} ({parts})": "Не змінювалися з перевірки {date} ({parts})",
    # ---- several iPhones ----
    "Очередь: {label} отключён — пропускаю": "Черга: {label} відключено — пропускаю",
    "Авто-режим: {label} — в очереди ({n})": "Авто-режим: {label} — у черзі ({n})",
    "Авто-режим: {label} уже активирован — пропускаю": "Авто-режим: {label} уже активовано — пропускаю",
    "⛔ Авто-режим остановлен: {reason}": "⛔ Авто-режим зупинено: {reason}",
    "Нет ответа от iPhone или службы Apple за {n} с": "Немає відповіді від iPhone або служби Apple за {n} с",
    # ---- colour themes ----
    "синяя ночь": "синя ніч",
    "мятная": "м'ятна",
    "графит": "графіт",
    "Обновление установится и программа откроется снова через несколько секунд.": "Оновлення встановиться, і програма відкриється знову за кілька секунд.",
    "Автозапуск: путь к программе обновлён": "Автозапуск: шлях до програми оновлено",
    "Имя": "Ім'я",
    "Событий нет": "Подій немає",
    "Впервые подключён": "Вперше підключено",
    "Последний раз": "Востаннє",
    "Серийные номера деталей (записаны {time})": "Серійні номери деталей (записано {time})",
    "События ({n})": "Події ({n})",
    "Создано в iActivator {time}": "Створено в iActivator {time}",
    "Этого устройства нет в истории.": "Цього пристрою немає в історії.",
    "TXT-файлы сохранены: {n}": "TXT-файли збережено: {n}",
    "Удалено файлов: {n}, освобождено {size}": "Видалено файлів: {n}, звільнено {size}",
    "{n} КБ": "{n} КБ",
    "{n} МБ": "{n} МБ",
    "Батарея (здоровье)": "Батарея (здоров'я)",
    "История очищена: устройств {d}, файлов {n}, освобождено {size}": "Історію очищено: пристроїв {d}, файлів {n}, звільнено {size}",
    "Нет связи с сервером Apple — проверьте интернет на компьютере: {e}": "Немає зв'язку з сервером Apple — перевірте інтернет на комп'ютері: {e}",
    "iPhone не дал проверить ({e}). Проверьте после активации: Настройки → [имя] → Локатор": "iPhone не дав перевірити ({e}). Перевірте після активації: Параметри → [ім'я] → Локатор",
    "До активации этот iPhone не даёт прочитать — проверьте после активации": "До активації цей iPhone не дає прочитати — перевірте після активації",
    "новая батарея: ёмкость выше заводской, это нормально": "нова батарея: ємність вища за заводську, це нормально",
    "новая батарея": "нова батарея",
    "Заметка": "Нотатка",
    "{action}: готово": "{action}: готово",
    "{action}: ошибка": "{action}: помилка",
    "Автоочистка (старше {days} дн.): устройств {d}, файлов {n}, освобождено {size}": "Автоочищення (старше {days} дн.): пристроїв {d}, файлів {n}, звільнено {size}",
    "Наклейка": "Наліпка",
    "Наклейки": "Наліпки",
    "Не удалось сделать наклейку: {e}": "Не вдалося зробити наліпку: {e}",
    "🏷 Наклейки сохранены: {n} · {name}": "🏷 Наліпки збережено: {n} · {name}",
    "Не найден шрифт с кириллицей для PDF": "Не знайдено шрифт із кирилицею для PDF",
    "Вход прерван. Начните заново.": "Вхід перервано. Почніть заново.",
    "Apple просит подтверждение, но не прислала полей для ввода. Повторите вход владельца на самом iPhone.": "Apple просить підтвердження, але не надіслала полів для введення. Повторіть вхід власника на самому iPhone.",
    "Apple вернула неожиданный ответ. Повторите позже.": "Apple повернула неочікувану відповідь. Повторіть пізніше.",
    "Дождитесь окончания текущей операции.": "Дочекайтеся завершення поточної операції.",
    "Вход владельца Apple ID для снятия блокировки активации…": "Вхід власника Apple ID для зняття блокування активації…",
    "Вход владельца Apple ID": "Вхід власника Apple ID",
    "✅ Блокировка активации снята входом владельца.": "✅ Блокування активації знято входом власника.",
    "Вход Apple ID": "Вхід Apple ID",
    "Не удалось открыть браузер. Ссылка: {url}": "Не вдалося відкрити браузер. Посилання: {url}",
    "Устройство привязано к Apple ID. Снимается входом владельца: пароль Apple ID (кнопка ниже), или на самом iPhone «Разблокировать с помощью код-пароля?» и старый код-пароль устройства (iOS 15.2+), или отвязка на icloud.com/find": "Пристрій прив'язаний до Apple ID. Знімається входом власника: пароль Apple ID (кнопка нижче), або на самому iPhone «Розблокувати за допомогою коду-пароля?» і старий код-пароль пристрою (iOS 15.2+), або відв'язка на icloud.com/find",
    "На этой iOS статус Локатора до активации по USB не читается. Проверьте после активации на iPhone: Настройки → [имя] → Локатор": "На цій iOS статус Локатора до активації по USB не читається. Перевірте після активації на iPhone: Параметри → [ім'я] → Локатор",
    "Введите название профиля.": "Введіть назву профілю.",
    "Профиль сохранён: {name}": "Профіль збережено: {name}",
    "Создано в iActivator": "Створено в iActivator",
    "Акт приёма устройства": "Акт приймання пристрою",
    "Акт выдачи устройства": "Акт видачі пристрою",
    "Гарантийный талон": "Гарантійний талон",
    "Документ": "Документ",
    "Дата": "Дата",
    "Клиент": "Клієнт",
    "Состояние / дефекты": "Стан / дефекти",
    "Выполненные работы": "Виконані роботи",
    "Стоимость": "Вартість",
    "Гарантия": "Гарантія",
    "{n} мес. (до {date})": "{n} міс. (до {date})",
    "Гарантия не распространяется на механические повреждения, попадание жидкости и следы самостоятельного ремонта. Сохраняйте этот талон.": "Гарантія не поширюється на механічні пошкодження, потрапляння рідини та сліди самостійного ремонту. Зберігайте цей талон.",
    "Сдал (клиент)": "Здав (клієнт)",
    "Получил (клиент)": "Отримав (клієнт)",
    "Принял (сервис)": "Прийняв (сервіс)",
    "Выдал (сервис)": "Видав (сервіс)",
    "Сервис": "Сервіс",
    "Не удалось создать документ: {e}": "Не вдалося створити документ: {e}",
    "📄 Документ сохранён: {name}": "📄 Документ збережено: {name}",
}


# Polish. Only the strings translated here override English; anything missing falls back to
# English (see t()). Add entries over time to make the Polish UI complete.
PL: dict[str, str] = {
    "Активация": "Aktywacja",
    "Диагностика": "Diagnostyka",
    "История": "Historia",
    "Журнал": "Dziennik",
    "Статистика": "Statystyka",
    "Настройки": "Ustawienia",
    "О программе": "O programie",
    "Нет устройства": "Brak urządzenia",
    "Состояние подключения": "Stan połączenia",
    "Подключите iPhone кабелем.": "Podłącz iPhone kablem.",
    "Подключите iPhone кабелем…": "Podłącz iPhone kablem…",
    "Готово": "Gotowe",
    "Запустить": "Uruchom",
    "Обновить": "Odśwież",
    "Проверить": "Sprawdź",
    "PDF-отчёт": "Raport PDF",
    "Отмена": "Anuluj",
    "Продолжить": "Kontynuuj",
    "Сохранить": "Zapisz",
    "Открыть файл": "Otwórz plik",
    "Отчёты": "Raporty",
    "Открыть журнал": "Otwórz dziennik",
    "Выгрузить в файл": "Zapisz do pliku",
    "Язык и регион": "Język i region",
    "Язык": "Język",
    "Регион": "Region",
    "Часовой пояс": "Strefa czasowa",
    "Режим": "Tryb",
    "Активировать": "Aktywuj",
    "Пропустить экраны настройки": "Pomiń ekrany konfiguracji",
    "Все": "Wszystkie",
    "24 ч": "24 h",
    "Оформление": "Wygląd",
    "Тема": "Motyw",
    "Язык программы": "Język programu",
    "Как в системе": "Jak w systemie",
    "Светлая": "Jasny",
    "Тёмная": "Ciemny",
    "Запуск": "Uruchamianie",
    "Перенос настроек": "Przenoszenie ustawień",
    "Открыть страницу загрузки": "Otwórz stronę pobierania",
    "Активации": "Aktywacje",
    "Проверки": "Sprawdzenia",
    "Сегодня": "Dziś",
    "7 дней": "7 dni",
    "30 дней": "30 dni",
    "Всего": "Razem",
    "Всего устройств": "Urządzeń łącznie",
    "Активировано": "Aktywowano",
    "С замечаниями": "Z uwagami",
    "Пока нет данных": "Brak danych",
    "Модель": "Model",
    "Серийный №": "Nr seryjny",
    "Последнее действие": "Ostatnia akcja",
    "Удалить из истории": "Usuń z historii",
    "Заметка": "Notatka",
    "Событий нет": "Brak zdarzeń",
    "Сохранить TXT": "Zapisz TXT",
    "Все в TXT": "Wszystkie do TXT",
    "Очистить всё": "Wyczyść wszystko",
    "Наклейка": "Naklejka",
    "Наклейки": "Naklejki",
    "Ничего не найдено": "Nic nie znaleziono",
    "Показано": "Pokazano",
    "из": "z",
    "Батарея": "Bateria",
    "Память": "Pamięć",
    "Годен": "Sprawny",
    "Не годен": "Niesprawny",
    "Годен с замечаниями": "Sprawny z uwagami",
    "Доступна новая версия": "Dostępna nowa wersja",
    "Скачать и установить": "Pobierz i zainstaluj",
    "Скачать": "Pobierz",
}

ES: dict[str, str] = {
    "Активация": "Activación",
    "Диагностика": "Diagnóstico",
    "История": "Historial",
    "Журнал": "Registro",
    "Статистика": "Estadísticas",
    "Настройки": "Ajustes",
    "О программе": "Acerca de",
    "Нет устройства": "Sin dispositivo",
    "Состояние подключения": "Estado de conexión",
    "Подключите iPhone кабелем.": "Conecta el iPhone con un cable.",
    "Подключите iPhone кабелем…": "Conecta el iPhone con un cable…",
    "Готово": "Listo",
    "Запустить": "Iniciar",
    "Обновить": "Actualizar",
    "Проверить": "Comprobar",
    "PDF-отчёт": "Informe PDF",
    "Отмена": "Cancelar",
    "Продолжить": "Continuar",
    "Сохранить": "Guardar",
    "Открыть файл": "Abrir archivo",
    "Отчёты": "Informes",
    "Открыть журнал": "Abrir el registro",
    "Выгрузить в файл": "Exportar a archivo",
    "Язык и регион": "Idioma y región",
    "Язык": "Idioma",
    "Регион": "Región",
    "Часовой пояс": "Zona horaria",
    "Режим": "Modo",
    "Активировать": "Activar",
    "Пропустить экраны настройки": "Omitir pantallas de configuración",
    "Все": "Todos",
    "24 ч": "24 h",
    "Оформление": "Apariencia",
    "Тема": "Tema",
    "Язык программы": "Idioma del programa",
    "Как в системе": "Como el sistema",
    "Светлая": "Claro",
    "Тёмная": "Oscuro",
    "Запуск": "Inicio",
    "Перенос настроек": "Transferir ajustes",
    "Открыть страницу загрузки": "Abrir la página de descarga",
    "Активации": "Activaciones",
    "Проверки": "Comprobaciones",
    "Сегодня": "Hoy",
    "7 дней": "7 días",
    "30 дней": "30 días",
    "Всего": "Total",
    "Всего устройств": "Dispositivos en total",
    "Активировано": "Activados",
    "С замечаниями": "Con observaciones",
    "Пока нет данных": "Aún no hay datos",
    "Модель": "Modelo",
    "Серийный №": "N.º de serie",
    "Последнее действие": "Última acción",
    "Удалить из истории": "Eliminar del historial",
    "Заметка": "Nota",
    "Событий нет": "Sin eventos",
    "Сохранить TXT": "Guardar TXT",
    "Все в TXT": "Todos a TXT",
    "Очистить всё": "Borrar todo",
    "Наклейка": "Etiqueta",
    "Наклейки": "Etiquetas",
    "Ничего не найдено": "No se encontró nada",
    "Показано": "Mostrado",
    "из": "de",
    "Батарея": "Batería",
    "Память": "Almacenamiento",
    "Годен": "Apto",
    "Не годен": "No apto",
    "Годен с замечаниями": "Apto con observaciones",
    "Доступна новая версия": "Hay una versión nueva",
    "Скачать и установить": "Descargar e instalar",
    "Скачать": "Descargar",
}

DE: dict[str, str] = {
    "Активация": "Aktivierung",
    "Диагностика": "Diagnose",
    "История": "Verlauf",
    "Журнал": "Protokoll",
    "Статистика": "Statistik",
    "Настройки": "Einstellungen",
    "О программе": "Über das Programm",
    "Нет устройства": "Kein Gerät",
    "Состояние подключения": "Verbindungsstatus",
    "Подключите iPhone кабелем.": "iPhone per Kabel anschließen.",
    "Подключите iPhone кабелем…": "iPhone per Kabel anschließen…",
    "Готово": "Fertig",
    "Запустить": "Starten",
    "Обновить": "Aktualisieren",
    "Проверить": "Prüfen",
    "PDF-отчёт": "PDF-Bericht",
    "Отмена": "Abbrechen",
    "Продолжить": "Weiter",
    "Сохранить": "Speichern",
    "Открыть файл": "Datei öffnen",
    "Отчёты": "Berichte",
    "Открыть журнал": "Protokoll öffnen",
    "Выгрузить в файл": "In Datei exportieren",
    "Язык и регион": "Sprache und Region",
    "Язык": "Sprache",
    "Регион": "Region",
    "Часовой пояс": "Zeitzone",
    "Режим": "Modus",
    "Активировать": "Aktivieren",
    "Пропустить экраны настройки": "Einrichtungsbildschirme überspringen",
    "Все": "Alle",
    "24 ч": "24 h",
    "Оформление": "Darstellung",
    "Тема": "Thema",
    "Язык программы": "Programmsprache",
    "Как в системе": "Wie das System",
    "Светлая": "Hell",
    "Тёмная": "Dunkel",
    "Запуск": "Autostart",
    "Перенос настроек": "Einstellungen übertragen",
    "Открыть страницу загрузки": "Download-Seite öffnen",
    "Активации": "Aktivierungen",
    "Проверки": "Prüfungen",
    "Сегодня": "Heute",
    "7 дней": "7 Tage",
    "30 дней": "30 Tage",
    "Всего": "Gesamt",
    "Всего устройств": "Geräte insgesamt",
    "Активировано": "Aktiviert",
    "С замечаниями": "Mit Anmerkungen",
    "Пока нет данных": "Noch keine Daten",
    "Модель": "Modell",
    "Серийный №": "Seriennr.",
    "Последнее действие": "Letzte Aktion",
    "Удалить из истории": "Aus Verlauf löschen",
    "Заметка": "Notiz",
    "Событий нет": "Keine Ereignisse",
    "Сохранить TXT": "TXT speichern",
    "Все в TXT": "Alle als TXT",
    "Очистить всё": "Alles löschen",
    "Наклейка": "Etikett",
    "Наклейки": "Etiketten",
    "Ничего не найдено": "Nichts gefunden",
    "Показано": "Angezeigt",
    "из": "von",
    "Батарея": "Batterie",
    "Память": "Speicher",
    "Годен": "Bestanden",
    "Не годен": "Nicht bestanden",
    "Годен с замечаниями": "Bestanden mit Anmerkungen",
    "Доступна новая версия": "Neue Version verfügbar",
    "Скачать и установить": "Herunterladen und installieren",
    "Скачать": "Herunterladen",
}

TABLES = {"en": EN, "uk": UK, "pl": PL, "es": ES, "de": DE}
