# analysis.py
import pandas as pd
import json

class Analysis:
    def __init__(self, df):
        self.df = df.copy()  # make a copy so we don't accidentally mutate the original

    def compute_weekly_kpis(self, output_path="weekly_kpis.csv"):
        """
        Compute KPIs aggregated by week from ticket_open_time:
        - avg_response_seconds
        - avg_resolution_minutes
        - total_tickets
        - percent_response_sla_pass
        - percent_resolution_sla_pass
        """
        # Ensure ticket_open_time is datetime
        self.df['ticket_open_time'] = pd.to_datetime(self.df['ticket_open_time'])

        # Extract year-week for grouping
        self.df['year_week'] = self.df['ticket_open_time'].dt.strftime('%Y-%U')

        # Compute weekly KPIs
        weekly_kpis = self.df.groupby('year_week').agg(
            avg_response_seconds=('response_seconds', 'mean'),
            avg_resolution_minutes=('resolution_minutes', 'mean'),
            total_tickets=('report_id', 'count'),
            percent_response_sla_pass=('response_status', lambda x: (x=="Passed").mean() * 100),
            percent_resolution_sla_pass=('resolution_escalation', lambda x: (x=="passed").mean() * 100)
        ).reset_index()

        # Save to CSV
        weekly_kpis.to_csv(output_path, index=False)
        print(f"Weekly KPIs saved to {output_path}")
