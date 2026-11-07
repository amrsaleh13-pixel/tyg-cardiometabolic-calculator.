
import math
import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TyG & Cardiometabolic Risk Calculator",
    page_icon="🧬",
    layout="wide"
)


# Responsive layout: desktop, tablet and mobile (Android/iOS)
st.markdown("""
<style>
/* Main page width and spacing */
.block-container {
    max-width: 1180px;
    padding-top: 1.2rem;
    padding-bottom: 2.5rem;
    padding-left: clamp(0.8rem, 3vw, 2.5rem);
    padding-right: clamp(0.8rem, 3vw, 2.5rem);
}
h1 { letter-spacing: -0.025em; }
[data-testid="stMetric"] {
    background: rgba(128,128,128,0.07);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 14px;
    padding: 12px 14px;
}
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button {
    min-height: 46px;
    border-radius: 11px;
    font-weight: 600;
}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] [data-baseweb="select"] {
    min-height: 44px;
    border-radius: 9px;
}
div[data-testid="stTabs"] button {
    white-space: nowrap;
    min-height: 44px;
    padding-left: 12px;
    padding-right: 12px;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    width: 100%;
}
.small-note {
    font-size: 0.86rem;
    opacity: 0.82;
}
@media (max-width: 768px) {
    .block-container {
        padding-top: 0.65rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-bottom: 1.5rem !important;
    }
    h1 { font-size: 1.65rem !important; line-height: 1.2 !important; }
    h2 { font-size: 1.35rem !important; }
    h3 { font-size: 1.12rem !important; }
    p, label, .stMarkdown { font-size: 0.94rem; }
    [data-testid="stMetric"] {
        padding: 10px;
        border-radius: 12px;
    }
    [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
    div[data-testid="stTabs"] div[role="tablist"] {
        gap: 0.15rem;
        overflow-x: auto;
        flex-wrap: nowrap;
        scrollbar-width: thin;
    }
    div[data-testid="stTabs"] button {
        flex: 0 0 auto;
        font-size: 0.82rem;
        padding: 0.45rem 0.65rem;
    }
    [data-testid="stDataFrame"] {
        overflow-x: auto;
    }
    div[data-testid="stForm"] {
        padding: 0.65rem !important;
    }
    div[data-testid="stAlert"] {
        padding: 0.75rem !important;
    }
    [data-testid="stSidebar"] { min-width: 0; }
}
@media (max-width: 480px) {
    h1 { font-size: 1.42rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.18rem !important; }
    div[data-testid="stTabs"] button { font-size: 0.76rem; }
}
</style>
""", unsafe_allow_html=True)


# Thesis-derived ROC cutoffs (Table 13 / Results section)
# These are cohort-derived screening thresholds, not universal diagnostic criteria.
THESIS = {
    "Metabolic syndrome": {
        "TyG Index": {"cutoff": 8.565, "auc": 0.774, "ci": "0.722–0.826", "sensitivity": 78.5, "specificity": 51.0, "p": "<0.001"},
        "TyG-BMI": {"cutoff": 241.14, "auc": 0.937, "ci": "0.911–0.964", "sensitivity": 98.5, "specificity": 94.0, "p": "<0.001"},
        "TyG-WHR": {"cutoff": 7.970, "auc": 0.748, "ci": "0.693–0.803", "sensitivity": 44.5, "specificity": 100.0, "p": "<0.001"},
        "HOMA-IR": {"cutoff": 1.950, "auc": 0.903, "ci": "0.868–0.938", "sensitivity": 81.0, "specificity": 99.0, "p": "<0.001"},
    },
    "Insulin resistance": {
        "TyG Index": {"cutoff": 8.565, "auc": 0.823, "ci": "0.774–0.873", "sensitivity": 84.0, "specificity": 50.4, "p": "<0.001"},
        "TyG-BMI": {"cutoff": 234.47, "auc": 0.853, "ci": "0.808–0.898", "sensitivity": 93.3, "specificity": 54.7, "p": "<0.001"},
        "TyG-WHR": {"cutoff": 7.970, "auc": 0.820, "ci": "0.773–0.867", "sensitivity": 54.0, "specificity": 99.3, "p": "<0.001"},
        "HOMA-IR": {"cutoff": 1.900, "auc": None, "sensitivity": None, "specificity": None},
    },
    "Cardiovascular Disease": {
        "TyG Index": {"cutoff": 8.585, "auc": 0.793, "ci": "0.704–0.881", "sensitivity": 96.2, "specificity": 34.3, "p": "<0.001"},
        "TyG-BMI": {"cutoff": 266.18, "auc": 0.672, "ci": "0.560–0.785", "sensitivity": 80.8, "specificity": 52.7, "p": "0.005"},
        "TyG-WHR": {"cutoff": 7.330, "auc": 0.690, "ci": "0.588–0.791", "sensitivity": 88.5, "specificity": 46.2, "p": "0.002"},
        "HOMA-IR": {"cutoff": None, "auc": None, "sensitivity": None, "specificity": None},
    }
}

def calculate_indices(tg, fpg, bmi, whr, insulin):
    tyg = math.log((tg * fpg) / 2)
    tyg_bmi = tyg * bmi
    tyg_whr = tyg * whr
    homa = (insulin * fpg) / 405
    return {
        "TyG Index": tyg,
        "TyG-BMI": tyg_bmi,
        "TyG-WHR": tyg_whr,
        "HOMA-IR": homa
    }

def flag(value, cutoff):
    if cutoff is None:
        return None
    return value >= cutoff

def status_text(value, cutoff, positive_label="Above thesis cut-off", negative_label="Below thesis cut-off"):
    if cutoff is None:
        return "Not assessed"
    return positive_label if value >= cutoff else negative_label

def make_results(indices, prevent_risk=None):
    rows = []
    for outcome, markers in THESIS.items():
        for marker, stats in markers.items():
            cutoff = stats["cutoff"]
            if cutoff is None:
                continue
            value = indices[marker]
            rows.append({
                "Outcome assessed": outcome,
                "Index": marker,
                "Patient value": round(value, 3),
                "Thesis cut-off": cutoff,
                "Screen positive": "Yes" if value >= cutoff else "No",
                "AUC": stats["auc"],
                "Sensitivity (%)": stats["sensitivity"],
                "Specificity (%)": stats["specificity"]
            })
    if prevent_risk is not None:
        rows.append({
            "Outcome assessed": "PREVENT 10-year risk (entered score)",
            "Index": "PREVENT 10-year risk",
            "Patient value": round(prevent_risk, 2),
            "Thesis cut-off": 7.5,
            "Screen positive": "Yes" if prevent_risk >= 7.5 else "No",
            "AUC": None,
            "Sensitivity (%)": None,
            "Specificity (%)": None
        })
    return pd.DataFrame(rows)

st.title("🧬 TyG & Cardiometabolic Risk Calculator")
st.caption("Mobile-ready clinical research calculator | TyG Index • TyG-BMI • TyG-WHR • HOMA-IR")

st.warning(
    "For research support and screening only. Thesis-derived ROC thresholds are cohort-specific "
    "and must not be treated as universally validated diagnostic criteria or as a substitute "
    "for clinical assessment."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Single patient calculator", "Batch calculation", "Thesis cut-offs",
    "PREVENT risk", "Formulas & notes"
])

with tab1:
    st.subheader("Patient data")
    c1, c2, c3 = st.columns(3)
    with c1:
        patient_id = st.text_input("Patient ID (optional)")
        tg_unit = st.selectbox("Triglycerides unit", ["mg/dL", "mmol/L"])
        tg_input = st.number_input("Fasting triglycerides", min_value=0.01, value=150.0, step=1.0)
        glucose_unit = st.selectbox("Fasting glucose unit", ["mg/dL", "mmol/L"])
        glucose_input = st.number_input("Fasting plasma glucose", min_value=0.01, value=100.0, step=1.0)
    with c2:
        weight = st.number_input("Weight (kg)", min_value=1.0, value=80.0, step=0.5)
        height_cm = st.number_input("Height (cm)", min_value=50.0, value=170.0, step=0.5)
        waist_cm = st.number_input("Waist circumference (cm)", min_value=1.0, value=95.0, step=0.5)
        hip_cm = st.number_input("Hip circumference (cm)", min_value=1.0, value=105.0, step=0.5)
    with c3:
        insulin = st.number_input("Fasting insulin (µIU/mL)", min_value=0.0, value=10.0, step=0.1)
        prevent = st.number_input(
            "PREVENT 10-year CVD risk (%) — enter calculated score",
            min_value=0.0, max_value=100.0, value=5.0, step=0.1
        )
        st.caption("PREVENT score is entered manually; this app does not calculate the PREVENT equation.")

    calculate = st.button("Calculate indices", type="primary", use_container_width=True)

    if calculate:
        if min(tg_input, glucose_input, weight, height_cm, waist_cm, hip_cm) <= 0:
            st.error("Please enter positive values for all required measurements.")
        else:
            tg_mg = tg_input if tg_unit == "mg/dL" else tg_input * 88.57
            fpg_mg = glucose_input if glucose_unit == "mg/dL" else glucose_input * 18.0182
            height_m = height_cm / 100
            bmi = weight / (height_m ** 2)
            whr = waist_cm / hip_cm

            indices = calculate_indices(tg_mg, fpg_mg, bmi, whr, insulin)

            st.divider()
            st.subheader("Calculated indices")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TyG Index", f'{indices["TyG Index"]:.3f}')
            m2.metric("TyG-BMI", f'{indices["TyG-BMI"]:.2f}')
            m3.metric("TyG-WHR", f'{indices["TyG-WHR"]:.3f}')
            m4.metric("HOMA-IR", f'{indices["HOMA-IR"]:.3f}')

            st.subheader("Anthropometric calculations")
            st.write(
                f"**BMI:** {bmi:.2f} kg/m²  |  **WHR:** {whr:.3f}  |  "
                f"**Converted TG:** {tg_mg:.1f} mg/dL  |  **Converted FPG:** {fpg_mg:.1f} mg/dL"
            )

            st.subheader("Interpretation using thesis ROC cut-offs")
            result_df = make_results(indices, prevent)
            for outcome in THESIS:
                st.markdown(f"**{outcome}**")
                subset = result_df[result_df["Outcome assessed"] == outcome]
                st.dataframe(subset, hide_index=True, use_container_width=True)

            if prevent >= 7.5:
                st.info("Entered PREVENT risk is ≥7.5% (the high-risk outcome definition used in the thesis ROC analysis).")
            else:
                st.success("Entered PREVENT risk is <7.5% (below the high-risk outcome definition used in the thesis ROC analysis).")

            st.caption(
                "A screen-positive TyG-derived index means the value is at or above the thesis ROC cut-off. "
                "It does not independently establish a diagnosis."
            )

            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Download patient results (CSV)",
                data=csv,
                file_name=f"TyG_results_{patient_id or 'patient'}.csv",
                mime="text/csv"
            )

with tab2:
    st.subheader("Batch calculation from Excel or CSV")
    st.write(
        "Upload a file containing these columns: TG, FPG, Weight_kg, Height_m, "
        "Waist_cm, Hip_cm, Insulin, and optionally PREVENT_10yr. "
        "TG and FPG must be in mg/dL."
    )
    uploaded = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
    if uploaded is not None:
        try:
            raw = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
            required = ["TG", "FPG", "Weight_kg", "Height_m", "Waist_cm", "Hip_cm", "Insulin"]
            missing = [c for c in required if c not in raw.columns]
            if missing:
                st.error("Missing columns: " + ", ".join(missing))
            else:
                for col in required + (["PREVENT_10yr"] if "PREVENT_10yr" in raw.columns else []):
                    raw[col] = pd.to_numeric(raw[col], errors="coerce")
                raw["BMI_calculated"] = raw["Weight_kg"] / (raw["Height_m"] ** 2)
                raw["WHR_calculated"] = raw["Waist_cm"] / raw["Hip_cm"]
                raw["TyG_index_calculated"] = (raw["TG"] * raw["FPG"] / 2).apply(
                    lambda x: math.log(x) if pd.notna(x) and x > 0 else float("nan")
                )
                raw["TyG_BMI_calculated"] = raw["TyG_index_calculated"] * raw["BMI_calculated"]
                raw["TyG_WHR_calculated"] = raw["TyG_index_calculated"] * raw["WHR_calculated"]
                raw["HOMA_IR_calculated"] = raw["Insulin"] * raw["FPG"] / 405

                raw["IR_by_HOMA_ge_1.9"] = raw["HOMA_IR_calculated"] >= 1.9
                raw["IR_screen_by_TyG_ge_8.565"] = raw["TyG_index_calculated"] >= 8.565
                raw["IR_screen_by_TyG_BMI_ge_234.47"] = raw["TyG_BMI_calculated"] >= 234.47
                raw["IR_screen_by_TyG_WHR_ge_7.970"] = raw["TyG_WHR_calculated"] >= 7.970
                raw["MetS_screen_by_TyG_BMI_ge_241.14"] = raw["TyG_BMI_calculated"] >= 241.14
                raw["High_CVD_risk_screen_by_TyG_ge_8.585"] = raw["TyG_index_calculated"] >= 8.585
                raw["High_CVD_risk_screen_by_TyG_BMI_ge_266.18"] = raw["TyG_BMI_calculated"] >= 266.18
                raw["High_CVD_risk_screen_by_TyG_WHR_ge_7.330"] = raw["TyG_WHR_calculated"] >= 7.330
                if "PREVENT_10yr" in raw.columns:
                    raw["PREVENT_ge_7.5_percent"] = raw["PREVENT_10yr"] >= 7.5

                st.success(f"Calculated indices for {len(raw)} rows.")
                st.dataframe(raw.head(100), use_container_width=True)
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as writer:
                    raw.to_excel(writer, index=False, sheet_name="Calculated_Indices")
                st.download_button(
                    "Download completed Excel file",
                    data=out.getvalue(),
                    file_name="TyG_Batch_Calculated.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Could not process file: {e}")

with tab3:
    st.subheader("ROC cut-offs reported in your thesis")
    st.caption("Values transcribed from the thesis Results, Table 13. Thresholds are cohort-derived.")
    for outcome, markers in THESIS.items():
        st.markdown(f"**{outcome}**")
        table = []
        for marker, x in markers.items():
            if x["cutoff"] is not None:
                table.append({
                    "Index": marker,
                    "Cut-off": x["cutoff"],
                    "AUC": x["auc"],
                    "95% CI": x.get("ci", "Not reported"),
                    "Sensitivity (%)": x["sensitivity"],
                    "Specificity (%)": x["specificity"],
                    "p value": x.get("p", "Not reported")
                })
        st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)

    st.markdown("**PREVENT outcome definition:** cardiovascular disease was defined as PREVENT 10-year risk ≥7.5% in the thesis ROC analysis.")

with tab4:
    st.subheader("PREVENT 10-year risk")
    st.info(
        "Enter the PREVENT 10-year risk (%) calculated using the official validated PREVENT tool. "
        "This application does not independently calculate the PREVENT equations."
    )
    st.markdown(
        "- Thesis outcome: cardiovascular disease was defined as PREVENT risk ≥7.5%.\\n"
        "- The TyG-derived ROC cut-offs for this outcome are shown below.\\n"
        "- PREVENT estimates risk; it is not an observed cardiovascular event."
    )
    st.dataframe(
        pd.DataFrame([
            {"Index": marker, "Thesis cut-off": stats["cutoff"],
             "AUC": stats["auc"], "Sensitivity (%)": stats["sensitivity"],
             "Specificity (%)": stats["specificity"]}
            for marker, stats in THESIS["Cardiovascular Disease"].items()
            if stats["cutoff"] is not None
        ]),
        hide_index=True, use_container_width=True
    )
    st.warning(
        "The PREVENT equations were developed using US cohorts. Their calibration in Egyptian "
        "patients should not be assumed without local validation."
    )

with tab5:
    st.subheader("Calculation formulas")
    st.latex(r"TyG = \ln\left(\frac{TG\ (mg/dL)\times FPG\ (mg/dL)}{2}\right)")
    st.latex(r"TyG\text{-}BMI = TyG \times BMI")
    st.latex(r"TyG\text{-}WHR = TyG \times WHR")
    st.latex(r"HOMA\text{-}IR = \frac{Fasting\ insulin\ (\mu IU/mL)\times FPG\ (mg/dL)}{405}")
    st.latex(r"BMI = \frac{Weight\ (kg)}{Height\ (m)^2}")
    st.latex(r"WHR = \frac{Waist\ circumference}{Hip\ circumference}")
    st.markdown("""
    **Important methodological notes**
    - The TyG formula requires TG and fasting glucose in mg/dL. The single-patient calculator converts mmol/L inputs automatically.
    - HOMA-IR ≥1.9 is the insulin-resistance reference definition. The separate HOMA-IR ROC comparison for MetS used cut-off 1.950 (AUC 0.903; sensitivity 81.0%; specificity 99.0%).
    - PREVENT risk is not calculated here. Enter a PREVENT 10-year risk value obtained from the validated PREVENT calculator.
    - Metabolic syndrome remains a clinical diagnosis based on the accepted component criteria. TyG-derived cut-offs are screening/classification thresholds from this thesis ROC analysis, not replacements for the clinical definition.
    - The cut-offs and performance estimates were derived in the thesis study cohort and require external validation before use in other populations.
    - PREVENT estimates risk; it is not an observed cardiovascular event.
    """)

st.sidebar.header("About")
st.sidebar.write("Thesis-based clinical research calculator")
st.sidebar.write("Version 2.3 – Table 13 exact values")
st.sidebar.info("Use fasting laboratory measurements. Confirm units before calculation.")
