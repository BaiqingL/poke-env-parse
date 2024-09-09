from poke_env.environment import Battle
import logging

class LogBattle(Battle):
    def __init__(self, battle_tag: str, log_file_path: str):
        # give it a logger
        logger = logging.getLogger(__name__)
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

    def simulate_battle(self):
        for turn, messages in self.turn_logs.items():
            print(f"Turn {turn}")
            # print out the player pokemon names and opponent pokemon names
            print(f"Player {self.player_username} pokemon names:")
            print(self.team.keys())
            
            print(f"Opponent {self.opponent_username} pokemon names:")
            print(self.opponent_team.keys())
            for split_message in messages:

                if split_message[0] in self.parse_message_commands:
                    if split_message[0] == "player" and split_message[1] in ["p1", "p2"]:
                        if split_message[1] == "p1":
                            self.p1 = split_message[2]
                            if split_message[2] == self.winner:
                                self._player_role = "p1"
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

        # After parsing all lines, finish the battle
        self._finish_battle()

# Usage
log_battle = LogBattle("log_battle_1", "replay.log")
log_battle.simulate_battle()
