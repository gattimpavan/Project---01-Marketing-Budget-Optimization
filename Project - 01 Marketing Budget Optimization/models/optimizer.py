"""
Marketing Budget Optimization Engine
Uses SciPy non-linear constrained optimization (SLSQP) to reallocate marketing budgets
for maximum revenue and net profit subject to channel bounds and diminishing returns.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from models.response_curves import ResponseCurveModel
from models.economics import UnitEconomicsAnalyzer

class BudgetOptimizer:
    def __init__(self, df_campaigns, df_customers):
        self.df_campaigns = df_campaigns.copy()
        self.df_customers = df_customers.copy()
        self.rc_model = ResponseCurveModel(self.df_campaigns)
        self.econ_analyzer = UnitEconomicsAnalyzer(self.df_campaigns, self.df_customers)
        self.econ_data = self.econ_analyzer.analyze_channel_economics()
        self.channels = self.df_campaigns["channel"].tolist()
        
    def optimize(self, total_budget=None, strategy="profit_maximization", min_spend_ratio=0.15, max_spend_multiplier=2.2):
        """
        Solves non-linear constrained optimization problem:
        max Sum(R_i(S_i)) or Sum(R_i(S_i) * margin_i - S_i)
        s.t. Sum(S_i) <= TotalBudget
             LowerBound_i <= S_i <= UpperBound_i
        """
        curr_total_spend = self.df_campaigns["current_spend"].sum()
        if total_budget is None:
            total_budget = curr_total_spend
            
        n_channels = len(self.channels)
        x0 = np.array([row["current_spend"] for _, row in self.df_campaigns.iterrows()])
        
        # Scale initial vector to match total_budget if different
        if x0.sum() > 0:
            x0 = x0 * (total_budget / x0.sum())
            
        # Get channel margin and efficiency status
        channel_meta = {}
        for _, row in self.econ_data.iterrows():
            ch = row["channel"]
            channel_meta[ch] = {
                "efficiency_status": row["efficiency_status"],
                "ltv_cac_ratio": row["ltv_cac_ratio"],
                "gross_margin_rate": 0.75 if row["efficiency_status"] == "Star Performer" else (0.50 if "Bleed" in row["efficiency_status"] else 0.65)
            }
            
        # Bounds per channel
        bounds = []
        for ch in self.channels:
            curr_s = self.df_campaigns.loc[self.df_campaigns["channel"] == ch, "current_spend"].values[0]
            status = channel_meta[ch]["efficiency_status"]
            
            if status == "Inefficient Spend Bleed":
                # Restrict bleeding channel heavily (e.g. cut by 60% - 90%)
                lb = max(2000.0, curr_s * 0.05)
                ub = curr_s * 0.35
            elif status == "Needs Optimization":
                lb = curr_s * 0.3
                ub = curr_s * 1.1
            elif status == "Star Performer":
                # High scalability headroom
                lb = curr_s * 0.8
                ub = curr_s * max_spend_multiplier
            else: # Profitable Growth
                lb = curr_s * 0.5
                ub = curr_s * 1.8
                
            bounds.append((lb, ub))
            
        # Objective functions (to minimize negative)
        if strategy == "profit_maximization":
            def objective(spends):
                net_profit = 0.0
                for i, ch in enumerate(self.channels):
                    rev = self.rc_model.predict_revenue(ch, spends[i])
                    margin_rate = channel_meta[ch]["gross_margin_rate"]
                    net_profit += (rev * margin_rate) - spends[i]
                return -net_profit
        elif strategy == "revenue_maximization":
            def objective(spends):
                total_rev = sum(self.rc_model.predict_revenue(ch, spends[i]) for i, ch in enumerate(self.channels))
                return -total_rev
        else: # balanced_growth
            def objective(spends):
                total_rev = sum(self.rc_model.predict_revenue(ch, spends[i]) for i, ch in enumerate(self.channels))
                # Add penalty for extreme concentration
                penalty = 0.001 * np.sum((spends - (total_budget / n_channels))**2)
                return -(total_rev - penalty)
                
        # Constraints: Total spend == total_budget
        constraints = [
            {"type": "eq", "fun": lambda s: np.sum(s) - total_budget}
        ]
        
        res = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500, "ftol": 1e-6}
        )
        
        opt_spends = res.x if res.success else x0
        
        # Calculate comparison details
        results = []
        curr_total_rev = 0.0
        opt_total_rev = 0.0
        
        for i, ch in enumerate(self.channels):
            curr_s = self.df_campaigns.loc[self.df_campaigns["channel"] == ch, "current_spend"].values[0]
            curr_r = self.df_campaigns.loc[self.df_campaigns["channel"] == ch, "actual_revenue"].values[0]
            
            opt_s = round(float(opt_spends[i]), 2)
            opt_r = round(float(self.rc_model.predict_revenue(ch, opt_s)), 2)
            
            curr_roas = curr_r / max(1, curr_s)
            opt_roas = opt_r / max(1, opt_s)
            
            spend_delta = opt_s - curr_s
            spend_delta_pct = (spend_delta / curr_s) * 100
            rev_delta = opt_r - curr_r
            rev_delta_pct = (rev_delta / curr_r) * 100
            
            curr_total_rev += curr_r
            opt_total_rev += opt_r
            
            results.append({
                "channel": ch,
                "current_spend": round(curr_s, 2),
                "recommended_spend": opt_s,
                "spend_change": round(spend_delta, 2),
                "spend_change_pct": round(spend_delta_pct, 1),
                "current_revenue": round(curr_r, 2),
                "projected_revenue": opt_r,
                "revenue_change": round(rev_delta, 2),
                "revenue_change_pct": round(rev_delta_pct, 1),
                "current_roas": round(curr_roas, 2),
                "projected_roas": round(opt_roas, 2),
                "status": "Cut / Defund" if spend_delta < -40000 else ("Expand / Scale" if spend_delta > 40000 else "Maintain / Fine-tune"),
                "efficiency_status": channel_meta[ch]["efficiency_status"]
            })
            
        df_results = pd.DataFrame(results)
        
        # Aggregate summary metrics
        total_opt_spend = df_results["recommended_spend"].sum()
        curr_blended_roas = curr_total_rev / curr_total_spend
        opt_blended_roas = opt_total_rev / total_opt_spend
        revenue_uplift = opt_total_rev - curr_total_rev
        revenue_uplift_pct = (revenue_uplift / curr_total_rev) * 100
        
        # Inefficient spend eliminated
        initial_inefficient_spend = self.econ_data["inefficient_spend"].sum()
        # Post-optimization inefficient spend in those specific bleeding channels:
        post_inefficient_spend = df_results[df_results["efficiency_status"] == "Inefficient Spend Bleed"]["recommended_spend"].sum() * 0.35
        inefficient_spend_saved = initial_inefficient_spend - post_inefficient_spend
        
        summary = {
            "strategy": strategy,
            "current_total_spend": round(curr_total_spend, 2),
            "optimized_total_spend": round(total_opt_spend, 2),
            "current_total_revenue": round(curr_total_rev, 2),
            "projected_total_revenue": round(opt_total_rev, 2),
            "revenue_uplift": round(revenue_uplift, 2),
            "revenue_uplift_pct": round(revenue_uplift_pct, 1),
            "current_blended_roas": round(curr_blended_roas, 2),
            "projected_blended_roas": round(opt_blended_roas, 2),
            "roas_improvement": round(opt_blended_roas - curr_blended_roas, 2),
            "inefficient_spend_eliminated": round(max(0, inefficient_spend_saved), 2),
            "optimization_converged": bool(res.success)
        }
        
        return df_results, summary

if __name__ == "__main__":
    df_camp = pd.read_csv("data/channel_performance.csv")
    df_cust = pd.read_csv("data/customer_conversions.csv")
    opt = BudgetOptimizer(df_camp, df_cust)
    df_res, summary = opt.optimize()
    print("--- Reallocation Recommendations ---")
    print(df_res[["channel", "current_spend", "recommended_spend", "spend_change_pct", "current_roas", "projected_roas", "status"]])
    print("\n--- Optimization Summary ---")
    for k, v in summary.items():
        print(f"{k}: {v}")
