from poke_env.environment import Battle
from poke_env.player.battle_order import BattleOrder
from poke_env.environment.pokemon import Pokemon
import pandas as pd

import logging
from typing import Dict, List, Optional, Union, Tuple

class BattleSimulator(Battle):
    def __init__(self, battle_tag: str, log_content: str):
        # give it a logger
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARN)
        self.logger.addHandler(logging.StreamHandler())

        self.turn: int = 0
        self.p1: Optional[str] = None 
        self.p2: Optional[str] = None
        self.winner: str = ""
        self.turn_logs: Dict[int, List[List[str]]] = {}
        self.log_content: str = log_content
        self.parse_message_commands: List[str] = [
            "drag", "switch", "-damage", "move", "cant", "turn", "-heal", "-boost",
            "-weather", "faint", "-unboost", "-ability", "-start", "-activate",
            "-status", "rule", "-clearallboost", "-clearboost", "-clearnegativeboost",
            "-clearpositiveboost", "-copyboost", "-curestatus", "-cureteam", "-end",
            "-endability", "-enditem", "-fieldend", "-fieldstart", "-formechange",
            "detailschange", "-invertboost", "-item", "-mega", "-mustrecharge",
            "-prepare", "-primal", "-setboost", "-sethp", "-sideend", "-sidestart",
            "-singleturn", "-singlemove", "-swapboost", "-transform", "-zpower",
            "clearpoke", "gen", "tier", "inactive", "player", "poke", "raw",
            "replace", "start", "swap", "message", "-message", "-immune",
            "-swapsideconditions", "title", "-terastallize"
        ]
        self.player_decision: Dict[int, Tuple[BattleOrder, bool]] = {}
        self._parse_log_find_winner()
        self.logger.info(f"Winner of this battle: {self.winner}")
        super().__init__(battle_tag=battle_tag, username=self.winner, gen=9, logger=self.logger)

    def _parse_log_find_winner(self) -> None:
        current_turn: int = 0

        for line in self.log_content.split('\n'):
            line = line.strip()
            if line.startswith('|'):
                split_message: List[str] = line.split('|')[1:]
                if split_message[0] == 'turn':
                    current_turn = int(split_message[1])
                if current_turn not in self.turn_logs:
                    self.turn_logs[current_turn] = []
                if split_message[0] == "win":
                    self.winner = split_message[1]
                self.turn_logs[current_turn].append(split_message)
    
    def _register_player_pokemons(self) -> None:
        self.logger.info("Registering player pokemons")
        for _, messages in self.turn_logs.items():
            for split_message in messages:
                if split_message[0] == "switch" and split_message[1].startswith(self._player_role):
                    team_key = split_message[1].replace(self._player_role+"a", self._player_role)
                    if team_key not in self._team.keys():  
                        pokemon = self.get_pokemon(split_message[1], details=split_message[2], force_self_team=True)
                        hp = int(split_message[3].split("/")[0])
                        pokemon._current_hp = hp
                        pokemon._max_hp = hp
                        self.logger.info(f"Registered pokemon {pokemon}")
                elif split_message[0] == "move" and split_message[1].startswith(self._player_role):
                    pokemon, move = split_message[1:3]
                    self.get_pokemon(pokemon)._add_move(move)
                    self.logger.info(f"Added move {move} to {pokemon}")
                elif split_message[0] == "-terastallize" and split_message[1].startswith(self._player_role):
                    pokemon, terra_type = split_message[1:3]
                    self.get_pokemon(pokemon)._terastallized_type = terra_type
                    self.logger.info(f"Added terra type {terra_type} to {pokemon}")

    def _parse_player_decision(self, current_turn: int) -> None:
        if current_turn >= len(self.turn_logs) - 1:
            return  # No decision to parse for the last turn

        next_turn_messages = self.turn_logs[current_turn + 1]
        fainted = False
        for message in next_turn_messages:
            if message[0] == "faint" and message[1].startswith(self._player_role):
                fainted = True
                break

        for message in next_turn_messages:
            if message[0] == "move" and message[1].startswith(self._player_role):
                pokemon, move = message[1:3]
                move = move.lower().replace(" ", "").replace("-", "")
                pokemon_obj = self.get_pokemon(pokemon)
                move_obj = pokemon_obj.moves[move]
                self.player_decision[current_turn] = (BattleOrder(move_obj), False)
                return
            elif message[0] == "switch" and message[1].startswith(self._player_role):
                pokemon = message[1].replace(self._player_role+"a", self._player_role)
                switch_pokemon = self.get_pokemon(pokemon)
                self.player_decision[current_turn] = (BattleOrder(switch_pokemon), fainted)
                return

    def simulate_new_turn(self) -> bool:
        if self.turn >= len(self.turn_logs):
            self._finish_battle()
            return False

        self.logger.info(f"Processing turn {self.turn}")
        messages: List[List[str]] = self.turn_logs[self.turn]

        for split_message in messages:
            if split_message[0] in self.parse_message_commands:
                if split_message[0] == "player" and split_message[1] in ["p1", "p2"]:
                    if split_message[1] == "p1":
                        self.p1 = split_message[2]
                        if split_message[2] == self.winner:
                            self._player_role = "p1"
                            self._register_player_pokemons()
                    elif split_message[1] == "p2":
                        self.p2 = split_message[2]
                        if split_message[2] == self.winner:
                            self._player_role = "p2"
                            self._register_player_pokemons()
                    if self.opponent_username is None and split_message[2] != self.winner:
                        self.opponent_username = split_message[2]
                    continue
                elif split_message[0] == "switch":
                    if split_message[1] == "p1a":
                        split_message[1] = self.p1
                    elif split_message[1] == "p2a":
                        split_message[1] = self.p2
                split_message.insert(0, "padding")
                self.parse_message(split_message)

        self._parse_player_decision(self.turn)
        self.turn += 1
        return True
    
    def get_scenario(self) -> str:
        # Return only the parsed logs up to the current turn
        parsed_logs = []
        self.logger.info(f"Parsing logs up to turn {self.turn}")
        for turn in range(self.turn):
            # only extend the parsed logs if the log is supported by parse_message_commands
            for split_message in self.turn_logs[turn]:
                if split_message[0] == "padding" and split_message[1] != "inactive" and split_message[1] != "raw":
                    parsed_logs.append(split_message[1:])
        return "\n".join([" ".join(message) for message in parsed_logs])

    def get_available_orders(self) -> List[BattleOrder]:
        available_orders: List[BattleOrder] = [
            BattleOrder(self.active_pokemon.moves[move]) for move in self.active_pokemon.moves
        ]
        # if the active pokemon's _terastallize type is not None and terra is not active, add the terra move to the available moves
        if self.active_pokemon._terastallized_type is not None and not self.active_pokemon._terastallized:
            for move in self.active_pokemon.moves:
                available_orders.append(BattleOrder(self.active_pokemon.moves[move], terastallize=True))
        # look at the pokemon in the players team, and find the ones that are not fainted or active
        for _, pokemon in self._team.items():
            if pokemon._current_hp > 0 and not pokemon._active:
                available_orders.append(BattleOrder(pokemon))
        return available_orders

if __name__ == "__main__":

    # Read one log from the parquet file
    df = pd.read_parquet("data/battle_logs.parquet")
    log_content = df.iloc[100]['log_content']  # Assuming 'log_content' is the column name containing the battle log
    battleSimulator: BattleSimulator = BattleSimulator("log_battle_1", log_content)
    while battleSimulator.simulate_new_turn():
        print(f"Player's pokemon: {battleSimulator.active_pokemon.species}")

        available_orders = battleSimulator.get_available_orders(battleSimulator)
        available_orders_prompt = ""
        for i, order in enumerate(available_orders):
            available_orders_prompt += f"{i}. {str(order)}\n"
        print(f"Available orders:\n{available_orders_prompt}")
        
        if battleSimulator.turn - 1 in battleSimulator.player_decision:
            decision, fainted = battleSimulator.player_decision[battleSimulator.turn - 1]
            print(f"Player's decision for turn {battleSimulator.turn - 1}: {decision}")
            if fainted:
                print(f"Switch due to fainted Pokemon")