from typing import Tuple, List
from battle_simulator import BattleOrder
import pandas as pd
from poke_env.environment.battle import Battle
from battle_simulator import BattleSimulator
from javascript import require
import json, requests
move_effects = pd.read_csv("data/moves.csv")
item_lookup = json.load(open("data/items.json"))
random_sets = requests.get(
            "https://pkmn.github.io/randbats/data/gen9randombattle.json"
        ).json()

def find_potential_random_set(team_data):
        for pokemon in team_data.keys():
            pokemon_name = team_data[pokemon]["name"].strip().lower()
            if pokemon_name in random_sets.keys():
                known_moves = team_data[pokemon]["moves"]
                possible_sets = random_sets[pokemon_name]["roles"]
                for role in possible_sets:
                    if isinstance(known_moves, dict):
                        known_moves = set(known_moves.keys())
                    if known_moves.issubset(possible_sets[role]["moves"]):
                        # also grab the evs and ivs for the pokemon
                        if "evs" in possible_sets[role]:
                            team_data[pokemon]["evs"] = possible_sets[role]["evs"]
                        if "ivs" in possible_sets[role]:
                            team_data[pokemon]["ivs"] = possible_sets[role]["ivs"]

                        potential_moveset = possible_sets[role]["moves"]
                        seen_unseen_moves = dict()
                        for move in potential_moveset:
                            if move in known_moves:
                                seen_unseen_moves[move] = "seen"
                            else:
                                seen_unseen_moves[move] = "unseen"
                        team_data[pokemon]["moves"] = seen_unseen_moves

                        break
        return team_data
    
def find_move_effect(move_name: str, move_effects: pd.DataFrame):
    move_effect = move_effects.loc[move_effects["name"] == move_name]
    if move_effect.empty:
        return None
    # tf is this
    return list(move_effect.to_dict()["effect"].values())[0]

def get_team_data(battle: Battle, opponent: bool = False) -> dict:
    result = {}
    if not opponent:
        team = battle.team
    else:
        team = battle.opponent_team
    for pokemon in team.values():
        result[pokemon.species] = {
            "moves": {},
            "hp": pokemon.current_hp,
            "ability": pokemon.ability,
            "fainted": pokemon.fainted,
            "item": item_lookup.get(pokemon.item, ""),
            "tera": (
                pokemon.tera_type.name.lower().capitalize()
                if pokemon.terastallized
                else ""
            ),
            "name": pokemon._data.pokedex[pokemon.species]["name"],
            "boosts": pokemon.boosts,
            "level": pokemon.level,
        }
        for move in pokemon.moves.keys():
            result[pokemon.species]["moves"][pokemon.moves[move].entry["name"]] = {
                "type": pokemon.moves[move].entry["type"],
                "accuracy": pokemon.moves[move].entry["accuracy"],
                "secondary effect": pokemon.moves[move].entry.get(
                    "secondary", None
                ),
                "base power": pokemon.moves[move].entry["basePower"],
                "category": pokemon.moves[move].entry["category"],
                "priority": pokemon.moves[move].entry["priority"],
                "effect": find_move_effect(
                    pokemon.moves[move].entry["name"], move_effects
                ),
            }
    return result
def calculate_damage(
        atkr: dict,
        defdr: dict,
        move_used,
        opponent: bool = False,
        log: bool = False,
    ):

        # remove key evasion and accuracy from boosts
        if "evasion" in atkr["boosts"]:
            del atkr["boosts"]["evasion"]
        if "accuracy" in atkr["boosts"]:
            del atkr["boosts"]["accuracy"]
        if "evasion" in defdr["boosts"]:
            del defdr["boosts"]["evasion"]
        if "accuracy" in defdr["boosts"]:
            del defdr["boosts"]["accuracy"]
        damage_calc = require("@smogon/calc")
        generation = damage_calc.Generations.get(9)
        attacker = None
        defender = None
        atkr_attributes = {}
        if "level" in atkr:
            atkr_attributes["level"] = atkr.get("level")
        if "item" in atkr:
            atkr_attributes["item"] = atkr.get("item")
        if "boosts" in atkr:
            atkr_attributes["boosts"] = atkr.get("boosts")
        if "tera" in atkr:
            atkr_attributes["teraType"] = atkr.get("tera")
        if "item" in atkr:
            atkr_attributes["item"] = atkr.get("item")
        if "evs" in atkr:
            atkr_attributes["evs"] = atkr.get("evs")
        if "ivs" in atkr:
            atkr_attributes["ivs"] = atkr.get("ivs")
        defdr_attributes = {}
        if "level" in defdr:
            defdr_attributes["level"] = defdr.get("level")
        if "item" in defdr:
            defdr_attributes["item"] = defdr.get("item")
        if "boosts" in defdr:
            defdr_attributes["boosts"] = defdr.get("boosts")
        if "tera" in defdr:
            defdr_attributes["teraType"] = defdr.get("tera")
        if "item" in defdr:
            defdr_attributes["item"] = defdr.get("item")
        if "evs" in defdr:
            defdr_attributes["evs"] = defdr.get("evs")
        if "ivs" in defdr:
            defdr_attributes["ivs"] = defdr.get("ivs")
        try:
            attacker = damage_calc.Pokemon.new(
                generation, atkr.get("name"), atkr_attributes
            )
        except:
            attacker = damage_calc.Pokemon.new(
                generation, atkr.get("name").split("-")[0], atkr_attributes
            )
        try:
            defender = damage_calc.Pokemon.new(
                generation, defdr.get("name"), defdr_attributes
            )
        except:
            defender = damage_calc.Pokemon.new(
                generation, defdr.get("name").split("-")[0], defdr_attributes
            )
        move = damage_calc.Move.new(generation, move_used)

        result = damage_calc.calculate(generation, attacker, defender, move)
        if log:
            print("Attacker: ", attacker)
            print("Defender: ", defender)
            print("Defender HP: ", defender.originalCurHP)
            print("Move: ", move)
            print("RESULT: ", result)
        if result.damage == 0:
            return 0, 0
        if isinstance(result.damage, str):
            return result.damage + "%", result.damage + "%"
        try:
            if isinstance(result.damage, int):
                min_dmg = result.damage
                max_dmg = result.damage
            else:
                dmg_range = result.damage.valueOf()

                min_dmg = min(dmg_range)
                max_dmg = max(dmg_range)
        except:
            print("INPUTS: ", atkr.get("name"), defdr.get("name"), move_used)
            print(atkr)
            print(defdr)
            print("ERROR: ", result.damage)
            print("DMG RANGE: ", dmg_range)

        # calculate the percentage of damage
        hp = defdr.get("hp")
        if log:
            print("DEFENDER HP Ratio: ", hp)
            print("MIN DMG: ", min_dmg)
            print("MAX DMG: ", max_dmg)
            print("MOVE USED: ", move_used)
        if hp == 0:
            return "100%", "100%"
        if hp == None:
            hp = defdr.get("maximum hp")
        if opponent:
            min_dmg_percent = int(
                min_dmg / (defender.originalCurHP * (hp / 100.0)) * 100
            )
            max_dmg_percent = int(
                max_dmg / (defender.originalCurHP * (hp / 100.0)) * 100
            )
        else:
            min_dmg_percent = int(min_dmg / hp * 100)
            max_dmg_percent = int(max_dmg / hp * 100)
        return str(min_dmg_percent) + "%", str(max_dmg_percent) + "%"

def produce_question_prompt(scenario: str, winner_move: Tuple[BattleOrder, bool], available_orders: List[BattleOrder], winner_pokemon: str, loser_pokemon: str, player_moves_impact: List[Tuple[str, Tuple[str, str]]], opponent_moves_impact: List[Tuple[str, Tuple[str, str]]]) -> str:
    # https://www.reddit.com/r/stunfisk/comments/801dxo/the_ultimate_guide_to_random_battles/
    strategy_prompt = """It's really important to know things like what different items do, what different abilities Pokemon have, the moves that are in the game and what those moves do, their accuracies and power and their effects, and knowing as best you can the Pokemon type weaknesses chart. All this stuff you can look up either in Google or in the Pokemon interface, but remember that in a Showdown battle you are on the clock. If you spend too much time looking up things, you're not going to have enough time to be present strategizing in combat. So the more stuff you can memorize ahead of time, the more helpful it's going to be for your actual battles.
Random Battles is unique in that it purely measures battling skill as players have no control over their teams. In other tiers, the viability of teams will affect players' win-loss records, but in Random Battles, everyone is on an even playing field. Many argue against the competitiveness of Random Battles by pointing out how the random factor can either bring a good or bad matchup, making player skill level hard to determine. This is a good point, but it only holds true for each individual battle. Given the law of large numbers, in the long run everyone will get similar amounts of good and bad matchups and everyone will get haxed the same amount. So eventually, players will be placed on the ladder accordingly with their skill level. The ladder itself proves this, because for example the top 30 has the same names floating around, which shows rankings aren't entirely decided by luck of the draw.
Random Battles is also easy to play on the go which makes it a convenient pastime. If players are on a device that does not have their teams in it and they are looking for some quick battles, Random Battles is there to quench that thirst. It is also not an official tier like VGC or Smogon's OU, so it's easy to not get too invested in it, resulting in less frustration.
The gameplay of Random Battles is notably different from usual tiers due to the following changes:
Every Pokemon has a neutral nature and has 504 EVs spread evenly across the board, making for 84 EVs in each stat. There is one exception for Pokemon that carry Trick Room which is that their Speed gets 0 EVs, but their other stats still have 84 EVs each. All Pokemon get perfect 31 IVs across the board, and Trick Room Pokemon are not exempt from this.
Movesets are randomised so Pokemon don't always get the best sets. They aren't entirely random, but rather are any combo of four from moves each Pokemon runs. So, it is possible to get a Nasty Plot Infernape with 3 physical attacks, or perhaps a Chansey with no Softboiled or Wish.
Unlike other tiers, teams aren't entirely visible from the get go. Instead, Pokemon are only revealed as they are sent out. This opens up quite a few battling strategies which are discussed below.
A win condition is best defined as something that can take down multiple Pokemon, usually ending up winning the game. These are usually Pokemon with set up moves because through boosting their stats to supernatural levels, they can blow through the opponent's team. On the other hand, they could be very bulky Pokemon that the opponent cannot take down. These Pokemon can gradually win the game by chipping away with weak attacks or using moves like Toxic, while recovering health whenever necessary.
The above definitions only fit for general cases however, because technically any Pokemon can be a win condition. For example, you have a Rhyperior, Virizion, and Leavanny remaining while your opponent has a Talonflame and a Mega Glalie. In this case, Rhyperior is the win condition because without it, Talonflame will just destroy Virizion and Leavanny, giving your opponent an easy win.
So, in a situation where Rhyperior is out against Mega Glalie, it is better to sack the Leavanny as it beats neither Mega Glalie or Talonflame. It is never acceptable to sack Rhyperior just because Virizion and Leavanny can't switch into Mega Glalie. After sacking Leavanny, Virizion can be sent out to Close Combat and finish off the Mega Glalie, or perhaps Stone Edge the incoming Talonflame if prediction is necessary or desired.
There are two main tips for playing around the lack of team preview. Further ones are discussed in the advanced tips section. Both main tips relate to win conditions, but in practice can be applied to any Pokemon that seems like it can cause a lot of trouble to the opponent.
The first tip is to hide win conditions unless it is absolutely necessary to send them out. The benefit of hiding win conditions is that your opponent may end up sacking their check or counter to it. To demonstrate, you have a Geomancy Xerneas which is walled by the opponent's Chansey. If your opponent has yet to see your Xerneas, they may end up sacking the Chansey because they feel they can afford to, or a situation in the battle has pressured it. However, if Xerneas was revealed, your opponent will be a lot more conservative with the Chansey, ensuring it is healthy enough to check Xerneas. This method exploits team preview by revealing as little of your team as possible.
The second tip is a counterpart to the first, which is trying to expose as much of the opponent's team as possible. This is normally achieved as the battle is played out, but using phasing moves such as Dragon Tail and Whirlwind can help. Laying up hazards can also help as Toxic Spikes forces the opponent to send out a Poison type, while other hazards such as Stealth Rock force out their hazard clearer. The advantage of this tip is that by exposing your opponent's team, you may identify further win conditions, and / or when your primary win condition can be sent out.
Win conditions have been discussed a lot so it may seem battle plans should be entirely focussed around them as soon as they are identified, but this couldn't be further from the truth. Often, as the battle plays out, the primary win condition may no longer be needed because another one has been discovered. Going off the previous example, Chansey may be preventing that Xerneas from sweeping, but now Hitmonchan finishes off the opponent's Chansey, Cacturne, and Tyranitar. In this case, it is fine to sack or play aggressively with the Xerneas should a situation demand it.
Due to the endless permutations, it is not possible to give advice that covers what the best play is for every single turn. Nonetheless, a point to take from the previous paragraph is that players should be mindful of all the situational changes that occur in every turn. Identifying and playing to win conditions works as a general strategy, but individual initiative is needed to determine when the plan can be changed or dismissed.
Hazards are paramount in any tier, but their importance is even greater in Random Battles due to the heavily switching focused nature of the format, and the good chance that the opponent has no hazard removal. It is advised to make it a priority to get them up as soon as possible, but not to set them up at every single opportunity. Sometimes recovering health or dishing out damage will be more important, and only basic battling experience is needed to determine this.
Status moves are fantastic in Random Battles because they are very spammable, which is highly appreciated in a format where the opponent's team isn't shown. When to use them should be obvious enough, but for the sake of a little in-depth advice, they're good to use when it's obvious the opponent will switch out. For instance, Hippowdon is out against a Magcargo. It's near certain that the Magcargo will switch out in fear of Earthquake, so it's better to use Toxic with the Hippowdon to punish the incoming check by putting it on a timer.
Advanced tips are best described as something players can do when they are very focused and not just playing on auto-pilot. If they are correctly applied, players can gain very discrete advantages.
A double down occurs when both Pokemon on the field faint in the same turn. For example, Garchomp takes down Heatran with Earthquake but also faints to recoil from its Life Orb. Not knowing the opponent's Pokemon may tempt players to randomly select which Pokemon to send out, but there are advantages to be gained with smart selecting. This can be achieved by sending out a Pokemon that has its weaknesses covered. To demonstrate, you have a Landorus-T and a Xurkitree. If Landorus-T is sent out, it can be threatened and forced out by Ice and Water type Pokemon. Xurkitree resists neither of these types, so it will have to take considerable damage upon switching in. However, if Xurkitree was sent out and a Ground type Pokemon threatens and forces it out, Landorus-T gets a free switch in thanks to its immunity. In this case, neither Pokemon will have to take damage. Following this rule will result in far more favourable situations in a scenario that most players think is down to luck.
Of course, there will be situations where no Pokemon has its weaknesses covered. In such situations, it is best to send out a Pokemon that has already been revealed to the opponent as this gains the advantage of hiding your team. The benefits of this are already stated in the basic tips section. In the rarer case of all revealed Pokemon being fainted and no Pokemon having its weaknesses covered, it's best to follow the rules of hiding win conditions / stronger Pokemon and sending out the most disposable Pokemon. However, there is a danger of the weaker / more disposable Pokemon being set up bait to an incoming sweeper, so Pokemon that carry Taunt, status or phasing moves are favoured. It is not possible to know which Pokemon your opponent will send out however, so there is still an element of luck involved.
These strategies are the more advanced ways to play around no team preview that were mentioned in the basic tips section.
Some very crucial information can be gathered about the opponent's movesets if the moves they use are noted each turn. For instance, your boosted Dragon Dance Salamence is about to sweep but your opponent sends out Mamoswine, forcing a switch out in fear of Ice Shard. Upon switching out, if the opponent does not use Ice Shard, and instead goes for Icicle Crash, it's very likely that the Mamoswine does not have Ice Shard. Thus, the next time Salamence boosts with Dragon Dance and Mamoswine is sent out, you should be free to finish it off rather than switching out. This is just one example upon many, so using this tactic can open up many other ways to win that would otherwise be unconsidered.
Observing how the opponent switches can also yield significant information, particularly with deciding which Pokemon is a threat to their team. As an example, Choice Specs Heliolisk is out against the opponent's Golduck. Instead of switching in a Pokemon that resists Electric, the opponent sacks Golduck to Thunderbolt. This indicates that the opponent either has no Electric resists or no checks to Heliolisk, so it can be ascertained that Heliolisk is a massive threat and thus a win condition. Furthermore, if you have another Electric type like Raikou, then it can be determined that it also is a threat as it is quite similar to Heliolisk. In this situation, Heliolisk and Raikou should pretty much guarantee a win because as one punches holes in the opponent's team, the other should have no problem cleaning up. So, in a nutshell, if the opponent doesn't switch in a Pokemon that has a type advantage against the one you currently have in play, you can determine that that Pokemon is a threat, or that the type of that Pokemon threatens your opponent's team.
Generation 9 introduces Terastallization, which lets your Pokemon transform in the middle of battle from its current typing into its Tera type. This adds a new layer of depth to Gen 9 battles. Tera typing can be super useful for things such as setting up STAB moves for that Tera type, setting up your Terablast users, or resisting a predicted attack you know your opponent is going to use."""

    type_effectiveness_prompt = """
Type      | Strong Against         | Weak To
----------|------------------------|------------------
Normal    | -                      | Fighting
Fire      | Grass, Ice, Bug, Steel | Water, Ground, Rock
Water     | Fire, Ground, Rock     | Electric, Grass
Electric  | Water, Flying          | Ground
Grass     | Water, Ground, Rock    | Fire, Ice, Poison, Flying, Bug
Ice       | Grass, Ground, Flying, | Fire, Fighting, Rock, Steel
          | Dragon                 |
Fighting  | Normal, Ice, Rock,     | Flying, Psychic, Fairy
          | Dark, Steel            |
Poison    | Grass, Fairy           | Ground, Psychic
Ground    | Fire, Electric, Poison,| Water, Grass, Ice
          | Rock, Steel            |
Flying    | Grass, Fighting, Bug   | Electric, Ice, Rock
Psychic   | Fighting, Poison       | Bug, Ghost, Dark
Bug       | Grass, Psychic, Dark   | Fire, Flying, Rock
Rock      | Fire, Ice, Flying, Bug | Water, Grass, Fighting, Ground, Steel
Ghost     | Psychic, Ghost         | Ghost, Dark
Dragon    | Dragon                 | Ice, Dragon, Fairy
Dark      | Psychic, Ghost         | Fighting, Bug, Fairy
Steel     | Ice, Rock, Fairy       | Fire, Fighting, Ground
Fairy     | Fighting, Dragon, Dark | Poison, Steel
"""

    question_prompt = """Imagine you're an expert Pokemon Showdown player analyzing a random battle. I'll provide you with a scenario from a Gen 9 random battle, including details about both teams, the current field conditions, and the move that was just made. I want you to explain why the player likely chose that specific move.
In your response, please:

Start with a brief overview of the situation.
Break down your reasoning step-by-step, consider the following tips for analyzing the situation:
[STRATEGY PROMPT]

Consider type advantages, the alternative moves the player could have made and why they might have been rejected.
Conclude with a summary of why this move was likely the best choice in this situation.

Here's the type effectiveness chart:
[TYPE EFFECTIVENESS CHART]

Here's the scenario:

[SCENARIO]

Here is the impact of the player's [WINNER_POKEMON] moves and the hp range that the move will do:
[PLAYER_MOVES_IMPACT]

Here is the impact of the opponent's [LOSER_POKEMON] moves and the hp range that the move will do:
[OPPONENT_MOVES_IMPACT]

The winner's active Pokemon is [WINNER_POKEMON]. They had the following choices:
[WINNER_CHOICES]

The winner chose to do the following:
[WINNER_MOVE]

Format your response in the following way:

<Summary>

<Analysis>

<Conclusion>
Given the above information, I would recommend to do xyz

Respond as if you don't know what move the player chose, and you managed to analyze the situation to arrive at the conclusion.
However, if the pokemon fainted you should acknowledge it by saying "Since the Pokemon fainted, the winner chose to sent out xyz because of abc"""


    available_orders_prompt = ""
    for i, order in enumerate(available_orders):
        available_orders_prompt += f"{i}. {str(order)}\n"
    result = question_prompt.replace("[STRATEGY PROMPT]", strategy_prompt).replace("[SCENARIO]", scenario).replace("[TYPE EFFECTIVENESS CHART]", type_effectiveness_prompt).replace("[WINNER_POKEMON]", winner_pokemon).replace("[LOSER_POKEMON]", loser_pokemon).replace("[WINNER_CHOICES]", available_orders_prompt)
    if not winner_move[1]:
        result = result.replace("[WINNER_MOVE]", str(winner_move[0]))
    else:
        result = result.replace("[WINNER_MOVE]", "Since the Pokemon fainted, we cannot determine the exact move they used. However, the winner chose to swap in " + str(winner_move[0].order.species) + ".")
    
    player_moves_impact_prompt = ""
    for move in player_moves_impact:
        player_moves_impact_prompt += f"{move[0]}: {move[1][0]} - {move[1][1]}\n"
    result = result.replace("[PLAYER_MOVES_IMPACT]", player_moves_impact_prompt)
    opponent_moves_impact_prompt = ""
    for move in opponent_moves_impact:
        opponent_moves_impact_prompt += f"{move[0]}: {move[1][0]} - {move[1][1]}\n"
    result = result.replace("[OPPONENT_MOVES_IMPACT]", opponent_moves_impact_prompt)
    return result
if __name__ == "__main__":
    import pandas as pd
    from battle_simulator import BattleSimulator
    from tqdm import tqdm
    
    # Read from the parquet file
    df = pd.read_parquet("data/battle_logs.parquet")
    
    # Initialize a new column for prompts
    df['prompts'] = [[] for _ in range(len(df))]
    
    # Iterate through each row in the dataframe
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Generating prompts"):
        try:
            # Create a BattleSimulator instance with the log content from the current row
            battleSimulator = BattleSimulator(f"log_battle_{index}", row['log_content'])
            
            # Parse the battle turn by turn and produce a question prompt for each turn
            turn_count = 0
            question_prompts = []
            while battleSimulator.simulate_new_turn():
                player_team = get_team_data(battleSimulator)
                opponent_team = find_potential_random_set(
                    get_team_data(battleSimulator, opponent=True)
                )
                player_moves_impact = []
                for move in battleSimulator.active_pokemon.moves.keys():
                    player_moves_impact.append(
                        (
                            move,
                            calculate_damage(
                                player_team[battleSimulator.active_pokemon.species], 
                                opponent_team[battleSimulator.opponent_active_pokemon.species], 
                                move, 
                                opponent=True
                            ),
                        )
                    )
                opponent_moves_impact = []
                for move in battleSimulator.opponent_active_pokemon.moves.keys():
                    opponent_moves_impact.append(
                        (
                            move,
                            calculate_damage(
                                opponent_team[battleSimulator.opponent_active_pokemon.species], 
                                player_team[battleSimulator.active_pokemon.species], 
                                move, 
                                opponent=False
                            ),
                        )
                    )
                # Produce the question prompt for the current turn
                try:
                    question_prompt = produce_question_prompt(
                        battleSimulator.get_scenario(), 
                        battleSimulator.player_decision[turn_count], 
                        battleSimulator.get_available_orders(), 
                        battleSimulator.active_pokemon.species, 
                        battleSimulator.opponent_active_pokemon.species, 
                        player_moves_impact, 
                        opponent_moves_impact
                    )
                    question_prompts.append(question_prompt)
                except KeyError:
                    break
                turn_count += 1
            
            # Store the prompts for this battle in the dataframe
            df.at[index, 'prompts'] = question_prompts
        except Exception as e:
            print(f"Error processing row {index}: {str(e)}")
            continue
    
    # Save the updated dataframe back to a parquet file
    df.to_parquet("data/battle_logs_with_prompts.parquet")