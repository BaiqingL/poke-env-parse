from poke_env.environment import Battle
import logging

class BattleSimulator(Battle):
    def __init__(self, battle_tag: str, log_file_path: str):
        # give it a logger
        logger = logging.getLogger(__name__)
        self.turn = 0
        self.p1 = None 
        self.p2 = None
        self.winner = ""
        self.turn_logs = {}
        self.log_file_path = log_file_path
        self.parse_message_commands = [
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
        super().__init__(battle_tag=battle_tag, username=self.winner, gen=9, logger=logger)
    def _parse_log_find_winner(self):
        current_turn = 0

        with open(self.log_file_path, 'r') as log_file:
            for line in log_file:
                line = line.strip()
                if line.startswith('|'):
                    split_message = line.split('|')[1:]
                    if split_message[0] == 'turn':
                        current_turn = int(split_message[1])
                    if current_turn not in self.turn_logs:
                        self.turn_logs[current_turn] = []
                    if split_message[0] == "win":
                        self.winner = split_message[1]
                    self.turn_logs[current_turn].append(split_message)
            log_file.close()
    
    def _register_player_pokemons(self):
        print("Registering player pokemons")
        for _, messages in self.turn_logs.items():
            for split_message in messages:
                if split_message[0] == "switch" and split_message[1].startswith(self._player_role):
                    self.get_pokemon(split_message[1], details=split_message[2], force_self_team=True)
                if split_message[0] == "move" and split_message[1].startswith(self._player_role):
                    pokemon, move, presumed_target = split_message[1:4]
                    self.get_pokemon(pokemon)._add_move(move)

    def simulate_new_turn(self):
        if self.turn >= len(self.turn_logs):
            self._finish_battle()
            return False

        print(f"Turn {self.turn}")
        messages = self.turn_logs[self.turn]

        # print out the player pokemons
        for pokemon in self.team.values():
            print(pokemon.moves)

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
    battleSimulator = BattleSimulator("log_battle_1", "replay.log")
    while battleSimulator.simulate_new_turn():
        pass
