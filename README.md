# dnsctl

Change your DNS server in two clicks.

dnsctl is a small Windows utility that lets you switch DNS resolvers on your active network adapter — without digging through network settings or writing commands.

---

## Features

- Automatically detects your active network interface
- Shows your current DNS configuration on launch
- One-click presets: Cloudflare, Google, Quad9, OpenDNS, AdGuard
- Hover any preset to understand what it actually does
- Revert to automatic (DHCP) at any time
- English / French interface

---

## Download

Go to [Releases](../../releases) and download the latest `dnsctl.exe`.

No installation required. Just run it — Windows will ask for administrator permission, which is needed to change network settings.

---

## Presets

| | Primary | Good for |
|---|---|---|
| **Cloudflare** | 1.1.1.1 | Best speed + privacy |
| **Google** | 8.8.8.8 | Reliable fallback |
| **Quad9** | 9.9.9.9 | Blocks malware automatically |
| **AdGuard** | 94.140.14.14 | Blocks ads on every device |
| **OpenDNS** | 208.67.222.222 | Configurable filtering |
| **Automatic** | — | Reverts to your ISP's DNS |

Not sure which to pick? **Cloudflare (1.1.1.1)** is a safe default for most people.

---

## License

MIT
