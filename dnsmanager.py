"""
dnsctl — DNS configuration utility for Windows.
Design: single-column, terminal-inspired. Amber accent, charcoal bg, Consolas.
Signature: the active DNS is shown as a large status line at the top — the most
important info is the first thing you read.
"""
from __future__ import annotations

import ctypes
import datetime
import locale
import re
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from i18n import DNS_COLORS, DNS_KNOWN, DNS_PRESETS, STRINGS

# ── Palette ───────────────────────────────────────────────────────────────────
C: dict[str, str] = {
    "bg":      "#1B1D21",   # blue-grey, not pure black
    "panel":   "#22252B",   # slightly lighter
    "input":   "#292C33",   # input fields
    "border":  "#363A42",   # hairlines
    "accent":  "#5B8FA8",   # muted slate-blue — the one color
    "green":   "#6A9E7F",   # muted sage
    "red":     "#A85B5B",   # muted brick
    "text":    "#C8CDD6",   # cool light grey
    "dim":     "#5A5F6A",   # secondary text
    "white":   "#E8ECF0",
}

# ── i18n ──────────────────────────────────────────────────────────────────────
def _detect_lang() -> str:
    try:
        # getdefaultlocale() is deprecated since 3.11 — use getlocale() instead
        code = locale.getlocale()[0]
        if code and code.lower().startswith("fr"):
            return "fr"
    except (ValueError, TypeError):
        pass
    return "en"

_lang: str = _detect_lang()

def t(key: str) -> str:
    return STRINGS[_lang].get(key, key)

_log_widget: Optional["LogPanel"] = None

def log(level: str, msg: str) -> None:
    if _log_widget is not None:
        _log_widget.append(datetime.datetime.now().strftime("%H:%M:%S"), level, msg)

# ── System ────────────────────────────────────────────────────────────────────
def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except OSError:
        return False

def _elevate() -> None:
    ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
        None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def run_netsh(*args: str) -> tuple[int, str, str]:
    cmd = ["netsh"] + list(args)
    log("CMD", " ".join(cmd[2:]))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="cp850", errors="replace",
                           creationflags=subprocess.CREATE_NO_WINDOW)
        bad = any(w in r.stdout.lower()
                  for w in ("syntaxe", "syntax", "n'est pas valide", "is not valid"))
        rc = 1 if bad else r.returncode
        if bad:
            log("ERR", "syntax rejected")
        elif r.stderr.strip():
            log("WARN", r.stderr.strip()[:100])
        return rc, r.stdout, r.stderr
    except OSError as exc:
        log("ERR", str(exc))
        return -1, "", str(exc)

def get_interfaces() -> list[tuple[str, bool]]:
    _, out, _ = run_netsh("interface", "show", "interface")
    result: list[tuple[str, bool]] = []
    for line in out.splitlines()[2:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            result.append((" ".join(parts[3:]),
                           parts[1] in ("Connecté", "Connected")))
    return result

def get_active(ifaces: list[tuple[str, bool]]) -> Optional[str]:
    for name, up in ifaces:
        if up:
            return name
    return ifaces[0][0] if ifaces else None

def get_dns(iface: str) -> tuple[str, str]:
    _, out, _ = run_netsh("interface", "ip", "show", "dnsservers", iface)
    s = re.findall(r"(\d{1,3}(?:\.\d{1,3}){3})", out)
    return (s[0] if s else ""), (s[1] if len(s) > 1 else "")

def set_dns(iface: str, primary: str, secondary: str) -> tuple[bool, str]:
    if not iface:
        return False, "no interface"
    if not primary:
        log("INFO", f"dhcp {iface}")
        rc, out, err = run_netsh("interface", "ip", "set", "dnsservers",
                                 iface, "dhcp")
        return (True, t("dhcp_ok")) if rc == 0 else (False, err or out)
    ip_re = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
    for addr in (primary, secondary):
        if addr and not ip_re.match(addr):
            return False, f"invalid IP: {addr}"
    log("INFO", f"primary {primary}")
    rc, out, err = run_netsh("interface", "ip", "set", "dnsservers",
                             iface, "static", primary, "no")
    if rc != 0:
        return False, err or out
    if secondary:
        log("INFO", f"secondary {secondary}")
        rc, out, err = run_netsh("interface", "ip", "add", "dnsservers",
                                 iface, secondary, "index=2")
        if rc != 0:
            return False, err or out
    return True, t("applied")

# ── Tooltip ───────────────────────────────────────────────────────────────────
class Tooltip:
    """Small popup shown on hover over the ⓘ button next to each preset."""

    def __init__(self, anchor: tk.Widget, key: str) -> None:
        self._anchor = anchor
        self._key    = key
        self._win: Optional[tk.Toplevel] = None
        anchor.bind("<Enter>", self._show)
        anchor.bind("<Leave>", self._hide)

    def _show(self, _event=None) -> None:
        if self._win:
            return
        info = STRINGS[_lang]["dns_info"].get(self._key)
        if not info:
            return
        tag, desc = info
        color = DNS_COLORS.get(self._key, C["dim"])

        win = tk.Toplevel(self._anchor)
        self._win = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=C["border"])

        inner = tk.Frame(win, bg=C["panel"], padx=14, pady=10)
        inner.pack(padx=1, pady=1)

        tk.Label(inner, text=tag, font=("Consolas", 8, "bold"),
                 fg=color, bg=C["panel"]).pack(anchor="w")
        tk.Frame(inner, height=1, bg=C["border"]).pack(fill="x", pady=(4, 6))
        tk.Label(inner, text=desc, font=("Consolas", 8),
                 fg=C["text"], bg=C["panel"], justify="left").pack(anchor="w")

        win.update_idletasks()
        # Position above the anchor
        ax = self._anchor.winfo_rootx()
        ay = self._anchor.winfo_rooty()
        tw = win.winfo_width()
        th = win.winfo_height()
        # center horizontally over anchor, show above it
        x = ax + self._anchor.winfo_width() // 2 - tw // 2
        y = ay - th - 6
        win.geometry(f"+{x}+{y}")

    def _hide(self, _event=None) -> None:
        if self._win:
            self._win.destroy()
            self._win = None

# ── Log panel ─────────────────────────────────────────────────────────────────
class LogPanel(tk.Frame):
    _COLORS = {"INFO": "#5A5F6A", "CMD": "#5B8FA8", "OK": "#6A9E7F",
               "ERR": "#A85B5B", "WARN": "#8A7F5A"}
    _ICONS  = {"OK": "+", "ERR": "!", "WARN": "~", "CMD": ">", "INFO": " "}

    def __init__(self, parent: tk.Misc, **kw) -> None:
        super().__init__(parent, bg=C["bg"], **kw)
        hdr = tk.Frame(self, bg=C["panel"])
        hdr.pack(fill="x")
        self._title = tk.Label(hdr, text="", font=("Consolas", 8, "bold"),
                               fg=C["dim"], bg=C["panel"], padx=10, pady=5)
        self._title.pack(side="left")
        clr = tk.Label(hdr, text="clr", font=("Consolas", 8),
                       fg=C["dim"], bg=C["panel"], padx=10, pady=5,
                       cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda _e: self.clear())

        self._txt = tk.Text(self, font=("Consolas", 9), bg=C["input"],
                            fg=C["text"], relief="flat", bd=0,
                            height=5, wrap="none", state="disabled",
                            padx=10, pady=6, cursor="arrow")
        sb = ttk.Scrollbar(self, command=self._txt.yview)
        self._txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._txt.pack(fill="both", expand=True)
        for tag, color in self._COLORS.items():
            self._txt.tag_configure(tag, foreground=color)

    def refresh_lang(self) -> None:
        self._title.config(text=t("logs").upper())

    def append(self, ts: str, level: str, msg: str) -> None:
        self._txt.configure(state="normal")
        tag  = level if level in self._COLORS else "INFO"
        icon = self._ICONS.get(level, " ")
        self._txt.insert("end", f"{ts}  {icon}  {msg}\n", tag)
        self._txt.see("end")
        self._txt.configure(state="disabled")

    def clear(self) -> None:
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.configure(state="disabled")

# ── Success dialog ─────────────────────────────────────────────────────────────
class SuccessDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, iface: str,
                 primary: str, secondary: str) -> None:
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=C["border"])
        self.attributes("-topmost", True)

        body = tk.Frame(self, bg=C["panel"], padx=28, pady=24)
        body.pack(padx=1, pady=1)

        # green top accent line
        tk.Frame(body, bg=C["green"], height=2).pack(fill="x", pady=(0, 16))

        tk.Label(body, text=t("popup_title"), font=("Consolas", 11, "bold"),
                 fg=C["green"], bg=C["panel"]).pack(anchor="w")
        tk.Label(body, text=iface, font=("Consolas", 9),
                 fg=C["dim"], bg=C["panel"]).pack(anchor="w", pady=(6, 0))

        tk.Frame(body, height=1, bg=C["border"]).pack(fill="x", pady=(12, 10))

        for label, val in ((t("primary"),   primary   or "DHCP"),
                           (t("secondary"), secondary or "—")):
            row = tk.Frame(body, bg=C["panel"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=("Consolas", 8),
                     fg=C["dim"], bg=C["panel"], width=12, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=("Consolas", 9, "bold"),
                     fg=C["green"], bg=C["panel"]).pack(side="left")

        tk.Frame(body, height=1, bg=C["border"]).pack(fill="x", pady=(14, 12))

        btn = tk.Label(body, text=t("ok"), font=("Consolas", 9, "bold"),
                       fg=C["bg"], bg=C["green"], padx=20, pady=6, cursor="hand2")
        btn.pack(anchor="w")
        btn.bind("<Button-1>", lambda _e: self.destroy())

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.grab_set()

# ── Application ───────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("dnsctl")
        self.resizable(False, False)
        self.configure(bg=C["bg"])

        self._iface_var   = tk.StringVar()
        self._primary_var = tk.StringVar()
        self._second_var  = tk.StringVar()

        self._ifaces:    list[tuple[str, bool]] = []
        self._inames:    list[str]              = []
        self._combo_idx: int                    = 0
        self._combo_var: tk.StringVar           = tk.StringVar()

        self._build()

        global _log_widget
        _log_widget = self._log_panel
        self._log_panel.refresh_lang()

        log("INFO", f"admin={is_admin()}  py={sys.version.split()[0]}")
        self.update_idletasks()
        self._load()
        self._center()

    def _center(self) -> None:
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        P = 20  # horizontal padding

        # ── Header bar ────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=C["panel"])
        bar.pack(fill="x")

        tk.Label(bar, text="dnsctl", font=("Consolas", 13, "bold"),
                 fg=C["accent"], bg=C["panel"], padx=P, pady=12).pack(side="left")

        # vertical divider
        tk.Frame(bar, width=1, bg=C["border"]).pack(side="left", fill="y",
                                                    pady=8)
        self._subtitle = tk.Label(bar, text=t("subtitle"),
                                  font=("Consolas", 9), fg=C["dim"],
                                  bg=C["panel"], padx=14)
        self._subtitle.pack(side="left")

        # lang toggle
        lang_f = tk.Frame(bar, bg=C["panel"])
        lang_f.pack(side="right", padx=P)
        self._lang_btns: dict[str, tk.Label] = {}
        for code in ("en", "fr"):
            lbl = tk.Label(lang_f, text=code.upper(),
                           font=("Consolas", 8, "bold"),
                           bg=C["panel"], cursor="hand2", padx=5, pady=12)
            lbl.bind("<Button-1>", lambda _e, c=code: self._switch_lang(c))
            lbl.pack(side="left")
            self._lang_btns[code] = lbl
        self._update_lang_btns()

        tk.Frame(self, height=1, bg=C["border"]).pack(fill="x")

        # ── Active DNS status — the hero element ──────────────────────────────
        self._hero = tk.Frame(self, bg=C["panel"])
        self._hero.pack(fill="x")

        # left accent bar
        tk.Frame(self._hero, width=3, bg=C["accent"]).pack(side="left",
                                                           fill="y")
        hero_inner = tk.Frame(self._hero, bg=C["panel"],
                              padx=P, pady=14)
        hero_inner.pack(side="left", fill="x", expand=True)

        self._hero_label = tk.Label(hero_inner, text="",
                                    font=("Consolas", 8), fg=C["dim"],
                                    bg=C["panel"], anchor="w")
        self._hero_label.pack(anchor="w")

        self._hero_provider = tk.Label(hero_inner, text="",
                                       font=("Consolas", 16, "bold"),
                                       fg=C["accent"], bg=C["panel"],
                                       anchor="w")
        self._hero_provider.pack(anchor="w", pady=(2, 0))

        self._hero_ip = tk.Label(hero_inner, text="",
                                 font=("Consolas", 9), fg=C["dim"],
                                 bg=C["panel"], anchor="w")
        self._hero_ip.pack(anchor="w")

        tk.Frame(self, height=1, bg=C["border"]).pack(fill="x")

        # ── Main content ──────────────────────────────────────────────────────
        content = tk.Frame(self, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=P, pady=P)

        # Interface selector
        self._field_label(content, "network_iface")
        self._build_combo(content)

        # Current DNS (compact)
        self._field_label(content, "current_cfg", pady_top=14)
        dns_row = tk.Frame(content, bg=C["input"])
        dns_row.pack(fill="x", pady=(4, 0))
        dns_inner = tk.Frame(dns_row, bg=C["input"], padx=12, pady=8)
        dns_inner.pack(fill="x")
        dns_inner.columnconfigure(1, weight=1)
        dns_inner.columnconfigure(3, weight=1)

        tk.Label(dns_inner, text=t("primary"), font=("Consolas", 8),
                 fg=C["dim"], bg=C["input"]).grid(row=0, column=0,
                                                  sticky="w", padx=(0, 10))
        self._cur_p = tk.Label(dns_inner, text="—",
                               font=("Consolas", 9, "bold"),
                               fg=C["text"], bg=C["input"])
        self._cur_p.grid(row=0, column=1, sticky="w")

        tk.Frame(dns_inner, width=1, bg=C["border"]).grid(
            row=0, column=2, sticky="ns", padx=14)

        tk.Label(dns_inner, text=t("secondary"), font=("Consolas", 8),
                 fg=C["dim"], bg=C["input"]).grid(row=0, column=3,
                                                  sticky="w", padx=(0, 10))
        self._cur_s = tk.Label(dns_inner, text="—", font=("Consolas", 9),
                               fg=C["dim"], bg=C["input"])
        self._cur_s.grid(row=0, column=4, sticky="w")

        # Preset chips with ⓘ tooltips
        self._field_label(content, "quick", pady_top=14)
        self._preset_frame = tk.Frame(content, bg=C["bg"])
        self._preset_frame.pack(fill="x", pady=(4, 0))
        self._build_presets()

        # New DNS inputs
        self._field_label(content, "new_primary", pady_top=14)
        self._entry_p = self._build_entry(content, self._primary_var)

        self._field_label(content, "new_secondary", pady_top=8)
        self._entry_s = self._build_entry(content, self._second_var)

        # Action buttons
        btn_row = tk.Frame(content, bg=C["bg"])
        btn_row.pack(fill="x", pady=(14, 0))

        self._btn_apply   = self._make_btn(btn_row, t("apply"),
                                           self._apply, C["accent"], C["bg"])
        self._btn_apply.pack(side="left")
        self._btn_auto    = self._make_btn(btn_row, t("auto_btn"),
                                           self._set_auto, C["input"], C["text"])
        self._btn_auto.pack(side="left", padx=(4, 0))
        self._btn_refresh = self._make_btn(btn_row, t("refresh"),
                                           self._load, C["input"], C["dim"])
        self._btn_refresh.pack(side="left", padx=(4, 0))

        # Feedback
        self._fb = tk.Label(content, text="", font=("Consolas", 9),
                            fg=C["dim"], bg=C["bg"], anchor="w")
        self._fb.pack(fill="x", pady=(8, 0))

        tk.Frame(content, height=1, bg=C["border"]).pack(
            fill="x", pady=(8, 0))

        # Log panel
        self._log_label = tk.Label(content, text=t("logs").upper(),
                                   font=("Consolas", 8),
                                   fg=C["dim"], bg=C["bg"])
        self._log_label.pack(anchor="w", pady=(8, 0))
        self._log_panel = LogPanel(content)
        self._log_panel.pack(fill="both", expand=True, pady=(4, 0))

        # Footer
        footer = tk.Frame(content, bg=C["bg"])
        footer.pack(fill="x", pady=(8, 0))
        tk.Label(footer, text="Made by ", font=("Consolas", 7),
                 fg=C["dim"], bg=C["bg"]).pack(side="left")
        link = tk.Label(footer, text="Narkos", font=("Consolas", 7),
                        fg=C["accent"], bg=C["bg"], cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>",
                  lambda _e: self._open_url("https://github.com/narkos69"))
        tk.Label(footer, text=" · dnsctl", font=("Consolas", 7),
                 fg=C["dim"], bg=C["bg"]).pack(side="left")

    # ── Widget helpers ────────────────────────────────────────────────────────
    def _field_label(self, parent: tk.Frame, key: str,
                     pady_top: int = 0) -> tk.Label:
        lbl = tk.Label(parent, text=t(key).upper(),
                       font=("Consolas", 8), fg=C["dim"], bg=C["bg"])
        lbl.pack(anchor="w", pady=(pady_top, 0))
        return lbl

    def _build_combo(self, parent: tk.Frame) -> None:
        # Custom dropdown — ttk.Combobox readonly ignores StringVar on Windows
        self._combo_var  = tk.StringVar()   # display text only
        self._combo_idx  = 0

        wrapper = tk.Frame(parent, bg=C["input"],
                           highlightbackground=C["border"],
                           highlightthickness=1)
        wrapper.pack(fill="x", pady=(4, 0))

        self._combo_lbl = tk.Label(wrapper, textvariable=self._combo_var,
                                   font=("Consolas", 10), fg=C["text"],
                                   bg=C["input"], anchor="w",
                                   padx=10, pady=7, cursor="hand2")
        self._combo_lbl.pack(side="left", fill="x", expand=True)

        arrow = tk.Label(wrapper, text="▾", font=("Consolas", 10),
                         fg=C["dim"], bg=C["input"], padx=10, cursor="hand2")
        arrow.pack(side="right")

        self._combo_lbl.bind("<Button-1>", lambda _e: self._open_dropdown())
        arrow.bind("<Button-1>",           lambda _e: self._open_dropdown())
        self._combo_wrapper = wrapper

    def _open_dropdown(self) -> None:
        if not self._inames:
            return
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg=C["border"])
        popup.attributes("-topmost", True)

        x = self._combo_wrapper.winfo_rootx()
        y = self._combo_wrapper.winfo_rooty() + self._combo_wrapper.winfo_height()
        w = self._combo_wrapper.winfo_width()

        for i, (name, up) in enumerate(self._ifaces):
            bullet = "●" if up else "○"
            display = f"  {bullet}  {name}"
            bg_item = C["input"] if i % 2 == 0 else C["panel"]
            row = tk.Label(popup, text=display, font=("Consolas", 10),
                           fg=C["text"] if up else C["dim"],
                           bg=bg_item, anchor="w",
                           padx=8, pady=6, cursor="hand2",
                           width=w // 8)
            row.pack(fill="x")
            row.bind("<Enter>", lambda _e, r=row: r.config(bg=C["border"]))
            row.bind("<Leave>", lambda _e, r=row, b=bg_item: r.config(bg=b))
            row.bind("<Button-1>",
                     lambda _e, idx=i, p=popup: self._pick_iface(idx, p))

        popup.update_idletasks()
        popup.geometry(f"{w}x{popup.winfo_height()}+{x}+{y}")

        # close on click outside
        popup.bind("<FocusOut>", lambda _e: popup.destroy())
        popup.focus_set()

    def _pick_iface(self, idx: int, popup: tk.Toplevel) -> None:
        popup.destroy()
        self._combo_idx = idx
        name, up = self._ifaces[idx]
        bullet = "●" if up else "○"
        self._combo_var.set(f"  {bullet}  {name}")
        self._iface_var.set(name)
        self._on_iface()

    def _build_entry(self, parent: tk.Frame,
                     var: tk.StringVar) -> tk.Frame:
        frame = tk.Frame(parent, bg=C["input"],
                         highlightbackground=C["border"],
                         highlightthickness=1)
        frame.pack(fill="x", pady=(4, 0))
        tk.Label(frame, text=">", font=("Consolas", 9),
                 fg=C["dim"], bg=C["input"], padx=10).pack(side="left")
        tk.Frame(frame, width=1, bg=C["border"]).pack(
            side="left", fill="y", pady=4)
        e = tk.Entry(frame, textvariable=var, font=("Consolas", 11),
                     bg=C["input"], fg=C["text"],
                     insertbackground=C["accent"],
                     relief="flat", bd=8, highlightthickness=0)
        e.pack(side="left", fill="x", expand=True)
        e.bind("<FocusIn>",
               lambda _e: frame.config(highlightbackground=C["accent"]))
        e.bind("<FocusOut>",
               lambda _e: frame.config(highlightbackground=C["border"]))
        return frame

    @staticmethod
    def _make_btn(parent: tk.Frame, text: str, cmd: Callable,
                  bg: str, fg: str) -> tk.Label:
        lbl = tk.Label(parent, text=text, font=("Consolas", 9, "bold"),
                       fg=fg, bg=bg, padx=16, pady=8, cursor="hand2")

        def _darken(h: str) -> str:
            r, g, b = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
            return "#{:02x}{:02x}{:02x}".format(
                max(r-25,0), max(g-25,0), max(b-25,0))

        dim = _darken(bg)
        lbl.bind("<Enter>",    lambda _e: lbl.config(bg=dim))
        lbl.bind("<Leave>",    lambda _e: lbl.config(bg=bg))
        lbl.bind("<Button-1>", lambda _e: cmd())
        return lbl

    def _build_presets(self) -> None:
        for w in self._preset_frame.winfo_children():
            w.destroy()

        for col, (key, primary, _sec) in enumerate(DNS_PRESETS):
            label = t("preset_auto") if key == "Automatic" else key
            color = DNS_COLORS.get(key, C["dim"])

            cell = tk.Frame(self._preset_frame, bg=C["input"],
                            cursor="hand2")
            cell.grid(row=0, column=col, padx=(0, 2), sticky="nsew")
            self._preset_frame.columnconfigure(col, weight=1)

            # Name
            name_lbl = tk.Label(cell, text=label,
                                font=("Consolas", 8, "bold"),
                                fg=C["text"], bg=C["input"],
                                padx=8, pady=6)
            name_lbl.pack()

            # IP
            ip_lbl = tk.Label(cell, text=primary or "DHCP",
                              font=("Consolas", 7), fg=C["dim"],
                              bg=C["input"])
            ip_lbl.pack()

            # ⓘ info button — hover shows tooltip
            info_btn = tk.Label(cell, text="i",
                                font=("Consolas", 7, "bold"),
                                fg=color, bg=C["input"],
                                pady=4, cursor="hand2")
            info_btn.pack()
            Tooltip(info_btn, key)

            # click anywhere on cell selects preset
            for w in [cell, name_lbl, ip_lbl]:
                w.bind("<Button-1>",
                       lambda _e, p=primary, s=_sec, k=key, c=cell:
                       self._select_preset(p, s, k, c))
                w.bind("<Enter>",
                       lambda _e, c=cell, lbls=[name_lbl, ip_lbl, info_btn]:
                       self._chip_hover(c, lbls, True))
                w.bind("<Leave>",
                       lambda _e, c=cell, lbls=[name_lbl, ip_lbl, info_btn]:
                       self._chip_hover(c, lbls, False))

        self._active_chip: Optional[tk.Frame] = None

    def _chip_hover(self, cell: tk.Frame, labels: list[tk.Label],
                    entering: bool) -> None:
        if cell is self._active_chip:
            return
        bg = C["border"] if entering else C["input"]
        cell.config(bg=bg)
        for lbl in labels:
            lbl.config(bg=bg)

    def _select_preset(self, primary: str, secondary: str,
                       _key: str, cell: tk.Frame) -> None:
        # reset previous active chip
        if self._active_chip is not None and self._active_chip is not cell:
            self._active_chip.config(bg=C["input"],
                                     highlightthickness=0)
            for ch in self._active_chip.winfo_children():
                ch.config(bg=C["input"])
        self._active_chip = cell
        cell.config(bg=C["border"],
                    highlightbackground=C["accent"],
                    highlightthickness=1)
        for ch in cell.winfo_children():
            ch.config(bg=C["border"])
        self._primary_var.set(primary)
        self._second_var.set(secondary)
        self._fb.config(text="")

    # ── Language ──────────────────────────────────────────────────────────────
    def _switch_lang(self, code: str) -> None:
        global _lang
        _lang = code
        self._update_lang_btns()
        self._refresh_text()
        self._build_presets()
        self._log_panel.refresh_lang()
        self._load()

    def _update_lang_btns(self) -> None:
        for code, lbl in self._lang_btns.items():
            lbl.config(fg=C["accent"] if code == _lang else C["dim"])

    def _refresh_text(self) -> None:
        self._subtitle.config(text=t("subtitle"))
        self._btn_apply.config(text=t("apply"))
        self._btn_auto.config(text=t("auto_btn"))
        self._btn_refresh.config(text=t("refresh"))
        self._log_label.config(text=t("logs").upper())

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load(self) -> None:
        self._ifaces = get_interfaces()
        self._inames = [n for n, _ in self._ifaces]
        active = get_active(self._ifaces)
        idx = next((i for i, (n, _) in enumerate(self._ifaces)
                    if n == active), 0)
        if self._ifaces:
            self._combo_idx = idx
            name, up = self._ifaces[idx]
            bullet = "●" if up else "○"
            self._combo_var.set(f"  {bullet}  {name}")
            self._iface_var.set(name)
        self._on_iface()
        self._fb_set(t("refreshed"), C["green"])

    def _real_iface(self) -> str:
        # _iface_var is set directly to the interface name (no prefix)
        val = self._iface_var.get().strip()
        if val in self._inames:
            return val
        # fallback: use stored index
        if 0 <= self._combo_idx < len(self._inames):
            return self._inames[self._combo_idx]
        return val

    def _on_iface(self) -> None:
        iface = self._real_iface()
        if not iface:
            return
        p, s = get_dns(iface)
        self._cur_p.config(text=p if p else t("auto_dhcp"),
                           fg=C["text"] if p else C["dim"])
        self._cur_s.config(text=s if s else "—",
                           fg=C["dim"])
        self._primary_var.set(p)
        self._second_var.set(s)
        self._update_hero(iface, p)
        self._fb.config(text="")

    def _update_hero(self, iface: str, primary_ip: str) -> None:
        self._hero_label.config(text=iface)
        if not primary_ip:
            self._hero_provider.config(text=t("using_isp"),
                                       fg=C["dim"])
            self._hero_ip.config(text="DHCP")
        else:
            provider = DNS_KNOWN.get(primary_ip)
            if provider:
                color = DNS_COLORS.get(provider, C["accent"])
                self._hero_provider.config(text=provider, fg=color)
            else:
                self._hero_provider.config(text=t("using_unknown"),
                                           fg=C["dim"])
            self._hero_ip.config(text=primary_ip)

    def _open_url(self, url: str) -> None:
        import webbrowser
        webbrowser.open(url)

    def _fb_set(self, msg: str, color: str = C["dim"]) -> None:
        self._fb.config(text=msg, fg=color)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _apply(self) -> None:
        iface   = self._real_iface()
        primary = self._primary_var.get().strip()
        second  = self._second_var.get().strip()
        if not iface:
            self._fb_set(t("no_iface"), C["red"])
            return
        ok, msg = set_dns(iface, primary, second)
        if ok:
            self._fb_set(msg, C["green"])
            self._on_iface()
            SuccessDialog(self, iface, primary, second)
        else:
            self._fb_set(t("fail_logs"), C["red"])

    def _set_auto(self) -> None:
        iface = self._real_iface()
        ok, msg = set_dns(iface, "", "")
        if ok:
            self._fb_set(msg, C["green"])
            self._on_iface()
            SuccessDialog(self, iface, "", "")
        else:
            self._fb_set(t("fail_logs"), C["red"])


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if sys.platform != "win32":
        print("Windows only.")
        sys.exit(1)
    if not is_admin():
        _elevate()
        sys.exit(0)
    App().mainloop()