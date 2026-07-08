# Automated Decline Curve Analysis (DCA) Web App

A web-based tool built for Reservoir and Production Engineering that automates well-production forecasting. It replaces subjective, manual curve-fitting by using non-linear regression to optimize Arps' decline parameters and calculate Estimated Ultimate Recovery (EUR).

## Key Features
* **Automated Parameter Extraction:** Uses least-squares regression to find optimal initial rate ($q_i$), b-factor ($b$), and decline rate ($D_i$).
* **EUR Calculation:** Computes total recoverable reserves via numerical integration up to a user-defined economic abandonment rate.
* **Interactive Visualization:** Dynamic plotting of historical data vs. predictive models with Linear and Semi-Log (Log-Y) scale toggles.
* **Bounded Optimization:** Math limits enforced on the $b$-factor (0.001 to 2.0) and rates to prevent non-physical outputs.

## Tech Stack
* **Frontend/Framework:** Streamlit
* **Data Handling:** Pandas, NumPy
* **Optimization/Math:** SciPy
* **Data Visualization:** Plotly

## Math
The app is built entirely on **Arps' Hyperbolic Decline Equation**:

$$q(t) = \frac{q_i}{(1 + b \cdot D_i \cdot t)^{1/b}}$$

EUR is calculated by integrating the area under the forecasted curve using NumPy's trapezoidal rule (`np.trapezoid`), bounded by `Time = 0` and the time the well hits the economic limit (e.g., 10 bbl/day).


## How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Test Data

Run the included data generator script to create a dummy production CSV.

```bash
python generate_data.py
```

### 3. Run the Web App

```bash
streamlit run app.py
```
Upload the generated CSV into the app sidebar to view the automated forecast.