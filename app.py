import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# ======================
# Page config & Branding
# ======================
st.set_page_config(page_title="PMO Leitstand – Heatmap", layout="wide")
SAGEMCOM_TURQUOISE = "#00B2A9"

st.markdown(f"""
<style>
.stApp {{
    background: linear-gradient(180deg, {SAGEMCOM_TURQUOISE}22 0%, #ffffff 40%);
}}
</style>
""", unsafe_allow_html=True)

# Logos (optional)
col1, col2 = st.columns([1, 1])
with col1:
    if os.path.exists("lackmann.png"):
        st.image("lackmann.png", height=50)
with col2:
    if os.path.exists("sagemcom.png"):
        st.image("sagemcom.png", height=50)

st.title("PMO Projekt-Leitstand – Risiko-Heatmap")

# ======================
# Excel laden
# ======================
EXCEL_FILENAME = "PMO_Leitstand_Zielstruktur_Template.xlsx"

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    goals = pd.read_excel(xls, "Goals")
    partners = pd.read_excel(xls, "Partners")
    return goals, partners

excel = EXCEL_FILENAME if os.path.exists(EXCEL_FILENAME) else st.file_uploader("Excel hochladen", type=["xlsx"])
if excel is None:
    st.stop()

goals, partners = load_data(excel)

# ======================
# Status & Kritikalität vorbereiten
# ======================
goals = goals.copy()
goals["Calculated_Status"] = goals["Calculated_Status"].astype("object")
goals.loc[goals.Goal_Level == 4, "Calculated_Status"] = goals.Manual_Status

# Nur Partnerziele
partner_goals = goals[goals.Partner_Involved == True]
partner_goals = partner_goals.merge(partners, on="Partner_ID", how="left")

status_map = {"Done": 0, "On Track": 1, "Not Started": 2, "At Risk": 3}
crit_map = {"low": 1, "medium": 2, "high": 3}

partner_goals["Status_Score"] = partner_goals["Calculated_Status"].map(status_map)
partner_goals["Criticality_Score"] = partner_goals["Criticality"].map(crit_map)

partner_goals = partner_goals.dropna(subset=["Status_Score", "Criticality_Score"])

# ======================
# Heatmap erzeugen
# ======================
fig, ax = plt.subplots(figsize=(6, 4))

heatmap_data = pd.crosstab(
    partner_goals["Criticality"],
    partner_goals["Calculated_Status"]
)

colors = plt.cm.Reds
ax.imshow(heatmap_data, cmap=colors)

ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns)
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index)

for i in range(len(heatmap_data.index)):
    for j in range(len(heatmap_data.columns)):
        ax.text(j, i, heatmap_data.iloc[i, j],
                ha="center", va="center", color="black")

ax.set_title("Risiko-Heatmap Partnerziele")
ax.set_xlabel("Status")
ax.set_ylabel("Partner-Kritikalität")

st.pyplot(fig)

st.markdown("""
**Interpretation:**  
- Rechts / oben = hohes Risiko  
- Besonders relevant für Lenkungskreis-Entscheidungen
""")
