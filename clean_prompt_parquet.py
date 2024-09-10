import pandas as pd
from tqdm import tqdm

# Read the parquet file
df = pd.read_parquet("data/battle_logs_with_prompts.parquet")

# Remove rows where prompts are empty
df_cleaned = df[df['prompts'].apply(lambda x: len(x) > 0)]

# Save to new parquet file with progress bar
df_cleaned.to_parquet("data/battle_logs_with_prompts_cleaned.parquet", engine="pyarrow")

# Print total amount of rows removed
print(f"Total rows removed: {df.shape[0] - df_cleaned.shape[0]}")

# Print total amount of prompts in the dataset
print(f"Total prompts in the dataset: {df_cleaned['prompts'].apply(len).sum()}")