import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ---------------------------------------------------------
# Heizflächentyp-Parameter (Dropdown-Logik)
# ---------------------------------------------------------
HEATING_TYPE_PARAMS = {
    "Fußbodenheizung": {"T_VL": 35.0, "T_RL": 28.0},
    "Wand-/Deckenheizung": {"T_VL": 38.0, "T_RL": 30.0},
    "Niedertemperatur-Heizkörper": {"T_VL": 45.0, "T_RL": 38.0},
    "Standard-Heizkörper": {"T_VL": 60.0, "T_RL": 50.0},
    "Altbau-Radiator": {"T_VL": 70.0, "T_RL": 60.0},
}

# ---------------------------------------------------------
# Hilfsfunktionen für Export
# ---------------------------------------------------------
def create_pdf_summary(result_df, type_summary_df, total_heating_load_building, T_out, default_T_set, safety_factor, analysis_level, wp_info=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ------------- Titelseite / Kopf -------------
    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "Heizlastberechnung – Ergebnisübersicht")

    y -= 1.0 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Analyse-Level: {analysis_level}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Norm-Außentemperatur: {T_out:.1f} °C")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Standard-Innentemperatur: {default_T_set:.1f} °C")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Sicherheitszuschlag: {safety_factor * 100:.0f} %")

    # ------------- Raumweise Heizlast (repräsentative Räume) -------------
    y -= 1.0 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Raumweise Heizlast (repräsentative Räume je Wohnungstyp)")
    y -= 0.7 * cm

    col_titles = ["Wohn-Typ", "Raum", "Fläche [m²]", "T_i [°C]", "Heizlast je Raum [W]"]
    col_x = [2 * cm, 5 * cm, 10 * cm, 13 * cm, 16 * cm]

    c.setFont("Helvetica-Bold", 9)
    for title, x in zip(col_titles, col_x):
        c.drawString(x, y, title)

    y -= 0.5 * cm
    c.setFont("Helvetica", 9)

    for _, row in result_df.iterrows():
        if y < 3 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica-Bold", 11)
            c.drawString(2 * cm, y, "Raumweise Heizlast (Fortsetzung)")
            y -= 0.7 * cm
            c.setFont("Helvetica-Bold", 9)
            for title, x in zip(col_titles, col_x):
                c.drawString(x, y, title)
            y -= 0.5 * cm
            c.setFont("Helvetica", 9)

        c.drawString(col_x[0], y, str(row.get("Wohnungstyp", "")))
        c.drawString(col_x[1], y, str(row["Raum"]))
        c.drawRightString(col_x[2] + 2.0 * cm, y, f'{row["Fläche (m²)"]:.1f}')
        c.drawRightString(col_x[3] + 1.5 * cm, y, f'{row["Tᵢ eff (°C)"]:.1f}')
        c.drawRightString(col_x[4] + 2.0 * cm, y, f'{row["Q_Raum (W)"]:.0f}')
        y -= 0.4 * cm

    # ------------- Heizlast je Wohnungstyp & Gebäude -------------
    if type_summary_df is not None and not type_summary_df.empty:
        if y < 4 * cm:
            c.showPage()
            y = height - 2 * cm
        y -= 0.5 * cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Heizlast je Wohnungstyp und für das Gesamtgebäude")
        y -= 0.7 * cm

        col_titles_type = ["Wohn-Typ", "Anzahl WE", "Heizlast je WE [kW]", "Heizlast Typ gesamt [kW]"]
        col_x_type = [2 * cm, 7 * cm, 11 * cm, 16 * cm]

        c.setFont("Helvetica-Bold", 9)
        for title, x in zip(col_titles_type, col_x_type):
            c.drawString(x, y, title)
        y -= 0.5 * cm
        c.setFont("Helvetica", 9)

        for _, row in type_summary_df.iterrows():
            if y < 3 * cm:
                c.showPage()
                y = height - 2 * cm
                c.setFont("Helvetica-Bold", 11)
                c.drawString(2 * cm, y, "Heizlast je Wohnungstyp (Fortsetzung)")
                y -= 0.7 * cm
                c.setFont("Helvetica-Bold", 9)
                for title, x in zip(col_titles_type, col_x_type):
                    c.drawString(x, y, title)
                y -= 0.5 * cm
                c.setFont("Helvetica", 9)

            c.drawString(col_x_type[0], y, str(row["Wohnungstyp"]))
            c.drawRightString(col_x_type[1] + 1.5 * cm, y, f'{row["Anzahl WE Typ"]:,.0f}')
            c.drawRightString(col_x_type[2] + 2.0 * cm, y, f'{row["Q_WE_kW"]:,.2f}')
            c.drawRightString(col_x_type[3] + 2.0 * cm, y, f'{row["Q_Typ_geb_kW"]:,.2f}')
            y -= 0.4 * cm

        if y < 3 * cm:
            c.showPage()
            y = height - 2 * cm

        y -= 0.5 * cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Gesamtheizlast Gebäude")
        y -= 0.7 * cm
        c.setFont("Helvetica", 10)
        c.drawString(
            2 * cm,
            y,
            f"Summe: {total_heating_load_building:,.0f} W (≈ {total_heating_load_building/1000:,.2f} kW)"
        )

    # ------------- Q²/Q³: Systemdaten je Raum -------------
    if analysis_level.startswith("Q²") or analysis_level.startswith("Q³"):
        c.showPage()
        y = height - 2 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Systemdaten je Raum (Q²/Q³)")

        y -= 0.8 * cm
        c.setFont("Helvetica", 9)
        c.drawString(2 * cm, y, "Heizflächentyp und Systemtemperaturen je Raum")
        y -= 0.6 * cm

        col_titles_sys = ["Wohn-Typ", "Raum", "Heizfläche", "T_VL [°C]", "T_RL [°C]", "T_mittel [°C]"]
        col_x_sys = [2 * cm, 5 * cm, 9 * cm, 13 * cm, 16 * cm, 19 * cm]

        c.setFont("Helvetica-Bold", 9)
        for title, x in zip(col_titles_sys, col_x_sys):
            c.drawString(x, y, title)
        y -= 0.5 * cm
        c.setFont("Helvetica", 9)

        for _, row in result_df.iterrows():
            if y < 3 * cm:
                c.showPage()
                y = height - 2 * cm
                c.setFont("Helvetica-Bold", 12)
                c.drawString(2 * cm, y, "Systemdaten je Raum (Fortsetzung)")
                y -= 0.8 * cm
                c.setFont("Helvetica-Bold", 9)
                for title, x in zip(col_titles_sys, col_x_sys):
                    c.drawString(x, y, title)
                y -= 0.5 * cm
                c.setFont("Helvetica", 9)

            hf = str(row.get("Heizflächentyp", ""))
            t_vl = row.get("T_VL (°C)", np.nan)
            t_rl = row.get("T_RL (°C)", np.nan)
            t_mid = row.get("T_mittel (°C)", np.nan)

            c.drawString(col_x_sys[0], y, str(row.get("Wohnungstyp", "")))
            c.drawString(col_x_sys[1], y, str(row["Raum"]))
            c.drawString(col_x_sys[2], y, hf)
            c.drawRightString(col_x_sys[3] + 1.2 * cm, y, f'{t_vl:.1f}' if not np.isnan(t_vl) else "-")
            c.drawRightString(col_x_sys[4] + 1.2 * cm, y, f'{t_rl:.1f}' if not np.isnan(t_rl) else "-")
            c.drawRightString(col_x_sys[5] + 1.2 * cm, y, f'{t_mid:.1f}' if not np.isnan(t_mid) else "-")
            y -= 0.4 * cm

    # ------------- Q³: Wärmepumpen-Abgleich & Empfehlung -------------
    if analysis_level.startswith("Q³") and wp_info is not None and wp_info.get("wp_typ") != "Kein WP / andere Erzeuger":
        c.showPage()
        y = height - 2 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Wärmepumpen-Abgleich (Q³) – Gesamtgebäude")

        y -= 0.8 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Wärmepumpen-Typ: {wp_info.get('wp_typ')}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Nennleistung WP: {wp_info.get('wp_power_kw', 0):,.1f} kW")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Deckungsgrad bei Norm-Heizlast (Gebäude): {wp_info.get('coverage', 0):,.0f} %")
        y -= 0.5 * cm

        weighted_avg_T = wp_info.get("weighted_avg_T")
        if weighted_avg_T is not None and not np.isnan(weighted_avg_T):
            c.drawString(2 * cm, y, f"gewichtete mittlere Systemtemperatur: {weighted_avg_T:,.1f} °C")
            y -= 0.5 * cm

        cop_est = wp_info.get("cop_est")
        jaz_est = wp_info.get("jaz_est")
        heizwaermebedarf = wp_info.get("heizwaermebedarf")
        strombedarf = wp_info.get("strombedarf")
        critical_share = wp_info.get("critical_share")

        if cop_est is not None and not np.isnan(cop_est):
            c.drawString(2 * cm, y, f"geschätzter COP am Auslegungspunkt: {cop_est:,.2f}")
            y -= 0.5 * cm
        if jaz_est is not None and not np.isnan(jaz_est):
            c.drawString(2 * cm, y, f"grobe JAZ-Schätzung: {jaz_est:,.2f}")
            y -= 0.5 * cm
        if heizwaermebedarf is not None and heizwaermebedarf > 0 and strombedarf is not None and not np.isnan(strombedarf):
            c.drawString(2 * cm, y, f"jährlicher Heizwärmebedarf: {heizwaermebedarf:,.0f} kWh/a")
            y -= 0.5 * cm
            c.drawString(2 * cm, y, f"resultierender Strombedarf WP (geschätzt): {strombedarf:,.0f} kWh/a")
            y -= 0.7 * cm
        if critical_share is not None:
            c.drawString(2 * cm, y, f"Anteil Heizlast in kritisch/bedingt geeigneten Bereichen (Gebäude): {critical_share:,.0f} %")
            y -= 0.7 * cm

        # Q-Konzept-Empfehlung (Ampellogik)
        y -= 0.3 * cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Q-Konzept – Empfehlung")

        y -= 0.7 * cm
        c.setFont("Helvetica", 10)

        coverage = wp_info.get("coverage", 0)
        text_lines = []

        if coverage < 90:
            text_lines.append(
                "Die Wärmepumpe ist für die Gesamtgebäudeheizlast tendenziell unterdimensioniert (< 90 % Deckung). "
                "Ein bivalenter Betrieb oder eine höhere Nennleistung sollte geprüft werden."
            )
        elif 90 <= coverage <= 120:
            text_lines.append(
                "Die Wärmepumpe liegt im üblichen Auslegungsbereich (ca. 90–120 % der Gebäude-Norm-Heizlast)."
            )
        else:
            text_lines.append(
                "Die Wärmepumpe ist für das Gebäude tendenziell überdimensioniert (> 120 % Deckung). "
                "Dies kann zu Takten und ineffizientem Betrieb führen."
            )

        if weighted_avg_T is not None and not np.isnan(weighted_avg_T):
            if weighted_avg_T <= 35:
                text_lines.append(
                    "Die mittlere Systemtemperatur ≤ 35 °C deutet auf eine sehr gute Eignung für den Wärmepumpenbetrieb hin "
                    "(typisch Fußbodenheizung / große Heizflächen)."
                )
            elif 35 < weighted_avg_T <= 45:
                text_lines.append(
                    "Die mittlere Systemtemperatur zwischen 35–45 °C ist gut für einen effizienten Wärmepumpenbetrieb geeignet."
                )
            elif 45 < weighted_avg_T <= 50:
                text_lines.append(
                    "Die mittlere Systemtemperatur von 45–50 °C ist nur bedingt optimal. "
                    "Eine Optimierung der Heizflächen, des hydraulischen Abgleichs oder der Heizkurve sollte geprüft werden."
                )
            else:
                text_lines.append(
                    "Die mittlere Systemtemperatur > 50 °C ist kritisch für einen effizienten Wärmepumpenbetrieb. "
                    "Empfohlen werden Maßnahmen wie Heizkörpertausch in Teilbereichen, Reduktion der Vorlauftemperatur "
                    "und ein detaillierter hydraulischer Abgleich."
                )

        if critical_share is not None:
            if critical_share > 0:
                text_lines.append(
                    f"Der Anteil der Gebäudeheizlast in nur bedingt oder kritisch für Wärmepumpen geeigneten Bereichen liegt bei "
                    f"rund {critical_share:,.0f} %. "
                    "Für eine voll WP-optimierte Anlage sollte in diesen Bereichen eine Anpassung der Heizflächen "
                    "(z. B. größere Heizkörper, Flächenheizsysteme) oder eine Reduktion der Systemtemperatur geprüft werden."
                )
            else:
                text_lines.append(
                    "Nahezu die gesamte Gebäudeheizlast liegt in gut oder sehr gut für Wärmepumpen geeigneten Bereichen. "
                    "Die Anlage ist damit grundsätzlich sehr gut WP-fähig."
                )

        text_lines.append(
            "Im Rahmen eines Q³-Konzeptes empfiehlt sich auf Basis dieser Bewertung eine vertiefte technische Analyse "
            "inklusive hydraulischem Abgleich, Optimierung der Heizflächen und – falls erforderlich – Anpassung des "
            "Wärmeerzeugerkonzeptes (z. B. bivalente Systeme, Pufferspeicher, Kombination mit PV und Speichern)."
        )

        for line in text_lines:
            wrapped = []
            words = line.split(" ")
            current = ""
            for w in words:
                test_line = current + (" " if current else "") + w
                if c.stringWidth(test_line, "Helvetica", 10) < (width - 4 * cm):
                    current = test_line
                else:
                    wrapped.append(current)
                    current = w
            if current:
                wrapped.append(current)

            for wl in wrapped:
                if y < 3 * cm:
                    c.showPage()
                    y = height - 2 * cm
                    c.setFont("Helvetica", 10)
                c.drawString(2 * cm, y, wl)
                y -= 0.5 * cm

    c.showPage()
    c.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


def create_excel(result_df, type_summary_df=None):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        result_df.to_excel(writer, sheet_name="Räume", index=False)
        if type_summary_df is not None and not type_summary_df.empty:
            type_summary_df.to_excel(writer, sheet_name="Wohnungstypen", index=False)
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------
# Grundkonfiguration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Heizlastberechnung – Qrauts Tool",
    layout="wide"
)

st.title("🔧 Heizlastberechnung (Q¹ / Q² / Q³) – by Marek Wulff")

st.markdown(
    """
Dieses Tool berechnet die **raumweise Heizlast** und ist nun für **Mehrfamilienhäuser** optimiert:

- Räume werden repräsentativ je **Wohnungstyp** (A/B/C/…) erfasst  
- Für jeden Wohnungstyp wird die **Anzahl identischer Wohneinheiten** angegeben  
- Das Tool berechnet Heizlast:
  - je Raum  
  - je Wohnungstyp (pro WE und für alle WE dieses Typs)  
  - für das **Gesamtgebäude**  

Q²/Q³ ergänzen Heizflächentyp, Systemtemperatur und Wärmepumpen-Abgleich.
"""
)

# ---------------------------------------------------------
# Analyse-Level Q¹ / Q² / Q³
# ---------------------------------------------------------
analysis_level = st.radio(
    "Analyse-Level wählen:",
    options=[
        "Q¹ – Basis Heizlast (DIN-ähnlich)",
        "Q² – inkl. Heizflächentyp & Systemtemperaturen",
        "Q³ – inkl. Wärmepumpen-Abgleich"
    ],
    horizontal=False
)

st.markdown(
    """
- **Q¹**: Heizlast je Raum, je Wohnungstyp, Gebäude gesamt  
- **Q²**: zusätzlich Heizflächentyp & Vor-/Rücklauftemperatur je Raum  
- **Q³**: zusätzlich Wärmepumpen-Auslegung, COP/JAZ-Schätzung & Q-Konzept-Empfehlung
"""
)

# ---------------------------------------------------------
# Globale Parameter
# ---------------------------------------------------------
st.sidebar.header("Globale Parameter")

T_out = st.sidebar.number_input(
    "Norm-Außentemperatur Tₑ (°C)",
    min_value=-30.0,
    max_value=10.0,
    value=-12.0,
    step=0.5
)

default_T_set = st.sidebar.number_input(
    "Standard-Innentemperatur Tᵢ (°C)",
    min_value=15.0,
    max_value=26.0,
    value=20.0,
    step=0.5
)

safety_factor = st.sidebar.number_input(
    "Sicherheitszuschlag (%)",
    min_value=0.0,
    max_value=50.0,
    value=10.0,
    step=1.0
) / 100.0

# Gebäudetyp-Profile mit typischen U-Werten
building_profiles = {
    "Neubau (Effizienzhaus)": {
        "U_wand": 0.20,
        "U_dach": 0.14,
        "U_boden": 0.25,
        "U_fenster": 0.90,
    },
    "Bestand saniert": {
        "U_wand": 0.35,
        "U_dach": 0.25,
        "U_boden": 0.40,
        "U_fenster": 1.30,
    },
    "Altbau unsaniert": {
        "U_wand": 1.20,
        "U_dach": 0.80,
        "U_boden": 0.80,
        "U_fenster": 2.70,
    },
}

selected_profile = st.sidebar.selectbox(
    "Gebäudetyp / U-Wert-Profil",
    options=list(building_profiles.keys()),
    index=1
)

profile = building_profiles[selected_profile]

st.sidebar.markdown(
    f"""
**Typische U-Werte ({selected_profile}):**

- Wand: **{profile["U_wand"]:.2f} W/m²K**  
- Dach: **{profile["U_dach"]:.2f} W/m²K**  
- Boden: **{profile["U_boden"]:.2f} W/m²K**  
- Fenster: **{profile["U_fenster"]:.2f} W/m²K**  
"""
)

# Button: U-Werte aus Profil in Tabelle schreiben
if st.sidebar.button("Standard-U-Werte auf Tabelle anwenden"):
    if "raumtabelle" in st.session_state:
        df_tmp = st.session_state["raumtabelle"].copy()
        for col, key in [
            ("U Wand (W/m²K)", "U_wand"),
            ("U Dach (W/m²K)", "U_dach"),
            ("U Boden (W/m²K)", "U_boden"),
            ("U Fenster (W/m²K)", "U_fenster"),
        ]:
            if col in df_tmp.columns:
                df_tmp[col] = profile[key]
        st.session_state["raumtabelle"] = df_tmp
        st.sidebar.success("Standard-U-Werte wurden angewendet.")
    else:
        st.sidebar.warning("Bitte zuerst die Raumtabelle laden bzw. verwenden.")

st.sidebar.markdown(
    """
**Hinweis:**  
- Jeder Datensatz in der Tabelle repräsentiert einen **Raum** einer typischen Wohnung.  
- Räume mit identischem *Wohnungstyp* werden zu einer Wohnung zusammengefasst.  
- Über **„Anzahl WE Typ“** skalierst du den Wohnungstyp auf das Gesamtgebäude.
"""
)

# ---------------------------------------------------------
# Eingabe-Tabelle für Räume
# ---------------------------------------------------------
st.subheader("Raumdaten je Wohnungstyp eingeben")

st.markdown(
    """
Typischer Workflow:

1. Wohnungstyp **A** definieren (z. B. Standardgeschosswohnung)  
2. Alle Räume dieses Typs unter „Wohnungstyp = A“ erfassen  
3. In mindestens einer Zeile für Typ A die **Anzahl WE Typ** setzen (z. B. 6 Stück)  
4. Optional Wohnungstyp **B** (z. B. Staffelgeschoss) etc. ergänzen  

Das Tool fasst alle Räume je Wohnungstyp zusammen und rechnet auf Gebäudeebene hoch.
"""
)

building_default = building_profiles["Bestand saniert"]

default_data = pd.DataFrame(
    [
        {
            "Wohnungstyp": "A",
            "Anzahl WE Typ": 6,
            "Raum": "Wohnen/Essen",
            "Fläche (m²)": 25.0,
            "Raumhöhe (m)": 2.6,
            "Tᵢ (°C)": 21.0,
            "A Wand (m²)": 18.0,
            "U Wand (W/m²K)": building_default["U_wand"],
            "A Dach (m²)": 0.0,
            "U Dach (W/m²K)": building_default["U_dach"],
            "A Boden (m²)": 25.0,
            "U Boden (W/m²K)": building_default["U_boden"],
            "A Fenster (m²)": 5.0,
            "U Fenster (W/m²K)": building_default["U_fenster"],
            "Luftwechsel n (1/h)": 0.7,
            "Heizflächentyp": "Standard-Heizkörper",
            "T_VL (°C)": np.nan,
            "T_RL (°C)": np.nan,
        },
        {
            "Wohnungstyp": "A",
            "Anzahl WE Typ": 6,
            "Raum": "Schlafen",
            "Fläche (m²)": 14.0,
            "Raumhöhe (m)": 2.6,
            "Tᵢ (°C)": 18.0,
            "A Wand (m²)": 12.0,
            "U Wand (W/m²K)": building_default["U_wand"],
            "A Dach (m²)": 0.0,
            "U Dach (W/m²K)": building_default["U_dach"],
            "A Boden (m²)": 14.0,
            "U Boden (W/m²K)": building_default["U_boden"],
            "A Fenster (m²)": 3.0,
            "U Fenster (W/m²K)": building_default["U_fenster"],
            "Luftwechsel n (1/h)": 0.7,
            "Heizflächentyp": "Standard-Heizkörper",
            "T_VL (°C)": np.nan,
            "T_RL (°C)": np.nan,
        },
        {
            "Wohnungstyp": "B",
            "Anzahl WE Typ": 2,
            "Raum": "Wohnen/Essen (Staffel)",
            "Fläche (m²)": 30.0,
            "Raumhöhe (m)": 2.6,
            "Tᵢ (°C)": 21.0,
            "A Wand (m²)": 22.0,
            "U Wand (W/m²K)": building_default["U_wand"],
            "A Dach (m²)": 10.0,
            "U Dach (W/m²K)": building_default["U_dach"],
            "A Boden (m²)": 30.0,
            "U Boden (W/m²K)": building_default["U_boden"],
            "A Fenster (m²)": 6.0,
            "U Fenster (W/m²K)": building_default["U_fenster"],
            "Luftwechsel n (1/h)": 0.7,
            "Heizflächentyp": "Standard-Heizkörper",
            "T_VL (°C)": np.nan,
            "T_RL (°C)": np.nan,
        },
    ]
)

data = st.data_editor(
    default_data,
    num_rows="dynamic",
    use_container_width=True,
    key="raumtabelle",
    column_config={
        "Heizflächentyp": st.column_config.SelectboxColumn(
            "Heizflächentyp",
            options=list(HEATING_TYPE_PARAMS.keys()),
            required=True,
        ),
        "Wohnungstyp": st.column_config.TextColumn(
            "Wohnungstyp (z. B. A/B/C)",
        ),
    }
)

# ---------------------------------------------------------
# Wärmepumpen-Parameter (für Q³ relevant, aber immer editierbar)
# ---------------------------------------------------------
st.subheader("Wärmepumpen-Parameter (für Q³ relevant, bezogen auf Gesamtgebäude)")

col_wp1, col_wp2, col_wp3 = st.columns(3)
with col_wp1:
    wp_typ = st.selectbox(
        "Wärmepumpen-Typ",
        options=["Luft/Wasser", "Sole/Wasser", "Kein WP / andere Erzeuger"],
        index=0
    )
with col_wp2:
    wp_power_kw_input = st.number_input(
        "Nennleistung Wärmepumpe bei Auslegungspunkt (kW)",
        min_value=1.0,
        max_value=500.0,
        value=40.0,
        step=1.0
    )
with col_wp3:
    heizwaermebedarf_input = st.number_input(
        "geschätzter jährlicher Heizwärmebedarf Gebäude (kWh/a)",
        min_value=0.0,
        max_value=5_000_000.0,
        value=120000.0,
        step=5000.0
    )

# ---------------------------------------------------------
# Berechnung
# ---------------------------------------------------------
def berechne_heizlast(df, T_out, default_T_set, safety_factor):
    df = df.copy()

    # Heizflächentyp → automatische T_VL/T_RL, falls leer/NaN
    if "Heizflächentyp" in df.columns:
        for idx, row in df.iterrows():
            h_type = row.get("Heizflächentyp")
            if h_type in HEATING_TYPE_PARAMS:
                params = HEATING_TYPE_PARAMS[h_type]
                if np.isnan(row.get("T_VL (°C)", np.nan)):
                    df.at[idx, "T_VL (°C)"] = params["T_VL"]
                if np.isnan(row.get("T_RL (°C)", np.nan)):
                    df.at[idx, "T_RL (°C)"] = params["T_RL"]

    # fehlende Temperaturen mit Standard belegen
    df["Tᵢ eff (°C)"] = df["Tᵢ (°C)"].fillna(default_T_set)

    # Volumen
    df["Volumen (m³)"] = df["Fläche (m²)"] * df["Raumhöhe (m)"]

    # Temperaturdifferenz
    df["ΔT (K)"] = df["Tᵢ eff (°C)"] - T_out

    # UA-Werte je Bauteil
    df["UA Wand (W/K)"] = df["A Wand (m²)"] * df["U Wand (W/m²K)"]
    df["UA Dach (W/K)"] = df["A Dach (m²)"] * df["U Dach (W/m²K)"]
    df["UA Boden (W/K)"] = df["A Boden (m²)"] * df["U Boden (W/m²K)"]
    df["UA Fenster (W/K)"] = df["A Fenster (m²)"] * df["U Fenster (W/m²K)"]

    df["UA gesamt (W/K)"] = (
        df["UA Wand (W/K)"]
        + df["UA Dach (W/K)"]
        + df["UA Boden (W/K)"]
        + df["UA Fenster (W/K)"]
    )

    # Transmissionsverluste
    df["Q_T (W)"] = df["UA gesamt (W/K)"] * df["ΔT (K)"]

    # Lüftungsverluste
    df["Q_V (W)"] = 0.33 * df["Luftwechsel n (1/h)"] * df["Volumen (m³)"] * df["ΔT (K)"]

    # Heizlast ohne / mit Zuschlag je Raum (repräsentative Wohnung)
    df["Q_ohne Zuschlag (W)"] = df["Q_T (W)"] + df["Q_V (W)"]
    df["Q_Raum (W)"] = df["Q_ohne Zuschlag (W)"] * (1.0 + safety_factor)

    # mittlere Systemtemperatur je Raum
    if "T_VL (°C)" in df.columns and "T_RL (°C)" in df.columns:
        df["T_mittel (°C)"] = (df["T_VL (°C)"] + df["T_RL (°C)"]) / 2.0
    else:
        df["T_mittel (°C)"] = np.nan

    # Ampel-Einstufung je Raum (WP-Eignung)
    def classify_eignung(t_mid):
        if np.isnan(t_mid):
            return "unbekannt"
        if t_mid <= 35:
            return "sehr gut"
        elif t_mid <= 45:
            return "gut"
        elif t_mid <= 50:
            return "bedingt"
        else:
            return "kritisch"

    df["WP-Eignung"] = df["T_mittel (°C)"].apply(classify_eignung)

    # Falls Anzahl WE Typ fehlt, auf 1 setzen
    if "Anzahl WE Typ" not in df.columns:
        df["Anzahl WE Typ"] = 1
    df["Anzahl WE Typ"] = df["Anzahl WE Typ"].fillna(1)

    return df


def schaetze_cop(wp_typ, T_mittel_system):
    if T_mittel_system is None or np.isnan(T_mittel_system):
        return np.nan

    if wp_typ == "Luft/Wasser":
        cop_ref = 3.2
    elif wp_typ == "Sole/Wasser":
        cop_ref = 4.0
    else:
        return np.nan

    delta_T = T_mittel_system - 35.0
    cop = cop_ref - 0.15 * (delta_T / 5.0)
    cop = max(2.0, min(cop, cop_ref + 0.6))
    return cop


if st.button("🔍 Heizlast berechnen"):
    try:
        result = berechne_heizlast(data, T_out, default_T_set, safety_factor)

        # Heizlast je Wohnungstyp (repräsentative Wohnung)
        if "Wohnungstyp" in result.columns:
            type_group = result.groupby("Wohnungstyp", dropna=True).agg(
                Q_WE_W=("Q_Raum (W)", "sum"),
                Anzahl_WE=("Anzahl WE Typ", "max"),
            ).reset_index()
        else:
            # Fallback: alles als Typ "A"
            result["Wohnungstyp"] = "A"
            type_group = result.groupby("Wohnungstyp").agg(
                Q_WE_W=("Q_Raum (W)", "sum"),
                Anzahl_WE=("Anzahl WE Typ", "max"),
            ).reset_index()

        type_group["Q_WE_kW"] = type_group["Q_WE_W"] / 1000.0
        type_group["Q_Typ_geb_W"] = type_group["Q_WE_W"] * type_group["Anzahl_WE"]
        type_group["Q_Typ_geb_kW"] = type_group["Q_Typ_geb_W"] / 1000.0

        # Gebäudeheizlast
        total_heating_load_building = type_group["Q_Typ_geb_W"].sum()
        heizlast_kw_building = total_heating_load_building / 1000.0 if total_heating_load_building > 0 else 0.0

        # gewichtete Systemtemperatur für das Gebäude
        if "T_mittel (°C)" in result.columns:
            # gewichtete nach Gebäudeanteil: Q_Raum * Anzahl_WE
            result["Q_Raum_geb (W)"] = result["Q_Raum (W)"] * result["Anzahl WE Typ"]
            mask = result["T_mittel (°C)"].notna() & (result["Q_Raum_geb (W)"] > 0)
            if mask.any():
                weighted_avg_T = (
                    (result.loc[mask, "T_mittel (°C)"] * result.loc[mask, "Q_Raum_geb (W)"]).sum()
                    / result.loc[mask, "Q_Raum_geb (W)"].sum()
                )
            else:
                weighted_avg_T = np.nan
        else:
            weighted_avg_T = np.nan

        # Anteil kritischer/bedingt geeigneter Heizlast (Gebäude)
        if "Q_Raum_geb (W)" not in result.columns:
            result["Q_Raum_geb (W)"] = result["Q_Raum (W)"] * result["Anzahl WE Typ"]

        total_Q_building = result["Q_Raum_geb (W)"].sum()
        crit_mask = result["WP-Eignung"].isin(["bedingt", "kritisch"])
        if crit_mask.any() and total_Q_building > 0:
            critical_share = (result.loc[crit_mask, "Q_Raum_geb (W)"].sum() / total_Q_building) * 100.0
        else:
            critical_share = 0.0

        # WP-Info vorbereiten (nur bei Q³ wirklich relevant, bezogen auf Gebäude)
        wp_info = None
        coverage = None
        cop_est = None
        jaz_est = None
        heizwaermebedarf = heizwaermebedarf_input
        strombedarf = None

        if analysis_level.startswith("Q³") and heizlast_kw_building > 0 and wp_typ != "Kein WP / andere Erzeuger":
            coverage = (wp_power_kw_input / heizlast_kw_building) * 100.0
            cop_est = schaetze_cop(wp_typ, weighted_avg_T)
            jaz_est = cop_est - 0.3 if not np.isnan(cop_est) else np.nan
            if jaz_est is not None and not np.isnan(jaz_est) and jaz_est > 0 and heizwaermebedarf_input > 0:
                strombedarf = heizwaermebedarf_input / jaz_est
            wp_info = {
                "wp_typ": wp_typ,
                "wp_power_kw": wp_power_kw_input,
                "coverage": coverage,
                "cop_est": cop_est,
                "jaz_est": jaz_est,
                "heizwaermebedarf": heizwaermebedarf_input,
                "strombedarf": strombedarf,
                "weighted_avg_T": weighted_avg_T,
                "critical_share": critical_share,
            }

        cols = st.columns((2, 3))
        with cols[0]:
            st.subheader("Ergebnisse je Raum (repräsentative Wohnungen)")

            anzeige = result[[
                "Wohnungstyp",
                "Anzahl WE Typ",
                "Raum",
                "Fläche (m²)",
                "Tᵢ eff (°C)",
                "ΔT (K)",
                "Q_T (W)",
                "Q_V (W)",
                "Q_Raum (W)",
                "Heizflächentyp",
                "T_VL (°C)",
                "T_RL (°C)",
                "T_mittel (°C)",
                "WP-Eignung",
            ]].copy()

            for c in ["ΔT (K)", "Q_T (W)", "Q_V (W)", "Q_Raum (W)", "T_VL (°C)", "T_RL (°C)", "T_mittel (°C)"]:
                anzeige[c] = anzeige[c].round(1)

            st.dataframe(anzeige, use_container_width=True)

            st.markdown(
                f"### 🔢 Gesamtheizlast Gebäude: **{total_heating_load_building:,.0f} W** "
                f"(≈ {heizlast_kw_building:,.2f} kW)"
            )
            st.markdown(
                f"🔍 Anteil Gebäudeheizlast in nur **bedingt/kritisch WP-geeigneten Bereichen**: "
                f"**{critical_share:,.0f} %**"
            )

            st.subheader("Heizlast je Wohnungstyp")
            type_display = type_group[["Wohnungstyp", "Anzahl_WE", "Q_WE_kW", "Q_Typ_geb_kW"]].copy()
            type_display.columns = ["Wohnungstyp", "Anzahl WE Typ", "Heizlast je WE [kW]", "Heizlast Typ gesamt [kW]"]
            st.dataframe(type_display, use_container_width=True)

            # Exporte
            excel_bytes = create_excel(result, type_group.rename(columns={
                "Q_WE_W": "Heizlast je WE [W]",
                "Q_WE_kW": "Heizlast je WE [kW]",
                "Q_Typ_geb_W": "Heizlast Typ gesamt [W]",
                "Q_Typ_geb_kW": "Heizlast Typ gesamt [kW]",
                "Anzahl_WE": "Anzahl WE Typ",
            }))
            st.download_button(
                label="📥 Ergebnisse als Excel (.xlsx)",
                data=excel_bytes,
                file_name="heizlast_mfh_ergebnisse.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            pdf_bytes = create_pdf_summary(
                result, type_group.rename(columns={
                    "Wohnungstyp": "Wohnungstyp",
                    "Anzahl_WE": "Anzahl WE Typ",
                    "Q_WE_kW": "Q_WE_kW",
                    "Q_Typ_geb_kW": "Q_Typ_geb_kW",
                }), total_heating_load_building, T_out, default_T_set, safety_factor, analysis_level, wp_info
            )
            st.download_button(
                label="📄 Ergebnisse als PDF-Handout (Q-Level & MFH)",
                data=pdf_bytes,
                file_name="heizlast_mfh_handout_qkonzept.pdf",
                mime="application/pdf",
            )

        with cols[1]:
            st.subheader("Visualisierung Heizlast je Wohnungstyp [kW]")
            plot_type = type_group[["Wohnungstyp", "Q_Typ_geb_kW"]].copy()
            plot_type = plot_type.set_index("Wohnungstyp")
            st.bar_chart(plot_type)

            if analysis_level.startswith("Q²") or analysis_level.startswith("Q³"):
                st.markdown("#### Mittlere Systemtemperatur je Wohnungstyp (gewichteter Mittelwert)")
                # Approx: mittlere Systemtemperatur je Typ durch Heizlastgewichtung auf Raumebene
                if "T_mittel (°C)" in result.columns:
                    temp_type = result.copy()
                    temp_type["Q_Raum_geb (W)"] = temp_type["Q_Raum (W)"] * temp_type["Anzahl WE Typ"]
                    temp_group = temp_type[temp_type["T_mittel (°C)"].notna()].groupby("Wohnungstyp").apply(
                        lambda g: (g["T_mittel (°C)"] * g["Q_Raum_geb (W)"]).sum() / g["Q_Raum_geb (W)"].sum()
                    )
                    temp_group = temp_group.to_frame(name="T_mittel_typ (°C)")
                    st.bar_chart(temp_group)

        with st.expander("Details / Zwischenwerte (Räume)"):
            st.dataframe(result, use_container_width=True)

        with st.expander("Details Wohnungstypen / Gebäude"):
            st.dataframe(type_group, use_container_width=True)

        # Wärmepumpen-Auswertung in Q³
        if analysis_level.startswith("Q³") and wp_info is not None:
            st.subheader("Wärmepumpen-Abgleich (Q³) – Gesamtgebäude")

            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric("Deckungsgrad Gebäude bei Normlast", f"{coverage:,.0f} %")
            with col_res2:
                if cop_est is not None and not np.isnan(cop_est):
                    st.metric("geschätzter COP am Auslegungspunkt", f"{cop_est:,.2f}")
                else:
                    st.metric("geschätzter COP am Auslegungspunkt", "n/a")
            with col_res3:
                if jaz_est is not None and not np.isnan(jaz_est):
                    st.metric("grobe JAZ-Schätzung", f"{jaz_est:,.2f}")
                else:
                    st.metric("grobe JAZ-Schätzung", "n/a")

            st.markdown(
                f"🔍 Anteil Gebäudeheizlast in nur **bedingt/kritisch WP-geeigneten Bereichen**: "
                f"**{critical_share:,.0f} %**"
            )

            if jaz_est is not None and not np.isnan(jaz_est) and heizwaermebedarf_input > 0:
                strombedarf = heizwaermebedarf_input / jaz_est
                st.markdown("### Grobe Strombedarfsschätzung")
                st.write(
                    f"- Heizwärmebedarf Gebäude: **{heizwaermebedarf_input:,.0f} kWh/a**  \n"
                    f"- Daraus resultierender **Strombedarf WP** (auf Basis JAZ-Schätzung): "
                    f"**{strombedarf:,.0f} kWh/a**"
                )

    except Exception as e:
        st.error(f"Fehler bei der Berechnung: {e}")
else:
    st.info("Bitte auf **„Heizlast berechnen“** klicken, nachdem du die Raumdaten je Wohnungstyp geprüft hast.")
