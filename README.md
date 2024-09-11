# Pokemon Showdown Replay Parser and Battle Simulator

This project provides tools to parse log files from Pokemon Showdown replays for random battles and simulate the battle step by step. It extracts the best effort information on the winner's team and recreates the battle flow.

## Features

- Parse Pokemon Showdown replay log files
- Extract winner's team information
- Simulate battle progression turn by turn
- Recreate Pokemon states, moves, and effects throughout the battle

## Usage

1. Save a Pokemon Showdown replay as a log file (e.g., `replay.log`).


2. Create a BattleSimulator instance:

```python
battleSimulator = BattleSimulator("log_battle_1", "replay.log")
```

3. Simulate the battle:

```python
while battleSimulator.simulate_new_turn():
    pass
```

During the simulation, you can access the current state of the battle and the Pokémon involved at any point.


## Data Processing Pipeline

The following files are used in sequence to clean and parse the data:

1. `paginated_search.py`: Grabs replays from the replay API and filters out ones with rating < 2200
2. `grab_battle_logs.py`: Grabs the battle logs for the replays
3. `produce_question_prompts.py`: Produces the question prompts for the replays
4. `clean_filter_prompt_parquet.py`: Cleans the prompts for the replays and filters out ones with rating < 2200

Each script builds upon the output of the previous one, creating a streamlined data processing pipeline.

