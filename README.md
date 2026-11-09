<div align="center">

**🇬🇧 English** · [🇷🇺 Русский](README.ru.md)

<img src="assets/social-preview.png" alt="iActivator" width="820">

### One-click iPhone activation & setup · Windows and macOS

[![Download for Windows and macOS](https://img.shields.io/badge/⬇%20Download-Windows%20%7C%20macOS-0297DE?style=for-the-badge)](https://github.com/mr1garik/iActivator/releases/latest)

[![Downloads](https://img.shields.io/github/downloads/mr1garik/iActivator/total?label=downloads&color=0297DE)](https://github.com/mr1garik/iActivator/releases)
[![MIT license](https://img.shields.io/github/license/mr1garik/iActivator?label=license&color=0297DE)](LICENSE)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS-2E3035)
![Interface languages](https://img.shields.io/badge/UI-EN%20%7C%20UK%20%7C%20RU-0297DE)

**⭐ If it saves you time, a star helps the project grow.**

</div>

Activate and set up an iPhone over USB in one click — activation, language, region, Wi-Fi and skipping the Setup Assistant — with a health check and PDF report. Free, open-source, runs on **Windows and macOS**, with the interface in **English, Ukrainian and Russian** (Settings → App language).

## Features

- 📲 **One-click activation** through Apple's servers over USB — the phone doesn't need Wi-Fi for it
- 🌐 **Language, region, timezone, 24h** — any locale, applied in one pass
- ⏭️ **Skips the Setup Assistant** screens (supervised mode, like Apple Configurator)
- 📶 **Wi-Fi via a profile**, read back from the device to confirm it applied — fixes the usual 3uTools Wi-Fi failures
- 🩺 **Health check + PDF report** — battery, Find My, MDM, 30-day crash logs, with a clear **Pass / Fail** verdict
- 🌍 **Trilingual interface** — English, Ukrainian, Russian
- 🖥️ **Windows & macOS** — free and open-source

**💬 Feedback:** found a problem or have an idea? Open an [Issue](https://github.com/mr1garik/iActivator/issues) — the app is improved based on your feedback.

## What it looks like

![Demo: iPhone activation and setup](assets/demo.gif)

Light and dark themes:

<p align="center">
  <img src="assets/screenshot-light.png" width="49%" alt="Light theme">
  <img src="assets/screenshot-dark.png" width="49%" alt="Dark theme">
</p>

## Support: models, iOS, system

| | Support |
|---|---|
| **iPhone models** | iPhone 5s and newer (anything that runs iOS 12+). iPads activate too, but the interface is designed for iPhone. |
| **iOS versions** | iOS 12–18. Screen skipping and the Wi-Fi profile work on iOS 13+; on older versions activation still goes through, but some settings may not apply. |
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

## The app
The interface opens in its own window (WebKit on Mac, Edge WebView2 on Windows).

- **Mac:** `dist/iActivator.app`. You can move it to Applications. Built with `./build_mac.sh`.
- **Windows:** `iActivator.exe`. Built on a Windows machine by double-clicking `build_windows.bat` (needs Python from python.org). Alternative: upload the folder to GitHub and run the **build** workflow on the Actions tab — GitHub then builds both the `.exe` and the Mac version.
- On Windows you need "Apple Devices" from the Microsoft Store or iTunes to work with the iPhone.

## Settings and journal
- **Language:** English or Russian (Settings → App language).
- **Theme:** System, Light or Dark (Settings).
- **Transfer settings:** Settings → "Save to file…" writes Wi‑Fi networks, language, region, modes and theme into a single `.json`. Optionally it also includes Wi‑Fi passwords, the supervision key and device history. On another computer: "Load from file…". Passwords in the file are not encrypted.
- **Journal:** every entry has a time, device and level. Filters: main, errors only, detailed (with technical error info). Daily logs are saved to the `logs` folder in the data directory and kept for 30 days. "Export to file" collects the whole journal and device history into one text file (for your own archive). "For sharing (no numbers)" does the same but hides serial numbers, IMEI and UDID and leaves out the history — that file is safe to send for diagnosis.

## Updates
- On launch the app quietly checks GitHub. If a new version is out, a bar with a "Download" button appears at the top of the Activation tab — it opens the download page.
- Check manually: About → Check for updates.
- An update replaces only the app itself. Device history and settings live in a separate data folder and are never lost on update.

## Activation run
- **Pre-run preview.** After you press "Run", a window shows a summary of what will be applied to the iPhone: device, activation, language, region, time zone, screen skipping, supervised mode and the Wi-Fi network. The run starts only after you confirm (the "Run" button in the window). In "Auto on connect" mode the window is not shown.
- While it runs, a step list appears under the "Mode" card: activation, language & region, skip setup, Wi-Fi. Each step gets a checkmark (done), a cross (error) or a spinner (in progress).
- If a Wi-Fi network is set and "Supervised mode" is off, a yellow hint appears above the list: the network will need confirmation on the iPhone itself.
- **The PDF report** gains an "Activation run (last run)" section with the result of each step — so you can see exactly what failed (e.g. activation went through but the phone rejected the Wi-Fi profile) without repeating the whole procedure.

## Window and background
- The window fits the screen size (so it doesn't overflow at 125–150% scaling on Windows) and remembers its size and position.
- **Windows:** tray icon. The close button minimizes to the tray; quit from the icon's menu. You can reopen the window from there too.
- **Windows → Settings → Startup:** "Launch with Windows" checkbox (auto-start when the computer turns on).
- **macOS:** "Show window" and "Quit" items in the menu bar.
- On Windows the app runs its built-in browser more economically (lower RAM usage).

## Important
- The supervisor key is stored in `%APPDATA%\iActivator` (Windows) or `~/Library/Application Support/iActivator` (Mac). If you lose it, the iPhone must be erased before applying settings again.
- If the iPhone already has a configuration from 3uTools or another computer, press "Erase device" first.
- The app does **not** bypass iCloud Activation Lock: it's for your own or already-reset devices.

## License
MIT — free to use, modify and distribute. See [LICENSE](LICENSE).
