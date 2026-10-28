"""
P&G Marketing Data Generator
Simulates Procter & Gamble (P&G) multi-channel marketing, retail media,
household consumer journeys, and repeat purchase conversions.
"""
import os
import numpy as np
import pandas as pd

def generate_marketing_data(output_dir="data", seed=42):
    np.random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. P&G Strategic Marketing Channels
    channels = [
        "Amazon Ads (Retail Media)",
        "Walmart Connect & Retail Media",
        "Google Shopping & Search",
        "Meta Social (IG / FB Reels)",
        "Connected TV & YouTube Video",
        "P&G Good Everyday Rewards CRM",
        "TikTok Creator & Influencer",
        "Programmatic Open-Web Display"
    ]
    
    # P&G Portfolio Brands represented
    brands = [
        "Tide & Downy (Fabric Care)",
        "Pampers (Baby Care)",
        "Gillette & Venus (Grooming)",
        "Oral-B & Crest (Oral Care)",
        "Olay & Pantene (Beauty & Hair)",
        "Dawn & Cascade (Home Care)",
        "Febreze (Air Care)",
        "Bounty & Charmin (Family Care)"
    ]
    
    # Monthly spend configuration ($) for P&G Regional Consumer Portfolio ($12,000,000 Total Budget)
    current_spends = {
        "Amazon Ads (Retail Media)": 2800000,
        "Walmart Connect & Retail Media": 2400000,
        "Meta Social (IG / FB Reels)": 2100000,
        "Google Shopping & Search": 1600000,
        "Connected TV & YouTube Video": 1200000,
        "Programmatic Open-Web Display": 1100000,  # Severe ad-fraud / bot bleed
        "TikTok Creator & Influencer": 500000,     # High churn promo chasers
        "P&G Good Everyday Rewards CRM": 300000,    # Underfunded high-efficiency engine
    }
    
    # Hill Response Saturation Parameters: Revenue(S) = K * (S^n) / (S_half^n + S^n)
    channel_params = {
        "Amazon Ads (Retail Media)": {"K": 8200000, "S_half": 2500000, "n": 1.25, "base_cpc": 1.75, "target_tier": "Retail Conversion"},
        "Walmart Connect & Retail Media": {"K": 7100000, "S_half": 2200000, "n": 1.20, "base_cpc": 1.45, "target_tier": "Omnichannel Retail"},
        "Google Shopping & Search": {"K": 4800000, "S_half": 1500000, "n": 1.30, "base_cpc": 2.10, "target_tier": "High Intent Search"},
        "Meta Social (IG / FB Reels)": {"K": 5200000, "S_half": 2000000, "n": 1.15, "base_cpc": 1.20, "target_tier": "Lifestyle & Beauty"},
        "Connected TV & YouTube Video": {"K": 3100000, "S_half": 1400000, "n": 1.10, "base_cpc": 0.85, "target_tier": "Brand Equity & Reach"},
        "P&G Good Everyday Rewards CRM": {"K": 1900000, "S_half": 280000, "n": 1.45, "base_cpc": 0.35, "target_tier": "Loyalty & Retention"},
        "TikTok Creator & Influencer": {"K": 1100000, "S_half": 550000, "n": 0.95, "base_cpc": 0.80, "target_tier": "Gen-Z & Trial"},
        "Programmatic Open-Web Display": {"K": 950000, "S_half": 1600000, "n": 0.80, "base_cpc": 0.55, "target_tier": "Open Display (Bleed)"},
    }

    # Generate Campaign Performance Data
    campaign_records = []
    
    for ch in channels:
        p = channel_params[ch]
        spend = current_spends[ch]
        k, s_half, n = p["K"], p["S_half"], p["n"]
        theoretical_rev = k * (spend**n) / (s_half**n + spend**n)
        actual_rev = theoretical_rev * np.random.uniform(0.95, 1.05)
        
        cpc = p["base_cpc"] * np.random.uniform(0.92, 1.08)
        clicks = int(spend / cpc)
        
        # Click-through rate
        if "Retail Media" in ch or "Search" in ch:
            ctr = np.random.uniform(0.024, 0.048)
        elif "CRM" in ch:
            ctr = np.random.uniform(0.045, 0.075)
        elif "Social" in ch:
            ctr = np.random.uniform(0.014, 0.025)
        else:
            ctr = np.random.uniform(0.005, 0.012)
            
        impressions = int(clicks / ctr)
        
        # Conversion rate (CPG purchase or verified cart add)
        if "CRM" in ch:
            cvr = np.random.uniform(0.075, 0.110)
        elif "Amazon" in ch or "Walmart" in ch:
            cvr = np.random.uniform(0.052, 0.082)
        elif "Search" in ch:
            cvr = np.random.uniform(0.038, 0.060)
        elif "Social" in ch:
            cvr = np.random.uniform(0.025, 0.039)
        elif "TikTok" in ch:
            cvr = np.random.uniform(0.016, 0.028)
        elif "Video" in ch:
            cvr = np.random.uniform(0.012, 0.022)
        else: # Programmatic Open Web
            cvr = np.random.uniform(0.004, 0.008)
            
        conversions = int(clicks * cvr)
        cac = spend / max(1, conversions)
        roas = actual_rev / spend
        
        campaign_records.append({
            "channel": ch,
            "tier": p["target_tier"],
            "current_spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "actual_revenue": round(actual_rev, 2),
            "cac": round(cac, 2),
            "roas": round(roas, 2),
            "cpc": round(cpc, 2),
            "ctr_pct": round(ctr * 100, 2),
            "cvr_pct": round(cvr * 100, 2),
            "saturation_K": k,
            "saturation_S_half": s_half,
            "saturation_n": n
        })
        
    df_campaigns = pd.DataFrame(campaign_records)
    df_campaigns.to_csv(os.path.join(output_dir, "channel_performance.csv"), index=False)
    
    # 2. P&G Consumer Household Cohorts Dataset (5,000 households)
    n_households = 5000
    household_ids = [f"PG-HH-{10000 + i}" for i in range(n_households)]
    
    weights = df_campaigns["conversions"] / df_campaigns["conversions"].sum()
    primary_channels = np.random.choice(channels, size=n_households, p=weights)
    assigned_brands = np.random.choice(brands, size=n_households)
    
    # Household LTV Profiles (12-Month spend across P&G brand portfolio, repeat buying)
    ltv_profiles = {
        "Amazon Ads (Retail Media)": {"mean": 380, "std": 90, "churn_rate": 0.12, "margin": 0.62},
        "Walmart Connect & Retail Media": {"mean": 340, "std": 80, "churn_rate": 0.14, "margin": 0.60},
        "Google Shopping & Search": {"mean": 290, "std": 70, "churn_rate": 0.18, "margin": 0.64},
        "P&G Good Everyday Rewards CRM": {"mean": 420, "std": 95, "churn_rate": 0.08, "margin": 0.72},
        "Meta Social (IG / FB Reels)": {"mean": 240, "std": 60, "churn_rate": 0.22, "margin": 0.58},
        "Connected TV & YouTube Video": {"mean": 210, "std": 50, "churn_rate": 0.26, "margin": 0.56},
        "TikTok Creator & Influencer": {"mean": 115, "std": 35, "churn_rate": 0.46, "margin": 0.48},
        "Programmatic Open-Web Display": {"mean": 65, "std": 22, "churn_rate": 0.64, "margin": 0.42},
    }
    
    customer_records = []
    
    for hid, ch, br in zip(household_ids, primary_channels, assigned_brands):
        prof = ltv_profiles[ch]
        # Multi-touch path simulation (1 to 4 touchpoints)
        path_length = np.random.choice([1, 2, 3, 4], p=[0.38, 0.36, 0.18, 0.08])
        if path_length == 1:
            touchpoints = [ch]
        else:
            assists = list(np.random.choice(channels, size=path_length - 1, replace=True))
            touchpoints = assists + [ch]
            
        ltv = max(30.0, np.random.normal(prof["mean"], prof["std"]))
        churn = np.random.rand() < prof["churn_rate"]
        gross_margin = ltv * prof["margin"]
        annual_orders = max(1, int(ltv / np.random.uniform(25, 45)))
        acquisition_cost = df_campaigns.loc[df_campaigns["channel"] == ch, "cac"].values[0]
        
        net_profit = gross_margin - acquisition_cost
        is_profitable = net_profit > 0
        
        customer_records.append({
            "household_id": hid,
            "brand_category": br,
            "first_touch": touchpoints[0],
            "last_touch": touchpoints[-1],
            "touchpoints_path": " > ".join(touchpoints),
            "num_touchpoints": len(touchpoints),
            "acquisition_channel": ch,
            "ltv": round(ltv, 2),
            "gross_margin": round(gross_margin, 2),
            "acquisition_cost": round(acquisition_cost, 2),
            "net_profit": round(net_profit, 2),
            "is_profitable": is_profitable,
            "churned": churn,
            "annual_orders": annual_orders,
            "payback_months": round(max(0.6, (acquisition_cost / (gross_margin / 12))), 1)
        })
        
    df_customers = pd.DataFrame(customer_records)
    df_customers.to_csv(os.path.join(output_dir, "customer_conversions.csv"), index=False)
    
    total_spend = sum(current_spends.values())
    total_revenue = df_campaigns["actual_revenue"].sum()
    blended_roas = total_revenue / total_spend
    
    print(f"[P&G Data Generator] Created dataset for Procter & Gamble in '{output_dir}'.")
    print(f"P&G Channels: {len(channels)} | Monthly Marketing Budget: ${total_spend:,.2f}")
    print(f"Current Gross Revenue: ${total_revenue:,.2f} | Blended ROAS: {blended_roas:.2f}x")
    print(f"Consumer Household Records: {len(df_customers):,} rows")
    
    return df_campaigns, df_customers

if __name__ == "__main__":
    generate_marketing_data()
