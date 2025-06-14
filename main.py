# --- file: main.py ---
from data_utils import check_data
from data_utils import plot_summary
import pandas as pd

df = check_data()

# plot_summary(df, plot_type="bar")     # classic bar chart