
import pandas as pd
df = pd.read_parquet("electricity_usage.parquet")

print(df['YYYYMMDD'].max())

output_df = df[df['YYYYMMDD'] != df['YYYYMMDD'].max()]
print(output_df['YYYYMMDD'].max())

output_df.to_parquet("electricity_usage.parquet", index=False)
