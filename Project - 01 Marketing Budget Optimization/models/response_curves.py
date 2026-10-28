"""
Marketing Response Curves & Diminishing Marginal Returns
Fits and models channel saturation curves, elasticity, and marginal ROAS.
"""
import numpy as np
import pandas as pd

class ResponseCurveModel:
    def __init__(self, df_campaigns):
        self.df_campaigns = df_campaigns.copy()
        
    def predict_revenue(self, channel, spend):
        """Calculates expected revenue using Hill Saturation function."""
        row = self.df_campaigns[self.df_campaigns["channel"] == channel].iloc[0]
        K = row["saturation_K"]
        S_half = row["saturation_S_half"]
        n = row["saturation_n"]
        
        if spend <= 0:
            return 0.0
        spend_n = spend ** n
        return K * (spend_n / (S_half ** n + spend_n))
        
    def marginal_roas(self, channel, spend, delta=100.0):
        """Numerical derivative dRevenue/dSpend to calculate marginal ROAS."""
        r_plus = self.predict_revenue(channel, spend + delta)
        r_minus = self.predict_revenue(channel, max(0.0, spend - delta))
        denom = (spend + delta) - max(0.0, spend - delta)
        return (r_plus - r_minus) / denom

    def get_channel_curve_points(self, channel, n_points=50, max_multiplier=2.5):
        """Generates spend vs revenue curve points for plotting."""
        row = self.df_campaigns[self.df_campaigns["channel"] == channel].iloc[0]
        curr_spend = row["current_spend"]
        max_spend = curr_spend * max_multiplier
        
        spends = np.linspace(1000, max_spend, n_points)
        revenues = [self.predict_revenue(channel, s) for s in spends]
        marginal_roas_vals = [self.marginal_roas(channel, s) for s in spends]
        
        return {
            "channel": channel,
            "spends": [round(float(s), 2) for s in spends],
            "revenues": [round(float(r), 2) for r in revenues],
            "marginal_roas": [round(float(m), 3) for m in marginal_roas_vals],
            "current_spend": float(curr_spend),
            "current_revenue": float(row["actual_revenue"]),
            "current_marginal_roas": round(float(self.marginal_roas(channel, curr_spend)), 3)
        }

    def get_all_marginal_metrics(self):
        """Returns current marginal ROAS for all channels."""
        res = []
        for _, row in self.df_campaigns.iterrows():
            ch = row["channel"]
            spend = row["current_spend"]
            m_roas = self.marginal_roas(ch, spend)
            avg_roas = row["roas"]
            res.append({
                "channel": ch,
                "current_spend": spend,
                "average_roas": round(avg_roas, 2),
                "marginal_roas": round(m_roas, 3),
                "saturation_stage": "Diminishing Bleed" if m_roas < 1.0 else ("Optimal Band" if m_roas < 2.0 else "High Scalability Zone")
            })
        return pd.DataFrame(res)

if __name__ == "__main__":
    df_camp = pd.read_csv("data/channel_performance.csv")
    rc = ResponseCurveModel(df_camp)
    print("--- Channel Marginal ROAS & Saturation Status ---")
    print(rc.get_all_marginal_metrics())
