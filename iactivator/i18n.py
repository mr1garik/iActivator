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


LANGS = ("ru", "en", "uk")


def set_lang(code: str) -> None:
    global _lang
    with _lock:
        _lang = code if code in LANGS else "ru"


def get_lang() -> str:
    return _lang


def t(s: str, **kw) -> str:
    table = {"en": EN, "uk": UK}.get(_lang)
    tpl = table.get(s, s) if table else s
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
}
