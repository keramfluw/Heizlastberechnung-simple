# Heizlastberechnung Q¹ / Q² / Q³ – Streamlit-App

Dieses Tool berechnet die raumweise Heizlast auf Basis einer vereinfachten DIN EN 12831 Logik
und erweitert die Auswertung je nach Analyse-Level:

- **Q¹ – Basis Heizlast (DIN-ähnlich)**  
  - raumweise Heizlast (Transmission + Lüftung + Zuschlag)  
  - Gebäudetyp-Profile (Neubau / Bestand saniert / Altbau unsaniert)  
  - Export als Excel und PDF-Handout  

- **Q² – inkl. Heizflächentyp & Systemtemperaturen**  
  - zusätzlich Heizflächentyp je Raum  
  - Vorlauf- / Rücklauftemperatur je Raum  
  - Darstellung der mittleren Systemtemperaturen  

- **Q³ – inkl. Wärmepumpen-Abgleich**  
  - einfacher Abgleich der Heizlast mit einer geplanten Wärmepumpe  
  - Deckungsgrad bei Norm-Heizlast  
  - sehr grobe COP- / JAZ-Heuristik  
  - Strombedarfsschätzung der Wärmepumpe auf Basis eines jährlichen Heizwärmebedarfs  

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
- Für Q³ wird ein sehr einfacher Wärmepumpen-Abgleich zur Orientierung durchgeführt
  (Dimensionierung, Strombedarf, COP-/JAZ-Heuristik).
