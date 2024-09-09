from poke_env.environment import Battle
import logging
from typing import Dict, List, Optional, Union

class BattleSimulator(Battle):
    def __init__(self, battle_tag: str, log_file_path: str):
        # give it a logger
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())

        self.turn: int = 0
        self.p1: Optional[str] = None 
        self.p2: Optional[str] = None
        self.winner: str = ""
        self.turn_logs: Dict[int, List[List[str]]] = {}
        self.log_file_path: str = log_file_path
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
        self._parse_log_find_winner()
        super().__init__(battle_tag=battle_tag, username=self.winner, gen=9, logger=self.logger)

    def _parse_log_find_winner(self) -> None:
        current_turn: int = 0

        with open(self.log_file_path, 'r') as log_file:
            for line in log_file:
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
            log_file.close()
    
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

        self.turn += 1
        return True

# Usage
if __name__ == "__main__":
    battleSimulator: BattleSimulator = BattleSimulator("log_battle_1", "replay.log")
    while battleSimulator.simulate_new_turn():
        # print out the current state of the battle 
        
        # log out what happened in the turn, like "in turn 1, [player] has active pokemon [pokemon] with [hp]/[max_hp] hp and [opponent] has active pokemon [pokemon] with [hp]/[max_hp] hp"
        print(f"in turn {battleSimulator.turn}, {battleSimulator._player_role} has active pokemon {battleSimulator.active_pokemon.species} with {battleSimulator.active_pokemon.current_hp}/{battleSimulator.active_pokemon.max_hp} hp and {battleSimulator.opponent_active_pokemon.species} has {battleSimulator.opponent_active_pokemon.current_hp}/{battleSimulator.opponent_active_pokemon.max_hp} hp")
        # log out what moves were used in the turn, like "[player] used thunderbolt on [opponent]"
        if battleSimulator.active_pokemon.moves:
            print(f"Players's {battleSimulator.active_pokemon.species} used a move on {battleSimulator.opponent_active_pokemon.species}")
        if battleSimulator.opponent_active_pokemon.moves:
            print(f"Opponent's {battleSimulator.opponent_active_pokemon.species} used a move on {battleSimulator.active_pokemon.species}")