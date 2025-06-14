
import pandas as pd
df = pd.read_parquet("gas_usage.parquet")

print(df['YYYYMMDD'].max())

output_df = df[df['YYYYMMDD'] != df['YYYYMMDD'].max()]
print(output_df['YYYYMMDD'].max())

output_df.to_parquet("gas_usage.parquet", index=False)
