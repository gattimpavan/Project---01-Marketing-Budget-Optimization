"""
One-Click Runner for Project - 01: Marketing Budget Optimization
Executes data generation, unit economics modeling, SciPy non-linear optimization,
generates the publication-grade PDF report, and launches the interactive dashboard server.
"""
import os
import sys
import subprocess
import webbrowser
from models.data_generator import generate_marketing_data
from models.optimizer import BudgetOptimizer
from report.generate_pdf_report import generate_pdf
import pandas as pd

def main():
    print("=" * 80)
    print(" PROJECT - 01: MARKETING BUDGET OPTIMIZATION")
    print(" Procter & Gamble (P&G) Multi-Channel Spend Intelligence & Optimization Engine")
    print("=" * 80)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    camp_path = os.path.join(data_dir, "channel_performance.csv")
    cust_path = os.path.join(data_dir, "customer_conversions.csv")
    report_path = os.path.join(base_dir, "report", "Marketing_Budget_Optimization_Report.pdf")

    # Step 1: Data Generation
    print("\n[Step 1/4] Checking and generating marketing dataset...")
    df_camp, df_cust = generate_marketing_data(data_dir)
    print(f"  ✓ Processed {len(df_camp)} marketing channels & {len(df_cust):,} customer journeys.")

    # Step 2: Optimization
    print("\n[Step 2/4] Running SciPy SLSQP non-linear budget optimization...")
    optimizer = BudgetOptimizer(df_camp, df_cust)
    df_opt, summary = optimizer.optimize()
    print("  ✓ Optimization converged successfully!")
    print(f"  • Current Monthly Revenue:   ${summary['current_total_revenue']:,.2f}")
    print(f"  • Projected Monthly Revenue: ${summary['projected_total_revenue']:,.2f}")
    print(f"  • Net Revenue Uplift:        +${summary['revenue_uplift']:,.2f} (+{summary['revenue_uplift_pct']}%)")
    print(f"  • Blended ROAS Expansion:    {summary['current_blended_roas']}x -> {summary['projected_blended_roas']}x")
    print(f"  • Wasted Spend Reallocated:  ${summary['inefficient_spend_eliminated']:,.2f}/mo")

    # Step 3: PDF Generation
    print("\n[Step 3/4] Generating executive PDF intelligence report...")
    pdf_file = generate_pdf(report_path)
    print(f"  ✓ PDF Report generated: {pdf_file}")

    # Step 4: Web Dashboard Launch
    print("\n[Step 4/4] Starting Flask Interactive Dashboard...")
    print("  ✓ Access URL: http://127.0.0.1:5000")
    print("  ✓ PDF Direct Download: http://127.0.0.1:5000/api/download-pdf")
    print("\nLaunching Flask development server (Press Ctrl+C to stop)...")
    
    from app import app
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()
