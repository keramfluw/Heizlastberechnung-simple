# Heizlastberechnung Q¹ / Q² / Q³ – Streamlit-App (Dropdown + Ampel + Option C)

Diese Version enthält:

- Heizflächentyp je Raum als Dropdown (5 Standardtypen)
- Automatische Vorschläge für Vorlauf-/Rücklauftemperatur je Typ
- Ampel-Logik für WP-Eignung je Raum auf Basis der mittleren Systemtemperatur
- Q³: Wärmepumpen-Abgleich (Deckungsgrad, COP, JAZ, Strombedarf)
- Q³: Anteil der Heizlast in nur bedingt/kritisch WP-geeigneten Bereichen (Option C),
  als Hinweis, welcher Anteil der Heizflächen optimiert werden sollte, um auf
  eine voll WP-taugliche Anlage zu kommen.

Installation:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Start:

```bash
streamlit run app.py
```

Dann Analyse-Level wählen, Räume erfassen und das Handout als PDF/Excel exportieren.
