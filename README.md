<div align="center">

**🇬🇧 English** · [🇺🇦 Українська](README.uk.md) · [🇷🇺 Русский](README.ru.md)

<img src="assets/social-preview.png" alt="iActivator" width="820">

### One-click iPhone activation & setup · Windows and macOS

[![Download for Windows and macOS](https://img.shields.io/badge/⬇%20Download-Windows%20%7C%20macOS-0297DE?style=for-the-badge)](https://github.com/mr1garik/iActivator/releases/latest)

[![Downloads](https://img.shields.io/github/downloads/mr1garik/iActivator/total?label=downloads&color=0297DE)](https://github.com/mr1garik/iActivator/releases)
[![MIT license](https://img.shields.io/github/license/mr1garik/iActivator?label=license&color=0297DE)](LICENSE)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS-2E3035)
![Interface languages](https://img.shields.io/badge/UI-EN%20%7C%20UK%20%7C%20RU-0297DE)

**⭐ If it saves you time, a star helps the project grow.**

<br>

<img src="assets/demo.gif" alt="iActivator — iPhone activation and setup in one click" width="760">

</div>

Activate and set up an iPhone over USB in one click — activation, language, region, Wi-Fi and skipping the Setup Assistant — with a health check and PDF report. Free, open-source, runs on **Windows and macOS**, with the interface in **English, Ukrainian and Russian** (Settings → App language).

<details>
<summary><b>Contents</b></summary>

- [Features](#features)
- [Screenshots](#screenshots)
- [Supported models, iOS and systems](#support-models-ios-system)
- [What it does](#what-it-does)
- [Why Wi-Fi from 3uTools sometimes fails](#why-wi-fi-from-3utools-sometimes-fails-and-whats-done-here)
- [Diagnostics & PDF report](#diagnostics--pdf-report)
- [Settings and journal](#settings-and-journal)
- [Updates](#updates)
- [Download & build](#download--build)
- [Important](#important)
- [Related projects](#related-projects)
- [License](#license)

</details>

## Features

- 📲 **One-click activation** through Apple's servers over USB — the phone doesn't need Wi-Fi for it
- 🌐 **Language, region, timezone, 24h** — any locale, applied in one pass
- ⏭️ **Skips the Setup Assistant** screens (supervised mode, like Apple Configurator)
- 📶 **Wi-Fi via a profile**, read back from the device to confirm it applied — fixes the usual 3uTools Wi-Fi failures
- 🩺 **Health check + PDF report** — battery, Find My, MDM, 30-day crash logs, with a clear **Pass / Fail** verdict
- 🔄 **Built-in auto-update** — one-click "Download & install", no manual reinstall
- 🌍 **Trilingual interface** — English, Ukrainian, Russian
- 🖥️ **Windows & macOS** — free and open-source

**💬 Feedback:** found a problem or have an idea? Open an [Issue](https://github.com/mr1garik/iActivator/issues) — the app is improved based on your feedback.

## Screenshots

The **Activation** tab — connect the iPhone, pick language/region, choose the mode, and press Run. Each step reports back with a checkmark, so you see exactly what applied.

<p align="center">
  <img src="assets/screenshot-light.png" width="49%" alt="iActivator — Activation tab, light theme">
  <img src="assets/screenshot-dark.png" width="49%" alt="iActivator — Activation tab, dark theme">
</p>
<p align="center"><sub>Activation tab — light and dark themes</sub></p>

<!--
  More screenshots to add (drop the PNGs into assets/ and uncomment):
  - assets/screenshot-diagnostics.png  — Diagnostics tab with the Pass/Fail verdict
  - assets/screenshot-report.png       — a generated PDF report
  - assets/screenshot-settings.png     — Settings (languages, Wi-Fi, transfer)

<p align="center">
  <img src="assets/screenshot-diagnostics.png" width="49%" alt="Diagnostics with Pass/Fail verdict">
  <img src="assets/screenshot-settings.png" width="49%" alt="Settings">
</p>
-->

<h2 id="support-models-ios-system">Supported models, iOS and systems</h2>

| | Support |
|---|---|
| **iPhone models** | iPhone 5s and newer (anything that runs iOS 12+). iPads activate too, but the interface is designed for iPhone. |
| **iOS versions** | iOS 12–18. Screen skipping and the Wi-Fi profile work on iOS 13+; on older versions activation still goes through, but some settings may not apply. |
| **iPhone 4 / 4S (iOS 7–9)** | Experimental: activated through the legacy lockdown path. A SIM card is usually required; skipping setup screens may not be available. Not yet verified on real devices — feedback is welcome. |
| **Windows** | Windows 10 and 11. Needs the Apple driver: "Apple Devices" from the Microsoft Store or iTunes. Has a tray icon and auto-start. |
| **macOS** | macOS 11 Big Sur and newer (Intel and Apple Silicon). No drivers needed. Controls live in the menu bar. |
| **Activation Lock (iCloud)** | Not bypassed. An iPhone tied to someone else's Apple ID must be removed from the owner's account. |

If a model or iOS version behaves differently, open an [Issue](https://github.com/mr1garik/iActivator/issues) and we'll add it to the table.

## What it does
1. Activates the iPhone through Apple's servers. Internet comes from the computer over USB, so the phone doesn't need Wi‑Fi for this.
2. Sets the language, region (locale, e.g. `en_US`), time zone and 24‑hour format.
3. Skips the Setup Assistant screens (supervised mode, like Apple Configurator and 3uTools).
4. Installs a Wi‑Fi profile and verifies that the device accepted it.

The app will not activate an iPhone with Activation Lock (iCloud) enabled: the owner's Apple ID is required.

## Why Wi‑Fi from 3uTools sometimes fails, and what's done here
| Cause | Fix |
|---|---|
| Security type hardcoded as WPA while the router runs WPA3 or WPA2/WPA3 | Defaults to `Any`: iOS picks the protocol itself |
| "Private Wi‑Fi address" (random MAC) fails a MAC filter or DHCP reservation | An option disables the random MAC for that network |
| After skipping setup, the Wi‑Fi radio stays off | The radio is forced on before installing the profile |
| The profile is installed without supervisor rights, with no one to confirm it during setup | The profile is installed silently, after escalating with a supervisor certificate |
| Spaces in the SSID, a too-short password | Checked before sending to the device |
| The profile didn't install, and the app didn't say so | After installation the profile list is read back from the device; up to 3 attempts |

## Diagnostics & PDF report
- **Health check** reads battery, Find My, MDM and the last 30 days of crash logs, and shows a clear **Pass / Fail** verdict — handy before buying or reselling a device.
- **PDF report** per device: the health check plus an "Activation run (last run)" section with the result of each step — so you can see exactly what failed (e.g. activation went through but the phone rejected the Wi-Fi profile) without repeating the whole procedure.

## Settings and journal
- **App language:** English, Ukrainian or Russian (Settings → App language). On first run the app follows your system language.
- **Theme:** System, Light or Dark (Settings).
- **Transfer settings:** Settings → "Save to file…" writes Wi‑Fi networks, language, region, modes and theme into a single `.json`. Optionally it also includes Wi‑Fi passwords, the supervision key and device history. On another computer: "Load from file…". Passwords in the file are not encrypted.
- **Journal:** every entry has a time, device and level. Filters: main, errors only, detailed (with technical error info). Daily logs are saved to the `logs` folder in the data directory and kept for 30 days. "Export to file" collects the whole journal and device history into one text file (for your own archive). "For sharing (no numbers)" does the same but hides serial numbers, IMEI and UDID and leaves out the history — that file is safe to send for diagnosis.

## Updates
- On launch the app quietly checks GitHub. If a new version is out, a bar appears at the top of the Activation tab.
- **One-click auto-update:** press **"Download & install"** — the app downloads the new version, replaces itself and restarts. No manual reinstall.
- Check manually: About → Check for updates.
- **Coming from v3.0?** Download the new version once from the [Releases page](https://github.com/mr1garik/iActivator/releases/latest) and replace the app. The one-click update in v3.0 is turned off for safety (on macOS it could leave an app that doesn't start); from v3.1 on it works again.
- Before installing, the download is checked (size and checksum), so a cut-off download can't replace a working app. The previous version is kept in the data folder (`previous-version`) in case you need to go back.
- An update replaces only the app itself. Device history and settings live in a separate data folder and are never lost on update.

## Download & build
- **Just want the app?** Grab the latest `iActivator-windows.exe` (Windows) or `iActivator-macos.zip` (macOS) from the [Releases page](https://github.com/mr1garik/iActivator/releases/latest).
- **Mac:** `dist/iActivator.app` — move it to Applications. Built locally with `./build_mac.sh`.
- **Windows:** `iActivator.exe` — built on a Windows machine by double-clicking `build_windows.bat` (needs Python from python.org). You'll also need "Apple Devices" from the Microsoft Store or iTunes to talk to the iPhone.
- **Build both from GitHub:** upload the folder and run the **build** workflow on the Actions tab — GitHub builds the `.exe` and the Mac version and publishes a release.

The interface opens in its own window (WebKit on Mac, Edge WebView2 on Windows). On Windows the built-in browser runs more economically (lower RAM), the close button minimizes to the tray, and Settings → Startup has a "Launch with Windows" option. On macOS there are "Show window" and "Quit" items in the menu bar. The window fits the screen (no overflow at 125–150% scaling) and remembers its size and position.

## Important
- The supervisor key is stored in `%APPDATA%\iActivator` (Windows) or `~/Library/Application Support/iActivator` (Mac). If you lose it, the iPhone must be erased before applying settings again.
- If the iPhone already has a configuration from 3uTools or another computer, press "Erase device" first.
- The app does **not** bypass iCloud Activation Lock: it's for your own or already-reset devices.

## Related projects

🩺 **[iOS Panic Reader](https://github.com/mr1garik/ios-panic-reader)** — connect an iPhone over USB and it reads the panic/crash logs and tells you in plain words which part is faulty and what to do. A natural companion to iActivator (Windows & macOS, free).

## License
MIT — free to use, modify and distribute. See [LICENSE](LICENSE).
