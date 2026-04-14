import streamlit as st
import pandas as pd
import os

# ======================
# Page config
# ======================
st.set_page_config(page_title="PMO Leitstand", layout="wide")

# ======================
# Branding (Sagemcom Farben & Logos)
# ======================
SAGEMCOM_TURQUOISE = "#00B2A9"
SAGEMCOM_BLUE = "#0077C8"

st.markdown(f"""
<style>
.stApp {{
    background: linear-gradient(180deg, {SAGEMCOM_TURQUOISE}22 0%, #ffffff 40%);
}}
</style>
""", unsafe_allow_html=True)

# Logos (optional)
logo_col1, logo_col2 = st.columns([1, 1])
with logo_col1:
    if os.path.exists("lackmann.png"):
        st.image("lackmann.png", height=60)
with logo_col2:
    if os.path.exists("sagemcom.png"):
        st.image("sagemcom.png", height=60)

st.title("PMO Projekt-Leitstand")

# ======================
# Excel laden
# ======================
EXCEL_FILENAME = "PMO_Leitstand_Zielstruktur_Template.xlsx"

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    goals = pd.read_excel(xls, "Goals")
    persons = pd.read_excel(xls, "Persons")
    partners = pd.read_excel(xls, "Partners")
    return goals, persons, partners

excel_file = EXCEL_FILENAME if os.path.exists(EXCEL_FILENAME) else st.file_uploader("Excel-Datei hochladen", type=["xlsx"])
if excel_file is None:
    st.stop()

goals, persons, partners = load_data(excel_file)

# ======================
# Statusberechnung (FIX inkl. Datentyp)
# ======================
def calculate_status(df):
    df = df.copy()

    # <<< WICHTIGER FIX >>>
    df["Calculated_Status"] = df["Calculated_Status"].astype("object")

    # Ebene 4 = manueller Status
    df.loc[df["Goal_Level"] == 4, "Calculated_Status"] = df["Manual_Status"]

    # Bottom-Up Berechnung
    for level in [3, 2, 1]:
        for goal_id in df[df["Goal_Level"] == level]["Goal_ID"]:
            children = df[df["Parent_Goal_ID"] == goal_id]
            if children.empty:
                continue
            statuses = children["Calculated_Status"].dropna()
            if all(statuses == "Done"):
                status = "Done"
            elif any(statuses.isin(["At Risk", "Not Started"])):
                status = "At Risk"
            else:
                status = "On Track"
            df.loc[df["Goal_ID"] == goal_id, "Calculated_Status"] = status
    return df

goals = calculate_status(goals)

# ======================
# Ampellogik
# ======================
def ampel(status):
    if status in ["Done", "On Track"]:
        return "🟢"
    if status == "At Risk":
        return "🔴"
    return "🟡"

# ======================
# Sidebar
# ======================
levels = {1: "Ebene 1", 2: "Ebene 2", 3: "Ebene 3", 4: "Ebene 4"}
selected_levels = [lvl for lvl in levels if st.sidebar.checkbox(levels[lvl], lvl == 1)]

filtered = goals[goals["Goal_Level"].isin(selected_levels)]

# ======================
# Anzeige je Ebene + Ampel
# ======================
for lvl in selected_levels:
    df_lvl = filtered[filtered["Goal_Level"] == lvl]
    if df_lvl.empty:
        continue

    overall_status = (
        "At Risk" if any(df_lvl["Calculated_Status"] == "At Risk") else
        "On Track" if any(df_lvl["Calculated_Status"] == "On Track") else
        "Done"
    )

    st.subheader(f"{levels[lvl]} {ampel(overall_status)}")

    st.dataframe(
        df_lvl[[
            "Goal_ID",
            "Goal_Name",
            "Calculated_Status",
            "Planned_Start_Date",
            "Planned_End_Date",
        ]],
        use_container_width=True,
    )
