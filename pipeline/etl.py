import pandas as pd
import logging
from typing import List, Dict
import os
import numpy as np
import json

logging.basicConfig(format = '%(levelname)s : %(message)s', level = logging.DEBUG)

class ETL:
    def __init__(self):
        self.dataframes:Dict[str, pd.DataFrame] = {}

    def load_tables(self, paths: List[str], stop_on_error:bool) -> Dict[str, pd.DataFrame]:
        for filepath in paths:
            # Get the folder where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(script_dir, filepath)
            try:
                # name = filepath[(filepath.rfind("/") + 1):(filepath.find("."))]
                filename = os.path.basename(filepath)   # channel_type.csv
                name = os.path.splitext(filename)[0]  # channel_type
                df = pd.read_csv(filepath)
                self.dataframes[name] = df

            except Exception as e:
                logging.error(f"Error occured whilst loading {filepath}: {e}")

                # if the user wants to stop on the account of an error,the break out from the loop on the account of that error
                if stop_on_error:
                    break 

                else: # Else, continue to run the loop
                    continue

        # return the dataframes that have been loaded in     
        return self.dataframes

    def parse_datetime_columns(self, df):
        for col in df.columns:
            if "Time" in col:
                df[col] = pd.to_datetime(df[col].str.strip(), errors = 'coerce')
                if df[col].isna().any():
                    df.dropna(subset = [col], inplace = True)

        df.dropna(subset = ['Report ID'], inplace = True)
        df["Fault Type"].fillna("Not Specified", inplace = True)


    # Important validation befor extracting Service Code from the service_data
    def enricher(self, dfs: Dict[str, pd.DataFrame]):
        report_ids = dfs["service_data"]["Report ID"]
        if (report_ids.str.contains("-").all()) and (report_ids.str.split("-").str.len() >= 4).all():

            # Extract Service Code safely
            dfs["service_data"]['Service Code'] = report_ids.str.split("-",expand = True)[3]

        else:
            raise Exception("Invalid Report ID format — cannot extract Service Code.")  

        # Left Join
        df = pd.merge(
            dfs["service_data"],dfs['channel_type'], 
            left_on = "Report Channel", right_on = "Channel Key",
            how = "left")
        
        df = pd.merge(df,dfs['service_type'], on = "Service Code", how = "left")

        df = pd.merge(
            df,dfs['employee'],
            left_on = "Operator", right_on = "Employee_name", 
            how = "left")
        
        df = pd.merge(
            df,dfs['location'],
            on = "State Key",
            how = "left")

        # Drop redundant columns
        cols_to_drop = ["Operator", "Service Code", "Report Channel","Zone Desc"]
        df.drop(
            columns = [col for col in cols_to_drop if col in df.columns], 
            inplace = True
            )

        # Normalize column Names
        df.columns = df.columns.str.replace(" ","_").str.lower()
        df.rename(columns = {"empoyee_id":"employee_id"},inplace = True)

        # Drop duplicates
        df_cleaned = df.drop_duplicates(subset="report_id")
        df_cleaned.reset_index(drop = True, inplace = True)
        return df_cleaned
    
    def compute_sla_metrics(self, df):
        # time_cols = [col for col in df.columns if "time" in col]
        # df_sla = df[time_cols]

        df["response_seconds"] = round(
            (df["ticket_resp_time"] - df["ticket_open_time"]).dt.total_seconds(),
            2
        )

        df["resolution_minutes"] = round(
            (df["issue_res_time"] - df["ticket_resp_time"]).dt.total_seconds() / 60,
           2
        ) 
        df["response_sla_pass"] = df['response_seconds'].apply(lambda x: 'failed' if x > 10 else "Passed")

        df["resolution_category"] = df['resolution_minutes'].apply(lambda x: "Excellent" if x < 30 else ("Good" if 30 <= x <= 60 else ("Fair" if 60 < x <= 180 else "Critical")))
        
        df["resolution_sla_pass"] = np.where(df["resolution_category"] == 'Critical',"failed","passed")
        
        df_escalation = df[["report_id",'employee_id','designation','manager',"resolution_minutes","resolution_sla_pass","resolution_category"]]
        df_escalation = df_escalation[df_escalation["resolution_sla_pass"] == "failed"]

        df_escalation.to_csv("escalation.csv", index=False)

        return df


    def manager_operator_performance(self, df):
        # Fix typo in column names
        df = df.rename(columns={"empoyee_id": "employee_id", "employee_name": "operator"})

        # -----------------------------
        # OPERATOR PERFORMANCE
        # -----------------------------
        operator_stats = df.groupby("operator").agg({
            "response_seconds": "mean",
            "resolution_minutes": "mean",
            "report_id": "count"
        }).reset_index()

        # Operator response ranking
        operator_response_time_secs_rank = operator_stats[["operator", "response_seconds"]].copy()
        operator_response_time_secs_rank["rank"] = (
            operator_response_time_secs_rank["response_seconds"]
            .rank(ascending=True, method="max")
        )
        operator_response_time_secs_rank = operator_response_time_secs_rank.sort_values("rank")

        # Operator resolution ranking
        operator_resolution_time_minutes_rank = operator_stats[["operator", "resolution_minutes"]].copy()
        operator_resolution_time_minutes_rank["rank"] = (
            operator_resolution_time_minutes_rank["resolution_minutes"]
            .rank(ascending=True, method="max")
        )
        operator_resolution_time_minutes_rank = operator_resolution_time_minutes_rank.sort_values("rank")

        # -----------------------------
        # MANAGER PERFORMANCE
        # -----------------------------
        manager_stats = df.groupby("manager").agg({
            "response_seconds": "mean",
            "resolution_minutes": "mean",
            "report_id": "count"
        }).reset_index()

        # Manager response ranking
        manager_response_time_secs_rank = manager_stats[["manager", "response_seconds"]].copy()
        manager_response_time_secs_rank["rank"] = (
            manager_response_time_secs_rank["response_seconds"]
            .rank(ascending=True, method="max")
        )
        manager_response_time_secs_rank = manager_response_time_secs_rank.sort_values("rank")

        # Manager resolution ranking
        manager_resolution_time_minutes_rank = manager_stats[["manager", "resolution_minutes"]].copy()
        manager_resolution_time_minutes_rank["rank"] = (
            manager_resolution_time_minutes_rank["resolution_minutes"]
            .rank(ascending=True, method="max")
        )
        manager_resolution_time_minutes_rank = manager_resolution_time_minutes_rank.sort_values("rank")

        # Return all results in a dictionary
        return {
            "operator_stats": operator_stats,
            "operator_response_rank": operator_response_time_secs_rank,
            "operator_resolution_rank": operator_resolution_time_minutes_rank,
            "manager_stats": manager_stats,
            "manager_response_rank": manager_response_time_secs_rank,
            "manager_resolution_rank": manager_resolution_time_minutes_rank
        }


    

    def save_manager_operator_report(self, df, output_path="manager_operator_report.json"):
        report = self.manager_operator_performance(df)

        # Convert all DataFrames to dict for JSON serialization
        json_ready_report = {
            key: value.to_dict(orient="records")
            for key, value in report.items()
        }

        # Write to JSON file
        with open(output_path, "w") as f:
            json.dump(json_ready_report, f, indent=4)

        return f"Manager/Operator performance report saved to {output_path}"







def main():
    etl = ETL()
    paths = ["../data/channel_type.csv",
             "../data/employee.csv",
             "../data/fault_type.csv",
             "../data/location.csv",
             "../data/service_data.csv",
             "../data/service_type.csv"]
    dfs = etl.load_tables(paths, False)
    # print("Loaded tables:", list(dfs.keys()))
    # print(dfs["service_data"].head())

    # Print column names to see what is happening before merging
    print("\n--- COLUMN CHECK ---")
    print("SERVICE DATA:", dfs["service_data"].columns.tolist())
    print("EMPLOYEE:", dfs["employee"].columns.tolist())
    print("CHANNEL:", dfs["channel_type"].columns.tolist())
    print("SERVICE TYPE:", dfs["service_type"].columns.tolist())
    print("LOCATION:", dfs["location"].columns.tolist())
    print("---------------------\n")

    etl.parse_datetime_columns(dfs["service_data"])
    # print(dfs["service_data"].info())

    df_enriched = etl.enricher(dfs)
    # print(df_enriched.columns)
    
       # Show merged columns
    print("\n--- MERGED COLUMNS ---")
    print(df_enriched.columns.tolist())
    print("-----------------------")

    df_service_level_aggreements = etl.compute_sla_metrics(df_enriched)
    print(df_service_level_aggreements)

    print("-----------------------")
    performance_reports = etl.manager_operator_performance(df_service_level_aggreements)

    print(etl.save_manager_operator_report(df_service_level_aggreements))

    
    
if __name__ == "__main__":
     main()

     