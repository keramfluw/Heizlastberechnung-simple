# Heizlastberechnung Q¹ / Q² / Q³ – MFH-Version mit Wohnungstypen

Diese Version der App ist für **Mehrfamilienhäuser** optimiert:

- Räume werden repräsentativ je **Wohnungstyp** (z. B. A/B/C) erfasst
- Für jeden Wohnungstyp wird eine **Anzahl identischer Wohneinheiten** angegeben
- Das Tool berechnet Heizlast:
  - je Raum
  - je Wohnungstyp (pro WE und für alle WE dieses Typs)
  - für das Gesamtgebäude

Zusätzlich:

- Heizflächentyp je Raum als Dropdown (5 Standardtypen)
- Automatische Vorschläge für Vorlauf-/Rücklauftemperatur je Typ
- Ampel-Logik für WP-Eignung je Raum (auf Basis der mittleren Systemtemperatur)
- Q³: Wärmepumpen-Abgleich bezogen auf das Gesamtgebäude
- Q³: Anteil der Gebäudeheizlast in nur bedingt/kritisch WP-geeigneten Bereichen (Option C)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Start

```bash
streamlit run app.py
```

Dann:

1. Wohnungstypen A/B/C anlegen
2. Räume je Wohnungstyp erfassen
3. Anzahl der jeweiligen Wohneinheiten setzen
4. Analyse-Level wählen (Q¹/Q²/Q³)
5. Ergebnisse als Excel oder Q-Konzept-PDF exportieren.
