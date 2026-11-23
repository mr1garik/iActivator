## iActivator 3.0.4

**Download:** Windows — `iActivator-windows-setup.exe` (installer, recommended) or `iActivator-windows-portable.zip` (no installation). macOS — `iActivator-macos.zip`.

### ⚠️ Windows: install this version by hand once
Some Windows users saw the **update get stuck on "Installing…"** when updating to 3.0.3. The cause is fixed in 3.0.4, but the fix only runs once you are *on* 3.0.4 — the update that brings you *to* it still uses the old updater and can stall. So on Windows, **close the app, download `iActivator-windows-setup.exe` and run it once.** Your history and settings are kept. After that, updates install themselves. On macOS the in-app update works as usual.

### What's new
- **Fixed the stuck Windows update.** The installer now runs directly (no PowerShell, which antivirus could block) and force-closes the old app so files are always replaced. If anything still stalls, the app offers the download page instead of hanging, and a too-long download does the same.
- **"Report a problem" button** (About page): sends a report — version, system and the journal with serial numbers, IMEIs and UDIDs hidden — as a GitHub issue, or copy/save it to send another way.
- **QR code for the crypto wallet** on the About page, so it can be scanned to donate.

iActivator activates and sets up iPhones through Apple's servers. It does not bypass iCloud Activation Lock.
