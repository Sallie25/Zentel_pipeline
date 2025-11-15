import pandas as pd
import logging
from typing import List, Dict
import os

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

        return df.head()
    
    def compute_sla_metrics(df):
        pass


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
    
    
if __name__ == "__main__":
     main()

     