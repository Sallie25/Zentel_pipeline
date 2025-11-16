"""TODO: dfs is just a dictionary of DataFrames returned by load_tables.

When you call parse_datetime_columns(dfs["service_data"]), you modify that DataFrame in-place, which should affect dfs["service_data"]. ✅

But self.dataframes inside ETL is also holding the same DataFrame object, because dfs = self.dataframes in load_tables.

So technically, in-place changes do propagate, because both dfs["service_data"] and self.dataframes["service_data"] point to the same object.

TODO: Implement this
etl.load_tables(paths, False)
etl.parse_datetime_columns(etl.dataframes["service_data"])
etl.enricher(etl.dataframes)
print(etl.dataframes["service_data"].head())

"""

 # for col in df.columns:
        #     if col.endswith("_x") or col.endswith("_y"):
        #         df.drop(columns = col, inplace = True)