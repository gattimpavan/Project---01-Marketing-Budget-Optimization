"""
Unit Economics & Customer Profitability Analysis
Calculates LTV, CAC, LTV:CAC ratio, Payback period, and identifies inefficient spend.
"""
import pandas as pd
import numpy as np

class UnitEconomicsAnalyzer:
    def __init__(self, df_campaigns, df_customers):
        self.df_campaigns = df_campaigns.copy()
        self.df_customers = df_customers.copy()

    def analyze_channel_economics(self):
        """Computes comprehensive unit economics by acquisition channel."""
        id_col = "household_id" if "household_id" in self.df_customers.columns else "customer_id"
        cust_agg = self.df_customers.groupby("acquisition_channel").agg(
            total_customers=(id_col, "count"),
            avg_ltv=("ltv", "mean"),
            median_ltv=("ltv", "median"),
            avg_gross_margin=("gross_margin", "mean"),
            total_gross_profit=("net_profit", "sum"),
            profitable_cust_count=("is_profitable", lambda s: (s == True).sum()),
            churn_rate=("churned", "mean"),
            avg_payback_months=("payback_months", "mean"),
            high_value_customers=("ltv", lambda s: (s >= 300).sum())
        ).reset_index().rename(columns={"acquisition_channel": "channel"})
        
        # Merge with campaign spend and revenue data
        merged = pd.merge(self.df_campaigns, cust_agg, on="channel", how="left")
        
        # Calculate derived metrics
        merged["ltv_cac_ratio"] = (merged["avg_ltv"] / merged["cac"]).round(2)
        merged["profitable_customer_pct"] = ((merged["profitable_cust_count"] / merged["total_customers"]) * 100).round(1)
        merged["churn_rate_pct"] = (merged["churn_rate"] * 100).round(1)
        merged["high_value_pct"] = ((merged["high_value_customers"] / merged["total_customers"]) * 100).round(1)
        merged["avg_ltv"] = merged["avg_ltv"].round(2)
        merged["avg_payback_months"] = merged["avg_payback_months"].round(1)
        
        # Health & Efficiency Status
        # Benchmark:
        # Healthy: LTV:CAC >= 3.0 & Profitable % >= 80
        # Moderate: LTV:CAC >= 2.0 & Profitable % >= 65
        # Inefficient / Bleed: LTV:CAC < 2.0 or Profitable % < 65
        def classify_health(row):
            ratio = row["ltv_cac_ratio"]
            prof_pct = row["profitable_customer_pct"]
            if ratio >= 3.5 and prof_pct >= 85:
                return "Star Performer"
            elif ratio >= 2.5:
                return "Profitable Growth"
            elif ratio >= 1.8:
                return "Needs Optimization"
            else:
                return "Inefficient Spend Bleed"
                
        merged["efficiency_status"] = merged.apply(classify_health, axis=1)
        
        # Quantify Inefficient Spend:
        # For channels with LTV:CAC < 2.0 or negative net profit, spend is considered inefficient
        def calculate_inefficient_spend(row):
            ratio = row["ltv_cac_ratio"]
            spend = row["current_spend"]
            if ratio < 1.5:
                # 70% to 90% of spend is inefficient/wasted
                return round(spend * 0.85, 2)
            elif ratio < 2.0:
                # 35% to 50% is inefficient
                return round(spend * 0.45, 2)
            elif row["churn_rate_pct"] > 35:
                return round(spend * 0.25, 2)
            else:
                return 0.0
                
        merged["inefficient_spend"] = merged.apply(calculate_inefficient_spend, axis=1)
        merged["inefficient_spend_pct"] = ((merged["inefficient_spend"] / merged["current_spend"]) * 100).round(1)
        
        # Primary Inefficiency Root Cause
        def diagnose_cause(row):
            if row["efficiency_status"] in ["Star Performer", "Profitable Growth"]:
                return "None (High Performing Channel)"
            causes = []
            if row["cac"] > 100:
                causes.append("High Acquisition Cost (CAC)")
            if row["cvr_pct"] < 1.0:
                causes.append("Low Conversion Rate (CVR)")
            if row["churn_rate_pct"] > 30:
                causes.append("High Customer Churn")
            if row["ltv_cac_ratio"] < 1.5:
                causes.append("Sub-economic LTV")
            return ", ".join(causes) if causes else "Low Intent Traffic"
            
        merged["inefficiency_root_cause"] = merged.apply(diagnose_cause, axis=1)
        
        return merged

    def get_portfolio_summary(self):
        """Returns executive KPI scorecard."""
        econ = self.analyze_channel_economics()
        
        total_spend = econ["current_spend"].sum()
        total_revenue = econ["actual_revenue"].sum()
        total_inefficient_spend = econ["inefficient_spend"].sum()
        blended_roas = total_revenue / total_spend
        blended_cac = total_spend / econ["conversions"].sum()
        blended_ltv = econ["avg_ltv"].mean()
        blended_ltv_cac = blended_ltv / blended_cac
        
        inefficient_channels = econ[econ["inefficient_spend"] > 0]["channel"].tolist()
        star_channels = econ[econ["efficiency_status"] == "Star Performer"]["channel"].tolist()
        
        return {
            "total_monthly_spend": round(total_spend, 2),
            "total_monthly_revenue": round(total_revenue, 2),
            "blended_roas": round(blended_roas, 2),
            "blended_cac": round(blended_cac, 2),
            "blended_ltv": round(blended_ltv, 2),
            "blended_ltv_cac": round(blended_ltv_cac, 2),
            "total_inefficient_spend": round(total_inefficient_spend, 2),
            "inefficient_spend_ratio_pct": round((total_inefficient_spend / total_spend) * 100, 1),
            "inefficient_channels": inefficient_channels,
            "star_channels": star_channels
        }

if __name__ == "__main__":
    df_camp = pd.read_csv("data/channel_performance.csv")
    df_cust = pd.read_csv("data/customer_conversions.csv")
    analyzer = UnitEconomicsAnalyzer(df_camp, df_cust)
    print("--- Channel Unit Economics ---")
    print(analyzer.analyze_channel_economics()[["channel", "cac", "avg_ltv", "ltv_cac_ratio", "efficiency_status", "inefficient_spend"]])
    print("\n--- Portfolio Summary ---")
    print(analyzer.get_portfolio_summary())
