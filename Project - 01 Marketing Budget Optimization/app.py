"""
Flask Application for Marketing Budget Optimization Dashboard
Serves the web dashboard, interactive simulation API, and PDF export.
"""
import os
import json
import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file

from models.data_generator import generate_marketing_data
from models.attribution import MultiTouchAttribution
from models.economics import UnitEconomicsAnalyzer
from models.response_curves import ResponseCurveModel
from models.optimizer import BudgetOptimizer
from report.generate_pdf_report import generate_pdf

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure data exists on startup
DATA_DIR = os.path.join(BASE_DIR, "data")
CAMPAIGNS_PATH = os.path.join(DATA_DIR, "channel_performance.csv")
CUSTOMERS_PATH = os.path.join(DATA_DIR, "customer_conversions.csv")
REPORT_PATH = os.path.join(BASE_DIR, "report", "Marketing_Budget_Optimization_Report.pdf")

if not os.path.exists(CAMPAIGNS_PATH) or not os.path.exists(CUSTOMERS_PATH):
    generate_marketing_data(DATA_DIR)

def load_data():
    df_camp = pd.read_csv(CAMPAIGNS_PATH)
    df_cust = pd.read_csv(CUSTOMERS_PATH)
    return df_camp, df_cust

def sanitize(val):
    if isinstance(val, (int, float, str, bool)) or val is None:
        return val
    elif hasattr(val, "item"):  # numpy scalars like int64, float64, bool_
        return val.item()
    elif isinstance(val, dict):
        return {k: sanitize(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [sanitize(v) for v in val]
    return str(val)

def df_to_records(df):
    return json.loads(df.to_json(orient="records"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/overview", methods=["GET"])
def get_overview():
    df_camp, df_cust = load_data()
    analyzer = UnitEconomicsAnalyzer(df_camp, df_cust)
    econ_df = analyzer.analyze_channel_economics()
    portfolio_summary = sanitize(analyzer.get_portfolio_summary())
    
    mta = MultiTouchAttribution(df_cust)
    attr_comp = mta.get_attribution_comparison()
    
    opt = BudgetOptimizer(df_camp, df_cust)
    df_opt, opt_summary = opt.optimize()
    
    rc = ResponseCurveModel(df_camp)
    marginal_metrics = rc.get_all_marginal_metrics()
    
    # Merge economics with marginal ROAS
    econ_combined = pd.merge(econ_df, marginal_metrics[["channel", "marginal_roas", "saturation_stage"]], on="channel", how="left")
    
    # Sample customer journeys for preview
    cust_sample = df_cust.sample(n=min(50, len(df_cust)), random_state=42)
    
    return jsonify({
        "status": "success",
        "portfolio_summary": portfolio_summary,
        "optimization_summary": sanitize(opt_summary),
        "reallocation": df_to_records(df_opt),
        "channel_economics": df_to_records(econ_combined),
        "attribution": df_to_records(attr_comp),
        "customer_journeys_sample": df_to_records(cust_sample)
    })

@app.route("/api/optimize", methods=["POST"])
def optimize_budget():
    data = request.get_json() or {}
    total_budget = data.get("total_budget", None)
    strategy = data.get("strategy", "profit_maximization")
    
    if total_budget is not None:
        try:
            total_budget = float(total_budget)
        except ValueError:
            total_budget = None
            
    df_camp, df_cust = load_data()
    opt = BudgetOptimizer(df_camp, df_cust)
    df_opt, summary = opt.optimize(total_budget=total_budget, strategy=strategy)
    
    return jsonify({
        "status": "success",
        "summary": sanitize(summary),
        "reallocation": df_to_records(df_opt)
    })

@app.route("/api/curve-data", methods=["GET"])
def get_curve_data():
    df_camp, _ = load_data()
    rc = ResponseCurveModel(df_camp)
    curves = {}
    for ch in df_camp["channel"]:
        curves[ch] = rc.get_channel_curve_points(ch)
    return jsonify({"status": "success", "curves": curves})

@app.route("/api/download-pdf", methods=["GET"])
def download_pdf():
    # If PDF does not exist or refresh is requested, generate it
    if not os.path.exists(REPORT_PATH) or request.args.get("refresh") == "true":
        generate_pdf(REPORT_PATH)
    return send_file(
        REPORT_PATH,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="Project-01_Marketing_Budget_Optimization_Report.pdf"
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
