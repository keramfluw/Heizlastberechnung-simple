# Heizlastberechnung Q¹ / Q² / Q³ – Streamlit-App (Q-Konzept integriert)

Dieses Tool berechnet die raumweise Heizlast auf Basis einer vereinfachten DIN EN 12831 Logik
und bildet deine Qrauts Q-Level systematisch ab:

- **Q¹ – Basis Heizlast (DIN-ähnlich)**  
  - raumweise Heizlast (Transmission + Lüftung + Zuschlag)  
  - Gebäudetyp-Profile (Neubau / Bestand saniert / Altbau unsaniert)  
  - Export als Excel und **PDF-Handout (Q¹)**  

- **Q² – inkl. Heizflächentyp & Systemtemperaturen**  
  - zusätzlich Heizflächentyp je Raum  
  - Vorlauf- / Rücklauftemperatur je Raum  
  - mittlere Systemtemperatur je Raum  
  - PDF-Handout enthält zusätzlich eine Seite "Systemdaten je Raum"  

- **Q³ – inkl. Wärmepumpen-Abgleich & Q-Konzept**  
  - einfacher Abgleich der Heizlast mit einer geplanten Wärmepumpe  
  - Deckungsgrad bei Norm-Heizlast  
  - sehr grobe COP- / JAZ-Heuristik  
  - Strombedarfsschätzung der Wärmepumpe auf Basis eines jährlichen Heizwärmebedarfs  
  - PDF-Handout enthält zusätzlich:
    - Wärmepumpen-Abgleich
    - Deckungsgrad, COP, JAZ, Strombedarf
    - Textliche Q-Konzept-Empfehlung (Ampellogik nach Systemtemperatur & Deckungsgrad)

## Installation

Python-Umgebung erstellen (optional, aber empfohlen):

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Start der App

```bash
streamlit run app.py
```

Danach öffnet sich der Browser (oder unter http://localhost:8501).

## Hinweise

- Es handelt sich **nicht** um eine vollständige DIN EN 12831 Berechnung, sondern um ein
  pragmatisches Planungs- und Abschätzungstool.
- U-Werte-Profil kann im Sidebar gewählt und per Button auf die Raumtabelle übernommen werden.
- Für Q² und Q³ werden mittlere Systemtemperaturen aus Vor-/Rücklauf je Raum berechnet.
- Für Q³ wird ein Wärmepumpen-Abgleich zur Orientierung durchgeführt
  (Dimensionierung, Strombedarf, COP-/JAZ-Heuristik), und die Ergebnisse
  werden inkl. Q-Konzept-Empfehlung im PDF-Handout ausgegeben.
