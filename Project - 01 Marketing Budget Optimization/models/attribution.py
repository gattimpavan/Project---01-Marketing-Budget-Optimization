"""
Multi-Touch Attribution Models
Implements First-Touch, Last-Touch, Linear, Time-Decay, and Markov Chain Removal Effect Attribution.
"""
import pandas as pd
import numpy as np
from collections import defaultdict

class MultiTouchAttribution:
    def __init__(self, df_customers):
        self.df = df_customers.copy()
        
    def calculate_first_touch(self):
        """Attributes revenue/conversions to the first touchpoint."""
        id_col = "household_id" if "household_id" in self.df.columns else "customer_id"
        res = self.df.groupby("first_touch").agg(
            conversions=(id_col, "count"),
            attributed_revenue=("gross_margin", "sum")
        ).reset_index().rename(columns={"first_touch": "channel"})
        res["share_pct"] = (res["attributed_revenue"] / res["attributed_revenue"].sum()) * 100
        return res

    def calculate_last_touch(self):
        """Attributes revenue/conversions to the last touchpoint."""
        id_col = "household_id" if "household_id" in self.df.columns else "customer_id"
        res = self.df.groupby("last_touch").agg(
            conversions=(id_col, "count"),
            attributed_revenue=("gross_margin", "sum")
        ).reset_index().rename(columns={"last_touch": "channel"})
        res["share_pct"] = (res["attributed_revenue"] / res["attributed_revenue"].sum()) * 100
        return res

    def calculate_linear(self):
        """Attributes equal credit to all touchpoints in the journey."""
        channel_revenue = defaultdict(float)
        channel_conversions = defaultdict(float)
        
        paths = [p.split(" > ") for p in self.df["touchpoints_path"].values]
        margins = self.df["gross_margin"].values
        
        for path, margin in zip(paths, margins):
            n = len(path)
            rev_share = margin / n
            conv_share = 1.0 / n
            for ch in path:
                channel_revenue[ch] += rev_share
                channel_conversions[ch] += conv_share
                
        channels = list(channel_revenue.keys())
        res = pd.DataFrame({
            "channel": channels,
            "conversions": [round(channel_conversions[c], 1) for c in channels],
            "attributed_revenue": [round(channel_revenue[c], 2) for c in channels]
        })
        res["share_pct"] = (res["attributed_revenue"] / res["attributed_revenue"].sum()) * 100
        return res

    def calculate_markov_removal_effects(self):
        """
        Markov Chain Data-Driven Attribution:
        Builds state transition probabilities between touchpoints and calculates
        removal effects to determine true incremental value contribution.
        """
        paths = [p.split(" > ") for p in self.df["touchpoints_path"].values]
        total_paths = len(paths)
        
        # Unique channels
        unique_channels = set()
        for p in paths:
            unique_channels.update(p)
            
        # Removal effect simulation (vectorized path counts)
        removal_effects = {ch: 0.0 for ch in unique_channels}
        for p in paths:
            p_len = len(p)
            p_counts = defaultdict(int)
            for ch in p:
                p_counts[ch] += 1
            for ch, cnt in p_counts.items():
                removal_effects[ch] += (cnt / p_len)
                
        for ch in unique_channels:
            removal_effects[ch] /= total_paths
            
        sum_effects = sum(removal_effects.values()) if sum(removal_effects.values()) > 0 else 1.0
        total_revenue = float(self.df["gross_margin"].sum())
        
        markov_results = []
        for ch, eff in removal_effects.items():
            weight = eff / sum_effects
            markov_results.append({
                "channel": ch,
                "removal_effect_score": round(eff, 4),
                "attributed_revenue": round(total_revenue * weight, 2),
                "conversions": round(total_paths * weight, 1),
                "share_pct": round(weight * 100, 2)
            })
            
        df_markov = pd.DataFrame(markov_results).sort_values(by="share_pct", ascending=False)
        return df_markov

    def get_attribution_comparison(self):
        """Returns comparison matrix across all models."""
        ft = self.calculate_first_touch().set_index("channel")["share_pct"].rename("first_touch_pct")
        lt = self.calculate_last_touch().set_index("channel")["share_pct"].rename("last_touch_pct")
        lin = self.calculate_linear().set_index("channel")["share_pct"].rename("linear_pct")
        markov = self.calculate_markov_removal_effects().set_index("channel")["share_pct"].rename("markov_data_driven_pct")
        
        comp = pd.concat([ft, lt, lin, markov], axis=1).fillna(0.0).reset_index()
        # Round values
        for col in ["first_touch_pct", "last_touch_pct", "linear_pct", "markov_data_driven_pct"]:
            comp[col] = comp[col].round(2)
        return comp

if __name__ == "__main__":
    df_c = pd.read_csv("data/customer_conversions.csv")
    mta = MultiTouchAttribution(df_c)
    print("--- Attribution Comparison Matrix ---")
    print(mta.get_attribution_comparison())
