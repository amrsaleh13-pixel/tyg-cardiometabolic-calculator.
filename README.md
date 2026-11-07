# TyG & Cardiometabolic Risk Calculator

A public, mobile-responsive Streamlit application for calculating:
- TyG Index
- TyG-BMI
- TyG-WHR
- HOMA-IR

It displays the ROC cut-offs and diagnostic-performance values transcribed from Table 13 of the user's thesis.

## Deploy publicly with Streamlit Community Cloud

1. Create a GitHub repository, for example `tyg-cardiometabolic-calculator`.
2. Upload **all files and folders** in this project to the repository root:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `README.md`
3. Open https://share.streamlit.io/ and sign in with GitHub.
4. Choose **Create app**, select the repository and branch, and set the main file path to `app.py`.
5. Click **Deploy**. Streamlit will provide a public `*.streamlit.app` URL.
6. Open that URL on Android or iPhone. Use the browser menu and choose **Add to Home screen** (Android) or **Add to Home Screen** from the iOS Share menu.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Important clinical and privacy notes

- This public app is a research and screening aid, not a stand-alone diagnostic device.
- ROC thresholds are cohort-derived and require external validation before application to other populations.
- PREVENT risk is entered manually from the official PREVENT calculator; this app does not implement the PREVENT equations.
- Do not enter patient names, national IDs, phone numbers, or other identifiable health information.
- Uploaded batch files are processed by the running app. Do not upload identifiable patient datasets to a public deployment.
