import pandas as pd
from battle_simulator import BattleSimulator
import tempfile
import os
from tqdm import tqdm

# Read the parquet file
df = pd.read_parquet('data/battle_logs.parquet')

# Function to run battle simulator on a single log
def run_simulator(battle_id, log_content):
    # Create a temporary file to store the log content
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(log_content)
        temp_file_path = temp_file.name

    try:
        # Initialize and run the battle simulator
        simulator = BattleSimulator(battle_id, temp_file_path)
        while simulator.simulate_new_turn():
            pass  # Simulate all turns
        print(f"Successfully simulated battle: {battle_id}")
        return True
    except Exception as e:
        print(f"Error simulating battle {battle_id}: {str(e)}")
        return False
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

# List to store successfully processed battles
successful_battles = []

# Iterate through all battles in the dataframe with a progress bar
for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing battles"):
    if run_simulator(row['battle_id'], row['log_content']):
        successful_battles.append(row)

# Create a new DataFrame with only the successful battles
successful_df = pd.DataFrame(successful_battles)

# Save the successful battles to a new parquet file
successful_df.to_parquet('data/processed_battle_logs.parquet')

print(f"Sanity check complete. {len(successful_df)} out of {len(df)} battles have been successfully processed and saved to processed_battle_logs.parquet.")
