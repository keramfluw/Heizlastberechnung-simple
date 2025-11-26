# Heizlastberechnung Q¹ / Q² / Q³ – MFH-Version mit Wohnungstypen (V5)

Diese Version der App ist für **Mehrfamilienhäuser** optimiert und präzisiert
den Begriff der oberen Begrenzungsfläche des Raumes:

- statt `A Dach` / `U Dach` nun:
  - `A oberer Abschluss (m²)`
  - `U oberer Abschluss (W/m²K)`
  - `Typ oberer Abschluss` (Dach gegen Außenluft / Decke gegen beheizten Raum / Decke gegen unbeheizten Raum)

Räume werden repräsentativ je **Wohnungstyp** (z. B. A/B/C) erfasst, und für
jeden Typ wird eine **Anzahl identischer Wohneinheiten** angegeben.

Das Tool berechnet:

- Heizlast je Raum
- Heizlast je Wohnungstyp (pro WE und für alle WE dieses Typs)
- Heizlast für das Gesamtgebäude

Zusätzlich:

- Heizflächentyp je Raum als Dropdown (5 Standardtypen)
- automatische Vorschläge für Vorlauf-/Rücklauftemperatur je Typ
- Ampel-Logik für WP-Eignung je Raum (auf Basis der mittleren Systemtemperatur)
- Q³: Wärmepumpen-Abgleich bezogen auf das Gesamtgebäude
- Q³: Anteil der Gebäudeheizlast in nur bedingt/kritisch WP-geeigneten Bereichen

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
3. `A oberer Abschluss` / `Typ oberer Abschluss` passend zur Lage wählen
4. Anzahl der jeweiligen Wohneinheiten setzen
5. Analyse-Level wählen (Q¹/Q²/Q³)
6. Ergebnisse als Excel oder Q-Konzept-PDF exportieren.
