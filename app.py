import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# =====================
# Page config & Branding
# =====================
st.set_page_config(page_title="PMO Leitstand", layout="wide")
SAGEMCOM_TURQUOISE = "#00B2A9"

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
        st.image("lackmann.png", height=50)
with logo_col2:
    if os.path.exists("sagemcom.png"):
        st.image("sagemcom.png", height=50)

st.title("PMO Projekt-Leitstand")

# =====================
# Excel laden
# =====================
EXCEL_FILENAME = "PMO_Leitstand_Zielstruktur_Template.xlsx"

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    return (
        pd.read_excel(xls, "Goals"),
        pd.read_excel(xls, "Persons"),
        pd.read_excel(xls, "Partners"),
    )

excel = EXCEL_FILENAME if os.path.exists(EXCEL_FILENAME) else st.file_uploader("Excel hochladen", type=["xlsx"])
if excel is None:
    st.stop()

goals, persons, partners = load_data(excel)

# =====================
# Statusberechnung
# =====================
def calculate_status(df):
    df = df.copy()
    df["Calculated_Status"] = df["Calculated_Status"].astype("object")
    df.loc[df.Goal_Level == 4, "Calculated_Status"] = df.Manual_Status

    for lvl in [3, 2, 1]:
        for gid in df[df.Goal_Level == lvl].Goal_ID:
            children = df[df.Parent_Goal_ID == gid]
            if children.empty:
                continue
            s = children.Calculated_Status.dropna()
            if all(s == "Done"):
                r = "Done"
            elif any(s.isin(["At Risk", "Not Started"])):
                r = "At Risk"
            else:
                r = "On Track"
            df.loc[df.Goal_ID == gid, "Calculated_Status"] = r
    return df

goals = calculate_status(goals)

# =====================
# Helper
# =====================
def ampel(status):
    if status in ["Done", "On Track"]:
        return "🟢"
    if status == "At Risk":
        return "🔴"
    return "🟡"

# =====================
# Tabs
# =====================
tab1, tab2 = st.tabs(["📊 Leitstand", "🔥 Risiko-Heatmap (Partner)"])

# =====================
# TAB 1 – Leitstand
# =====================
with tab1:
    levels = {1: "Ebene 1", 2: "Ebene 2", 3: "Ebene 3", 4: "Ebene 4"}
    selected = [lvl for lvl in levels if st.checkbox(levels[lvl], lvl == 1)]

    view = goals[goals.Goal_Level.isin(selected)]

    for lvl in selected:
        df_lvl = view[view.Goal_Level == lvl]
        if df_lvl.empty:
            continue
        overall = (
            "At Risk" if any(df_lvl.Calculated_Status == "At Risk") else
            "On Track" if any(df_lvl.Calculated_Status == "On Track") else
            "Done"
        )
        st.subheader(f"{levels[lvl]} {ampel(overall)}")
        st.dataframe(
            df_lvl[["Goal_ID", "Goal_Name", "Calculated_Status", "Planned_End_Date"]],
            width="stretch",
        )

# =====================
# TAB 2 – Heatmap
# =====================
with tab2:
    st.subheader("Risiko-Heatmap der Partnerziele")

    partner_goals = goals[goals.Partner_Involved == True]
    partner_goals = partner_goals.merge(partners, on="Partner_ID", how="left")

    heatmap_data = pd.crosstab(
        partner_goals["Criticality"],
        partner_goals["Calculated_Status"],
    )

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.imshow(heatmap_data, cmap=plt.cm.Reds)

    ax.set_xticks(range(len(heatmap_data.columns)))
    ax.set_xticklabels(heatmap_data.columns)
    ax.set_yticks(range(len(heatmap_data.index)))
    ax.set_yticklabels(heatmap_data.index)

    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            ax.text(j, i, heatmap_data.iloc[i, j], ha="center", va="center")

    ax.set_xlabel("Status")
    ax.set_ylabel("Partner-Kritikalität")
    ax.set_title("Partner-Risiken (Heatmap)")

    st.pyplot(fig)

    st.markdown("""
    **Interpretation:**
    - Rechts / oben = hohes Risiko
    - Fokus für Lenkungskreis- und Eskalationsentscheidungen
    """)
