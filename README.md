# dnsctl

> DNS server configuration utility for Windows — GUI tool with a sysadmin aesthetic.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What it does

dnsctl lets you view and change the DNS servers of any active Windows network adapter — without touching `ncpa.cpl` or writing netsh commands by hand.

- Detects your active interface on launch and shows its current DNS
- One-click presets: Google, Cloudflare, OpenDNS, Quad9, AdGuard, or revert to DHCP
- Hover any preset to read what it actually does (privacy, filtering, speed)
- Diagnostic output panel — every netsh command and its result is shown inline
- English / French UI, switchable at runtime

```
$ Ethernet 3  ›  1.1.1.1
```

---

## Requirements

- Windows 10 / 11
- Python 3.10+ with `tkinter` (included in the standard installer)
- Administrator privileges (the app prompts UAC automatically)

---

## Run from source

```bash
git clone https://github.com/yourname/dnsctl
cd dnsctl
python dns_manager.py
```

No dependencies to install. `tkinter` and `subprocess` are stdlib.

---

## Build a standalone executable

Install [PyInstaller](https://pyinstaller.org) into your environment:

```bash
pip install pyinstaller
```

Then build a single `.exe` with UAC elevation baked in:

```bash
pyinstaller --onefile --windowed --uac-admin --name "dnsctl" dns_manager.py
```

| Flag | Effect |
|------|--------|
| `--onefile` | Packages everything into a single portable `.exe` |
| `--windowed` | Suppresses the CMD window on launch |
| `--uac-admin` | Embeds a UAC manifest — Windows will request elevation automatically |

The output is at `dist/dnsctl.exe`. No Python installation required on the target machine.

To add a custom icon:

```bash
pyinstaller --onefile --windowed --uac-admin --icon=icon.ico --name "dnsctl" dns_manager.py
```

Any `.ico` file works. You can convert a PNG at [convertio.co](https://convertio.co/png-ico/).

---

## Project structure

```
dnsctl/
├── dns_manager.py   # application — UI, logic, netsh calls
├── i18n.py          # all translatable strings and DNS preset data
└── README.md
```

Adding a new language means adding one block to `i18n.py`. The key just needs to appear in `STRINGS` and the language toggle in the UI will pick it up via `AVAILABLE_LANGS`.

---

## DNS presets

| Name | Primary | Secondary | Notes |
|------|---------|-----------|-------|
| Google | 8.8.8.8 | 8.8.4.4 | Fast, logs queries |
| Cloudflare | 1.1.1.1 | 1.0.0.1 | Fastest, best privacy |
| OpenDNS | 208.67.222.222 | 208.67.220.220 | Cisco, configurable filtering |
| Quad9 | 9.9.9.9 | 149.112.112.112 | Blocks malware, Swiss-based |
| AdGuard | 94.140.14.14 | 94.140.15.15 | Blocks ads network-wide |
| Automatic | — | — | Reverts to DHCP / ISP resolver |

---

## Notes

- The app calls `netsh interface ip set dnsservers` — the same command Windows uses internally
- Administrator rights are required to write network adapter settings; the app re-launches itself via `ShellExecuteW` with `runas` if not already elevated
- Tested on Windows 10 and Windows 11 with French and English system locales

---

## License

MIT
