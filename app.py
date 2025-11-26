import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ---------------------------------------------------------
# Hilfsfunktionen für Export
# ---------------------------------------------------------
def create_pdf_summary(df, total_heating_load, T_out, default_T_set, safety_factor, analysis_level):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

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

    y -= 1.0 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Raumweise Heizlast")
    y -= 0.7 * cm

    # Tabellenkopf
    c.setFont("Helvetica-Bold", 9)
    col_titles = ["Raum", "Fläche [m²]", "T_i [°C]", "Heizlast [W]"]
    col_x = [2 * cm, 8 * cm, 12 * cm, 16 * cm]
    for title, x in zip(col_titles, col_x):
        c.drawString(x, y, title)

    y -= 0.5 * cm
    c.setFont("Helvetica", 9)

    # Zeilen
    for _, row in df.iterrows():
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

        c.drawString(col_x[0], y, str(row["Raum"]))
        c.drawRightString(col_x[1] + 2.0 * cm, y, f'{row["Fläche (m²)"]:.1f}')
        c.drawRightString(col_x[2] + 1.5 * cm, y, f'{row["Tᵢ eff (°C)"]:.1f}')
        c.drawRightString(col_x[3] + 2.0 * cm, y, f'{row["Q_Raum (W)"]:.0f}')
        y -= 0.4 * cm

    # Gesamtheizlast
    if y < 3 * cm:
        c.showPage()
        y = height - 2 * cm

    y -= 0.5 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Gesamtheizlast")
    y -= 0.7 * cm
    c.setFont("Helvetica", 10)
    c.drawString(
        2 * cm,
        y,
        f"Summe: {total_heating_load:,.0f} W (≈ {total_heating_load/1000:,.2f} kW)"
    )

    c.showPage()
    c.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


def create_excel(result_df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        result_df.to_excel(writer, sheet_name="Heizlast", index=False)
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------
# Grundkonfiguration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Heizlastberechnung – Qrauts Tool",
    layout="wide"
)

st.title("🔧 Heizlastberechnung (Q¹ / Q² / Q³)")

st.markdown(
    """
Dieses Tool berechnet die **raumweise Heizlast** auf Basis einer vereinfachten 
DIN-EN-12831-Logik und erweitert dies – je nach Analyse-Level – um einen
einfachen **Heizsystem- und Wärmepumpen-Abgleich**.

- Transmission: \\( Q_T = UA_{gesamt} · ΔT \\)  
- Lüftung: \\( Q_V = 0{,}33 · n · V · ΔT \\)  
- Heizlast Raum: \\( (Q_T + Q_V) · (1 + Sicherheitszuschlag) \\)

Alle Leistungen werden in **Watt** ausgegeben.
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
- **Q¹**: raumweise Heizlast, Gebäudetyp-Profil, Export (Excel/PDF)  
- **Q²**: zusätzlich Heizflächentyp & Vor-/Rücklauftemperatur je Raum  
- **Q³**: zusätzlich einfacher Wärmepumpen-Leistungsabgleich (Über-/Unterdeckung, COP-Schätzung)
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
Du kannst pro Raum eine abweichende Innentemperatur angeben. 
Falls das Feld leer ist, wird der Standardwert verwendet.
"""
)

# ---------------------------------------------------------
# Eingabe-Tabelle für Räume
# ---------------------------------------------------------
st.subheader("Raumdaten eingeben")

st.markdown(
    """
Für jeden Raum bitte angeben:

- **Raum**: Bezeichnung  
- **Fläche (m²)** und **Raumhöhe (m)**: zur Volumenberechnung  
- **Tᵢ (°C)**: gewünschte Raumtemperatur (optional, sonst Standard)  
- **A Wand/Dach/Boden (m²)** und zugehörige **U-Werte (W/m²K)**  
- **A Fenster (m²)** / **U Fenster (W/m²K)**  
- **Luftwechsel n (1/h)**: z. B. 0,4 Neubau, 0,7 saniert, 1,0 Altbau  
- (Q²/Q³) **Heizflächentyp**, **Vorlauf- / Rücklauftemperatur**
"""
)

building_default = building_profiles["Bestand saniert"]

default_data = pd.DataFrame(
    [
        {
            "Raum": "Wohnzimmer",
            "Fläche (m²)": 25.0,
            "Raumhöhe (m)": 2.5,
            "Tᵢ (°C)": np.nan,  # nutzt dann Standard
            "A Wand (m²)": 20.0,
            "U Wand (W/m²K)": building_default["U_wand"],
            "A Dach (m²)": 10.0,
            "U Dach (W/m²K)": building_default["U_dach"],
            "A Boden (m²)": 25.0,
            "U Boden (W/m²K)": building_default["U_boden"],
            "A Fenster (m²)": 5.0,
            "U Fenster (W/m²K)": building_default["U_fenster"],
            "Luftwechsel n (1/h)": 0.7,
            "Heizflächentyp": "Heizkörper",
            "T_VL (°C)": 45.0,
            "T_RL (°C)": 35.0,
        },
        {
            "Raum": "Schlafzimmer",
            "Fläche (m²)": 15.0,
            "Raumhöhe (m)": 2.5,
            "Tᵢ (°C)": 18.0,
            "A Wand (m²)": 15.0,
            "U Wand (W/m²K)": building_default["U_wand"],
            "A Dach (m²)": 8.0,
            "U Dach (W/m²K)": building_default["U_dach"],
            "A Boden (m²)": 15.0,
            "U Boden (W/m²K)": building_default["U_boden"],
            "A Fenster (m²)": 3.0,
            "U Fenster (W/m²K)": building_default["U_fenster"],
            "Luftwechsel n (1/h)": 0.7,
            "Heizflächentyp": "Heizkörper",
            "T_VL (°C)": 45.0,
            "T_RL (°C)": 35.0,
        },
    ]
)

data = st.data_editor(
    default_data,
    num_rows="dynamic",
    use_container_width=True,
    key="raumtabelle"
)

# ---------------------------------------------------------
# Berechnung
# ---------------------------------------------------------
def berechne_heizlast(df, T_out, default_T_set, safety_factor):
    df = df.copy()

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

    # Heizlast ohne / mit Zuschlag
    df["Q_ohne Zuschlag (W)"] = df["Q_T (W)"] + df["Q_V (W)"]
    df["Q_Raum (W)"] = df["Q_ohne Zuschlag (W)"] * (1.0 + safety_factor)

    # mittlere Systemtemperatur je Raum (falls angegeben)
    if "T_VL (°C)" in df.columns and "T_RL (°C)" in df.columns:
        df["T_mittel (°C)"] = (df["T_VL (°C)"] + df["T_RL (°C)"]) / 2.0
    else:
        df["T_mittel (°C)"] = np.nan

    return df


def schaetze_cop(wp_typ, T_mittel_system):
    """
    Sehr einfache COP-Heuristik:
    - Referenz: 35 °C Systemtemperatur
      Luft/Wasser: COP ~ 3.2
      Sole/Wasser: COP ~ 4.0
    - Pro 5 K höher: -0.15 COP
    - Pro 5 K niedriger: +0.15 COP
    """
    if np.isnan(T_mittel_system):
        return np.nan

    if wp_typ == "Luft/Wasser":
        cop_ref = 3.2
    elif wp_typ == "Sole/Wasser":
        cop_ref = 4.0
    else:
        return np.nan

    delta_T = T_mittel_system - 35.0
    cop = cop_ref - 0.15 * (delta_T / 5.0)
    cop = max(2.0, min(cop, cop_ref + 0.6))  # grobe Klammer
    return cop


if st.button("🔍 Heizlast berechnen"):
    try:
        result = berechne_heizlast(data, T_out, default_T_set, safety_factor)

        cols = st.columns((2, 3))
        with cols[0]:
            st.subheader("Ergebnisse je Raum")

            anzeige = result[[
                "Raum",
                "Fläche (m²)",
                "Tᵢ eff (°C)",
                "ΔT (K)",
                "Q_T (W)",
                "Q_V (W)",
                "Q_Raum (W)"
            ]].copy()

            # etwas runden
            for c in ["ΔT (K)", "Q_T (W)", "Q_V (W)", "Q_Raum (W)"]:
                anzeige[c] = anzeige[c].round(1)

            st.dataframe(anzeige, use_container_width=True)

            total_heating_load = result["Q_Raum (W)"].sum()
            st.markdown(
                f"### 🔢 Gesamtheizlast: **{total_heating_load:,.0f} W** "
                f"(≈ {total_heating_load/1000:,.2f} kW)"
            )

            # Exporte
            excel_bytes = create_excel(result)
            st.download_button(
                label="📥 Ergebnisse als Excel (.xlsx)",
                data=excel_bytes,
                file_name="heizlast_ergebnisse.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            pdf_bytes = create_pdf_summary(
                anzeige, total_heating_load, T_out, default_T_set, safety_factor, analysis_level
            )
            st.download_button(
                label="📄 Ergebnisse als PDF-Handout",
                data=pdf_bytes,
                file_name="heizlast_handout.pdf",
                mime="application/pdf",
            )

        with cols[1]:
            st.subheader("Visualisierung Heizlast je Raum (W)")
            plot_df = result[["Raum", "Q_Raum (W)"]].copy()
            plot_df = plot_df.set_index("Raum")

            st.bar_chart(plot_df)

            if analysis_level in ["Q² – inkl. Heizflächentyp & Systemtemperaturen", "Q³ – inkl. Wärmepumpen-Abgleich"]:
                st.markdown("#### Mittlere Systemtemperatur je Raum")
                if "T_mittel (°C)" in result.columns:
                    temp_df = result[["Raum", "T_mittel (°C)"]].copy()
                    temp_df = temp_df.set_index("Raum")
                    st.bar_chart(temp_df)

        with st.expander("Details / Zwischenwerte"):
            st.dataframe(result, use_container_width=True)

        # -------------------------------------------------
        # Wärmepumpen-Abgleich (Q³)
        # -------------------------------------------------
        if analysis_level == "Q³ – inkl. Wärmepumpen-Abgleich":
            st.subheader("Wärmepumpen-Abgleich (Q³)")

            heizlast_kw = total_heating_load / 1000.0 if total_heating_load > 0 else 0.0

            # gewichtet nach Heizlast mittlere Systemtemperatur bestimmen
            if "T_mittel (°C)" in result.columns:
                mask = result["T_mittel (°C)"].notna() & (result["Q_Raum (W)"] > 0)
                if mask.any():
                    weighted_avg_T = (
                        (result.loc[mask, "T_mittel (°C)"] * result.loc[mask, "Q_Raum (W)"]).sum()
                        / result.loc[mask, "Q_Raum (W)"].sum()
                    )
                else:
                    weighted_avg_T = np.nan
            else:
                weighted_avg_T = np.nan

            col_wp1, col_wp2 = st.columns(2)
            with col_wp1:
                st.markdown("**Heizsystem-Übersicht**")
                st.write(f"Berechnete Gesamtheizlast: **{heizlast_kw:,.2f} kW**")
                if not np.isnan(weighted_avg_T):
                    st.write(f"Gewichtete mittlere Systemtemperatur: **{weighted_avg_T:,.1f} °C**")
                else:
                    st.write("Gewichtete mittlere Systemtemperatur: nicht verfügbar (bitte T_VL/T_RL prüfen).")

            with col_wp2:
                st.markdown("**Wärmepumpen-Parameter**")
                wp_typ = st.selectbox(
                    "Wärmepumpen-Typ",
                    options=["Luft/Wasser", "Sole/Wasser", "Kein WP / andere Erzeuger"],
                    index=0
                )

                default_wp_power = max(3.0, round(heizlast_kw * 1.1, 1)) if heizlast_kw > 0 else 8.0

                wp_power_kw = st.number_input(
                    "Nennleistung Wärmepumpe bei Auslegungspunkt (kW)",
                    min_value=1.0,
                    max_value=500.0,
                    value=default_wp_power,
                    step=0.5
                )

                heizwaermebedarf = st.number_input(
                    "geschätzter jährlicher Heizwärmebedarf (kWh/a)",
                    min_value=0.0,
                    max_value=1_000_000.0,
                    value=float(round(heizlast_kw * 1800, 0)) if heizlast_kw > 0 else 20000.0,
                    step=1000.0
                )

            if wp_typ != "Kein WP / andere Erzeuger" and heizlast_kw > 0:
                coverage = (wp_power_kw / heizlast_kw) * 100.0
                cop_est = schaetze_cop(wp_typ, weighted_avg_T) if not np.isnan(weighted_avg_T) else np.nan
                jaz_est = cop_est - 0.3 if not np.isnan(cop_est) else np.nan
                jaz_est = max(1.0, jaz_est) if not np.isnan(jaz_est) else np.nan

                st.markdown("---")
                st.markdown("### Bewertung Wärmepumpen-Auslegung")

                col_res1, col_res2, col_res3 = st.columns(3)
                with col_res1:
                    st.metric("Deckungsgrad bei Normlast", f"{coverage:,.0f} %")
                with col_res2:
                    if not np.isnan(cop_est):
                        st.metric("geschätzter COP am Auslegungspunkt", f"{cop_est:,.2f}")
                    else:
                        st.metric("geschätzter COP am Auslegungspunkt", "n/a")
                with col_res3:
                    if not np.isnan(jaz_est):
                        st.metric("grobe JAZ-Schätzung", f"{jaz_est:,.2f}")
                    else:
                        st.metric("grobe JAZ-Schätzung", "n/a")

                # Einordnung Deckungsgrad
                if coverage < 90:
                    st.warning(
                        "Die Wärmepumpe ist **tendenziell unterdimensioniert** "
                        "(< 90 % Deckung der Norm-Heizlast). Ein bivalenter Betrieb "
                        "oder eine höhere Leistung sollte geprüft werden."
                    )
                elif 90 <= coverage <= 120:
                    st.success(
                        "Die Wärmepumpe liegt im **üblichen Auslegungsbereich** "
                        "(ca. 90–120 % der Norm-Heizlast)."
                    )
                else:
                    st.info(
                        "Die Wärmepumpe ist **tendenziell überdimensioniert** "
                        "(> 120 % der Norm-Heizlast). Das kann zu Takten und "
                        "ineffizientem Betrieb führen."
                    )

                if not np.isnan(cop_est) and heizwaermebedarf > 0:
                    strombedarf = heizwaermebedarf / jaz_est if jaz_est > 0 else np.nan

                    st.markdown("### Grobe Strombedarfsschätzung")
                    st.write(
                        f"- Heizwärmebedarf: **{heizwaermebedarf:,.0f} kWh/a**  \n"
                        f"- Daraus resultierender **Strombedarf WP** (auf Basis JAZ-Schätzung): "
                        f"**{strombedarf:,.0f} kWh/a**"
                    )

            elif wp_typ == "Kein WP / andere Erzeuger":
                st.info("Wärmepumpen-Abgleich übersprungen (Typ: Kein WP / andere Erzeuger).")

    except Exception as e:
        st.error(f"Fehler bei der Berechnung: {e}")
else:
    st.info("Bitte auf **„Heizlast berechnen“** klicken, nachdem du die Raumdaten geprüft hast.")
