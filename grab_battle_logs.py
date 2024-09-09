import pandas as pd
import requests
import json
from tqdm import tqdm

# Read the replays.jsonl file
replays = []
with open('data/replays.jsonl', 'r') as f:
    for line in f:
        replays.append(json.loads(line))

# Create a list to store the data
data = []

# Iterate through the replays and fetch the battle logs
for replay in tqdm(replays, desc="Fetching battle logs"):
    battle_id = replay['id']
    rating = replay['rating']
    
    # Construct the URL for the battle log
    url = f"https://replay.pokemonshowdown.com/{battle_id}.log"
    
    # Fetch the battle log
    response = requests.get(url)
    
    if response.status_code == 200:
        log_content = response.text
        
        # Append the data to our list
        data.append({
            'battle_id': battle_id,
            'rating': rating,
            'log_content': log_content
        })
    else:
        print(f"Failed to fetch log for battle {battle_id}")

# Create a pandas DataFrame
df = pd.DataFrame(data)

# Write the DataFrame to a parquet file
df.to_parquet('data/battle_logs.parquet')

print("Battle logs have been saved to battle_logs.parquet")
