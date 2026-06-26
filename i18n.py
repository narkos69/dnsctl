"""
i18n.py — dnsctl
All user-visible strings and DNS preset metadata.
"""
from __future__ import annotations

STRINGS: dict[str, dict] = {
    "en": {
        "subtitle":      "DNS server configuration utility",
        "network_iface": "INTERFACE",
        "current_cfg":   "ACTIVE CONFIG",
        "primary":       "PRIMARY",
        "secondary":     "SECONDARY",
        "auto_dhcp":     "DHCP",
        "quick":         "PRESETS",
        "new_primary":   "SET PRIMARY",
        "new_secondary": "SET SECONDARY  (optional)",
        "apply":         "APPLY",
        "auto_btn":      "SET DHCP",
        "refresh":       "RELOAD",
        "logs":          "OUTPUT",
        "clear":         "CLR",
        "no_iface":      "ERR: no interface selected",
        "fail_logs":     "ERR: command failed — see output",
        "refreshed":     "OK: interfaces reloaded",
        "dhcp_ok":       "OK: reverted to DHCP",
        "applied":       "OK: DNS applied",
        "popup_title":   "DNS UPDATED",
        "ok":            "CLOSE",
        "active":        "UP",
        "preset_auto":   "AUTOMATIC",
        "using_dns":     "Currently using",
        "using_isp":     "your ISP's DNS",
        "using_unknown": "unknown resolver",
        "recommend_lbl": "RECOMMENDED FOR",
        "dns_info": {
            "Google":     ("FAST",     "Very fast, globally reliable.\nCaveat: Google logs queries\nfor ad-targeting purposes."),
            "Cloudflare": ("FASTEST",  "~1ms. Best privacy of the list:\nno IP logging, independently\naudited by KPMG."),
            "OpenDNS":    ("FILTERED", "Cisco-owned. Blocks malicious\ndomains. Configurable ACLs.\nLogs all queries."),
            "Quad9":      ("SECURE",   "Blocks malware & phishing at\nresolution time. Swiss-based,\nno PII logging."),
            "AdGuard":    ("AD-FREE",  "Drops ad/tracker domains at DNS.\nNetwork-wide effect — works on\nevery device without a plugin."),
            "Automatic":  ("ISP",      "Delegates to your ISP resolver.\nTypically slow. Queries are\nlogged and may be sold."),
        },
        "recommendations": [
            ("Gaming / low latency",       "Cloudflare",  "1.1.1.1 — fastest resolution worldwide"),
            ("Privacy",                    "Cloudflare",  "No IP logs, audited by KPMG"),
            ("Security / malware block",   "Quad9",       "Blocks known malicious domains at query time"),
            ("Ad-free network",            "AdGuard",     "Drops ads on every device, no plugin needed"),
            ("Movie / series streaming",   "Google",      "8.8.8.8 — reliable, unfiltered, fast CDN routing"),
            ("Online gambling / casino",   "Google",      "8.8.8.8 — unfiltered, no category blocking"),
            ("Parental / work filtering",  "OpenDNS",     "Configurable domain category blocking"),
            ("General use",               "Cloudflare",  "Best all-round: speed + privacy"),
        ],
    },
    "fr": {
        "subtitle":      "Utilitaire de configuration DNS",
        "network_iface": "INTERFACE",
        "current_cfg":   "CONFIG ACTIVE",
        "primary":       "PRIMAIRE",
        "secondary":     "SECONDAIRE",
        "auto_dhcp":     "DHCP",
        "quick":         "PRÉSETS",
        "new_primary":   "DNS PRIMAIRE",
        "new_secondary": "DNS SECONDAIRE  (optionnel)",
        "apply":         "APPLIQUER",
        "auto_btn":      "DHCP AUTO",
        "refresh":       "RECHARGER",
        "logs":          "SORTIE",
        "clear":         "CLR",
        "no_iface":      "ERR: aucune interface",
        "fail_logs":     "ERR: commande échouée — voir sortie",
        "refreshed":     "OK: interfaces rechargées",
        "dhcp_ok":       "OK: DHCP rétabli",
        "applied":       "OK: DNS appliqués",
        "popup_title":   "DNS MIS À JOUR",
        "ok":            "FERMER",
        "active":        "UP",
        "preset_auto":   "AUTOMATIQUE",
        "using_dns":     "DNS actuel",
        "using_isp":     "DNS de votre FAI",
        "using_unknown": "résolveur inconnu",
        "recommend_lbl": "RECOMMANDÉ POUR",
        "dns_info": {
            "Google":     ("RAPIDE",    "Très rapide et fiable.\nAttention : Google logue les requêtes\npour le ciblage publicitaire."),
            "Cloudflare": ("LE + VITE", "~1ms. Meilleure confidentialité :\npas de log IP, audité par KPMG\nindépendamment."),
            "OpenDNS":    ("FILTRAGE",  "Cisco. Bloque les domaines\nmalveillants, configurable.\nLogge toutes les requêtes."),
            "Quad9":      ("SÉCURISÉ",  "Bloque malwares et phishing à la\nrésolution. Suisse, pas de\nlog de données personnelles."),
            "AdGuard":    ("SANS PUBS", "Coupe pubs et trackers au niveau\nDNS pour tout le réseau — sans\nextension sur chaque appareil."),
            "Automatic":  ("FAI",       "Délègue au résolveur de votre FAI.\nSouvent lent. Les requêtes sont\nloguées et parfois revendues."),
        },
        "recommendations": [
            ("Gaming / latence faible",       "Cloudflare",  "1.1.1.1 — résolution la plus rapide au monde"),
            ("Confidentialité",               "Cloudflare",  "Pas de log IP, audité par KPMG"),
            ("Sécurité / blocage malwares",   "Quad9",       "Bloque les domaines malveillants à la requête"),
            ("Réseau sans pub",               "AdGuard",     "Coupe les pubs sur tous les appareils, sans plugin"),
            ("Streaming films / séries",      "Google",      "8.8.8.8 — fiable, non filtré, bon routage CDN"),
            ("Jeux d'argent / casino en ligne","Google",     "8.8.8.8 — non filtré, pas de blocage de catégorie"),
            ("Filtrage parental / pro",        "OpenDNS",    "Blocage de catégories configurable"),
            ("Usage général",                 "Cloudflare",  "Meilleur compromis : vitesse + confidentialité"),
        ],
    },
}

# DNS preset data — (key, primary IP, secondary IP)
DNS_PRESETS: list[tuple[str, str, str]] = [
    ("Google",    "8.8.8.8",        "8.8.4.4"),
    ("Cloudflare","1.1.1.1",        "1.0.0.1"),
    ("OpenDNS",   "208.67.222.222", "208.67.220.220"),
    ("Quad9",     "9.9.9.9",        "149.112.112.112"),
    ("AdGuard",   "94.140.14.14",   "94.140.15.15"),
    ("Automatic", "",               ""),
]

# Map known IPs → provider name (used for "currently using X" banner)
DNS_KNOWN: dict[str, str] = {
    "8.8.8.8":        "Google",
    "8.8.4.4":        "Google",
    "1.1.1.1":        "Cloudflare",
    "1.0.0.1":        "Cloudflare",
    "208.67.222.222": "OpenDNS",
    "208.67.220.220": "OpenDNS",
    "9.9.9.9":        "Quad9",
    "149.112.112.112":"Quad9",
    "94.140.14.14":   "AdGuard",
    "94.140.15.15":   "AdGuard",
}

DNS_COLORS: dict[str, str] = {
    "Google":    "#7A9E6E",   # muted olive-green
    "Cloudflare":"#5B8FA8",   # slate-blue (matches accent)
    "OpenDNS":   "#8A7FB5",   # dusty purple
    "Quad9":     "#4E8A8A",   # teal
    "AdGuard":   "#A8695B",   # terracotta
    "Automatic": "#5A5F6A",   # neutral grey
}

AVAILABLE_LANGS: list[str] = list(STRINGS.keys())