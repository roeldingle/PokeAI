"""
Battle Progression Service Module
Implements Lesson 6 tournament rules and non-stationary AI progression mechanics:
1. Strict 5-Turn Battle Clock enforcement (matches terminate at Turn 5).
2. Pre-Turn 1 TEAM Party Swap validation (disabled when party has only 1 monster).
3. +1% Incremental Stat Mastery Progression per victory:
   effective_stat = round(base_stat * (1.0 + victories_count * 0.01))
4. Milestone Move Slot Unlocks:
   - Move Slot 3 unlocked at 10 victories (+10% stat boost)
   - Move Slot 4 unlocked at 20 victories (+20% stat boost)
5. Automatic opponent recruitment into the trainer's party pool upon knockout within 5 turns.
"""

from typing import Dict, List, Optional
from src.schemas.battle_schema import ActiveBattleEntity, PokemonMoveSlot
from src.schemas.progression_schema import (
    RecruitedPartyMonster,
    TeamSwapResponse,
    TrainerPartyPoolState,
    VictoryProgressionUpdateResponse,
)

# Canonical tournament rule: every battle lasts a maximum of 5 turns
MAXIMUM_BATTLE_TURNS: int = 5

# Milestone victory thresholds for unlocking Move Slot 3 and Move Slot 4
MOVE_SLOT_3_VICTORY_THRESHOLD: int = 10
MOVE_SLOT_4_VICTORY_THRESHOLD: int = 20

# Incremental stat mastery bonus awarded per victory (+1% = 0.01)
INCREMENTAL_VICTORY_STAT_BONUS_RATE: float = 0.01


class BattleProgressionService:
    """
    Manages trainer party pools, monster victory counters, +1% stat progression scaling,
    move slot milestone unlocks, pre-Turn 1 TEAM swaps, and knockout auto-recruitment.
    """

    def __init__(self) -> None:
        # Maps normalized trainer_name -> { pokemon_id: RecruitedPartyMonster }
        self.trainer_party_rosters: Dict[str, Dict[int, RecruitedPartyMonster]] = {}
        # Maps normalized trainer_name -> currently active lead pokemon_id
        self.trainer_active_pokemon_ids: Dict[str, int] = {}

    @staticmethod
    def calculate_stat_progression_multiplier(victories_count: int) -> float:
        """
        Computes the +1% per-victory stat progression multiplier:
        stat_progression_multiplier = 1.0 + (victories_count * 0.01)
        """
        # Clamp negative counts to zero to preserve baseline 1.0x stats
        validated_victories_count = max(0, victories_count)
        # Round to 4 decimal places to eliminate IEEE 754 floating-point drift
        return round(1.0 + (validated_victories_count * INCREMENTAL_VICTORY_STAT_BONUS_RATE), 4)

    @staticmethod
    def calculate_effective_scaled_stat(base_stat_value: int, victories_count: int) -> int:
        """
        Applies the Lesson 6 mathematical progression formula:
        effective_stat = round(base_stat * (1.0 + victories_count * 0.01))
        """
        # Compute multiplier for the monster's cumulative victory count
        progression_multiplier = BattleProgressionService.calculate_stat_progression_multiplier(
            victories_count=victories_count
        )
        # Multiply base stat by progression multiplier and round to nearest integer
        scaled_stat_integer = round(base_stat_value * progression_multiplier)
        # Guarantee every combat stat remains at least 1
        return max(1, int(scaled_stat_integer))

    @staticmethod
    def evaluate_move_slots_for_victories(
        move_slots: List[PokemonMoveSlot],
        victories_count: int,
    ) -> List[PokemonMoveSlot]:
        """
        Evaluates all 4 GBA move slots against the monster's cumulative victory count.
        Unlocks Move Slot 3 at 10 victories and Move Slot 4 at 20 victories.
        """
        updated_move_slots: List[PokemonMoveSlot] = []
        for existing_slot in move_slots:
            # Determine if the monster's victory count meets or exceeds this slot's threshold
            is_slot_unlocked = victories_count >= existing_slot.unlock_victory_threshold
            # Create a fresh copy with updated unlock status and restored PP
            updated_move_slots.append(
                PokemonMoveSlot(
                    move_id=existing_slot.move_id,
                    move_name=existing_slot.move_name,
                    elemental_type=existing_slot.elemental_type,
                    base_power=existing_slot.base_power,
                    accuracy_percentage=existing_slot.accuracy_percentage,
                    current_power_points=existing_slot.maximum_power_points,
                    maximum_power_points=existing_slot.maximum_power_points,
                    is_unlocked=is_slot_unlocked,
                    unlock_victory_threshold=existing_slot.unlock_victory_threshold,
                )
            )
        return updated_move_slots

    def build_baseline_species_template(self, pokemon_id: int) -> RecruitedPartyMonster:
        """
        Creates a baseline (0-victory) RecruitedPartyMonster template for starters
        and recruitable wild monsters with full 4-move progression palettes.
        """
        # Charmander (#4 - Fire Starter)
        if pokemon_id == 4:
            base_moves = [
                PokemonMoveSlot(move_id=1, move_name="Scratch", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=2, move_name="Growl", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=40, maximum_power_points=40, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=3, move_name="Ember", elemental_type="fire", base_power=40, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_3_VICTORY_THRESHOLD),
                PokemonMoveSlot(move_id=4, move_name="Flamethrower", elemental_type="fire", base_power=90, accuracy_percentage=100, current_power_points=15, maximum_power_points=15, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_4_VICTORY_THRESHOLD),
            ]
            return RecruitedPartyMonster(
                pokemon_id=4,
                pokemon_name="Charmander",
                level=6,
                elemental_types=["fire"],
                victories_count=0,
                stat_progression_multiplier=1.0,
                base_health_points=20,
                base_attack_stat=12,
                base_defense_stat=10,
                base_speed_stat=14,
                effective_health_points=20,
                effective_attack_stat=12,
                effective_defense_stat=10,
                effective_speed_stat=14,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/4.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/4.gif",
                move_slots=base_moves,
            )

        # Bulbasaur (#1 - Grass/Poison Starter)
        if pokemon_id == 1:
            base_moves = [
                PokemonMoveSlot(move_id=5, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=6, move_name="Growl", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=40, maximum_power_points=40, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=7, move_name="Vine Whip", elemental_type="grass", base_power=45, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_3_VICTORY_THRESHOLD),
                PokemonMoveSlot(move_id=8, move_name="Solar Beam", elemental_type="grass", base_power=120, accuracy_percentage=100, current_power_points=10, maximum_power_points=10, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_4_VICTORY_THRESHOLD),
            ]
            return RecruitedPartyMonster(
                pokemon_id=1,
                pokemon_name="Bulbasaur",
                level=6,
                elemental_types=["grass", "poison"],
                victories_count=0,
                stat_progression_multiplier=1.0,
                base_health_points=21,
                base_attack_stat=11,
                base_defense_stat=11,
                base_speed_stat=11,
                effective_health_points=21,
                effective_attack_stat=11,
                effective_defense_stat=11,
                effective_speed_stat=11,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/1.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/1.gif",
                move_slots=base_moves,
            )

        # Squirtle (#7 - Water Starter)
        if pokemon_id == 7:
            base_moves = [
                PokemonMoveSlot(move_id=9, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=10, move_name="Tail Whip", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=40, maximum_power_points=40, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=11, move_name="Water Gun", elemental_type="water", base_power=40, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_3_VICTORY_THRESHOLD),
                PokemonMoveSlot(move_id=12, move_name="Hydro Pump", elemental_type="water", base_power=110, accuracy_percentage=80, current_power_points=5, maximum_power_points=5, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_4_VICTORY_THRESHOLD),
            ]
            return RecruitedPartyMonster(
                pokemon_id=7,
                pokemon_name="Squirtle",
                level=6,
                elemental_types=["water"],
                victories_count=0,
                stat_progression_multiplier=1.0,
                base_health_points=21,
                base_attack_stat=11,
                base_defense_stat=13,
                base_speed_stat=10,
                effective_health_points=21,
                effective_attack_stat=11,
                effective_defense_stat=13,
                effective_speed_stat=10,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/7.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/7.gif",
                move_slots=base_moves,
            )

        # Pidgey (#16 - Normal/Flying Recruitable Wild Monster)
        if pokemon_id == 16:
            base_moves = [
                PokemonMoveSlot(move_id=13, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=14, move_name="Sand Attack", elemental_type="ground", base_power=0, accuracy_percentage=100, current_power_points=15, maximum_power_points=15, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=15, move_name="Gust", elemental_type="flying", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_3_VICTORY_THRESHOLD),
                PokemonMoveSlot(move_id=16, move_name="Air Slash", elemental_type="flying", base_power=75, accuracy_percentage=95, current_power_points=15, maximum_power_points=15, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_4_VICTORY_THRESHOLD),
            ]
            return RecruitedPartyMonster(
                pokemon_id=16,
                pokemon_name="Pidgey",
                level=5,
                elemental_types=["normal", "flying"],
                victories_count=0,
                stat_progression_multiplier=1.0,
                base_health_points=18,
                base_attack_stat=10,
                base_defense_stat=9,
                base_speed_stat=12,
                effective_health_points=18,
                effective_attack_stat=10,
                effective_defense_stat=9,
                effective_speed_stat=12,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/16.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/16.gif",
                move_slots=base_moves,
            )

        # Onix (#95 - Rock/Ground Gym Leader Brock's Signature Monster)
        if pokemon_id == 95:
            base_moves = [
                PokemonMoveSlot(move_id=17, move_name="Rock Throw", elemental_type="rock", base_power=50, accuracy_percentage=90, current_power_points=15, maximum_power_points=15, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=18, move_name="Tackle", elemental_type="normal", base_power=40, accuracy_percentage=100, current_power_points=35, maximum_power_points=35, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=19, move_name="Harden", elemental_type="normal", base_power=0, accuracy_percentage=100, current_power_points=30, maximum_power_points=30, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_3_VICTORY_THRESHOLD),
                PokemonMoveSlot(move_id=20, move_name="Earthquake", elemental_type="ground", base_power=100, accuracy_percentage=100, current_power_points=10, maximum_power_points=10, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_4_VICTORY_THRESHOLD),
            ]
            return RecruitedPartyMonster(
                pokemon_id=95,
                pokemon_name="Onix",
                level=8,
                elemental_types=["rock", "ground"],
                victories_count=0,
                stat_progression_multiplier=1.0,
                base_health_points=24,
                base_attack_stat=11,
                base_defense_stat=18,
                base_speed_stat=11,
                effective_health_points=24,
                effective_attack_stat=11,
                effective_defense_stat=18,
                effective_speed_stat=11,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/95.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/95.gif",
                move_slots=base_moves,
            )

        # Starmie (#121 - Water/Psychic Gym Leader Misty's Signature Monster)
        if pokemon_id == 121:
            base_moves = [
                PokemonMoveSlot(move_id=21, move_name="Water Gun", elemental_type="water", base_power=40, accuracy_percentage=100, current_power_points=25, maximum_power_points=25, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=22, move_name="Swift", elemental_type="normal", base_power=60, accuracy_percentage=100, current_power_points=20, maximum_power_points=20, is_unlocked=True, unlock_victory_threshold=0),
                PokemonMoveSlot(move_id=23, move_name="Psybeam", elemental_type="psychic", base_power=65, accuracy_percentage=100, current_power_points=20, maximum_power_points=20, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_3_VICTORY_THRESHOLD),
                PokemonMoveSlot(move_id=24, move_name="Hydro Pump", elemental_type="water", base_power=110, accuracy_percentage=80, current_power_points=5, maximum_power_points=5, is_unlocked=False, unlock_victory_threshold=MOVE_SLOT_4_VICTORY_THRESHOLD),
            ]
            return RecruitedPartyMonster(
                pokemon_id=121,
                pokemon_name="Starmie",
                level=9,
                elemental_types=["water", "psychic"],
                victories_count=0,
                stat_progression_multiplier=1.0,
                base_health_points=25,
                base_attack_stat=13,
                base_defense_stat=14,
                base_speed_stat=16,
                effective_health_points=25,
                effective_attack_stat=13,
                effective_defense_stat=14,
                effective_speed_stat=16,
                sprite_front_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/121.gif",
                sprite_back_url="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/back/121.gif",
                move_slots=base_moves,
            )

        # Fallback generic monster template if an custom ID is provided
        return self.build_baseline_species_template(pokemon_id=7)

    def apply_victory_count_to_monster(
        self,
        party_monster: RecruitedPartyMonster,
        new_victories_count: int,
    ) -> RecruitedPartyMonster:
        """
        Updates a RecruitedPartyMonster with a specific victory count, recalculating
        its +1% stat progression multiplier, effective stats, and unlocked move slots.
        """
        # Compute updated multiplier: 1.0 + (new_victories_count * 0.01)
        updated_multiplier = self.calculate_stat_progression_multiplier(
            victories_count=new_victories_count
        )
        # Scale all four combat stats using the canonical rounding formula
        effective_hp = self.calculate_effective_scaled_stat(
            base_stat_value=party_monster.base_health_points,
            victories_count=new_victories_count,
        )
        effective_attack = self.calculate_effective_scaled_stat(
            base_stat_value=party_monster.base_attack_stat,
            victories_count=new_victories_count,
        )
        effective_defense = self.calculate_effective_scaled_stat(
            base_stat_value=party_monster.base_defense_stat,
            victories_count=new_victories_count,
        )
        effective_speed = self.calculate_effective_scaled_stat(
            base_stat_value=party_monster.base_speed_stat,
            victories_count=new_victories_count,
        )
        # Unlock Move Slot 3 at 10 wins and Move Slot 4 at 20 wins
        evaluated_moves = self.evaluate_move_slots_for_victories(
            move_slots=party_monster.move_slots,
            victories_count=new_victories_count,
        )

        return RecruitedPartyMonster(
            pokemon_id=party_monster.pokemon_id,
            pokemon_name=party_monster.pokemon_name,
            level=party_monster.level,
            elemental_types=list(party_monster.elemental_types),
            victories_count=new_victories_count,
            stat_progression_multiplier=updated_multiplier,
            base_health_points=party_monster.base_health_points,
            base_attack_stat=party_monster.base_attack_stat,
            base_defense_stat=party_monster.base_defense_stat,
            base_speed_stat=party_monster.base_speed_stat,
            effective_health_points=effective_hp,
            effective_attack_stat=effective_attack,
            effective_defense_stat=effective_defense,
            effective_speed_stat=effective_speed,
            sprite_front_url=party_monster.sprite_front_url,
            sprite_back_url=party_monster.sprite_back_url,
            move_slots=evaluated_moves,
        )

    @staticmethod
    def convert_party_monster_to_battle_entity(
        party_monster: RecruitedPartyMonster,
    ) -> ActiveBattleEntity:
        """
        Converts a persistent RecruitedPartyMonster into an ActiveBattleEntity
        ready for combat on the stadium floor with full HP and refreshed PP.
        """
        refreshed_moves = [
            PokemonMoveSlot(
                move_id=slot.move_id,
                move_name=slot.move_name,
                elemental_type=slot.elemental_type,
                base_power=slot.base_power,
                accuracy_percentage=slot.accuracy_percentage,
                current_power_points=slot.maximum_power_points,
                maximum_power_points=slot.maximum_power_points,
                is_unlocked=slot.is_unlocked,
                unlock_victory_threshold=slot.unlock_victory_threshold,
            )
            for slot in party_monster.move_slots
        ]
        return ActiveBattleEntity(
            pokemon_id=party_monster.pokemon_id,
            pokemon_name=party_monster.pokemon_name,
            level=party_monster.level,
            elemental_types=list(party_monster.elemental_types),
            current_health_points=party_monster.effective_health_points,
            maximum_health_points=party_monster.effective_health_points,
            attack_stat=party_monster.effective_attack_stat,
            defense_stat=party_monster.effective_defense_stat,
            speed_stat=party_monster.effective_speed_stat,
            sprite_front_url=party_monster.sprite_front_url,
            sprite_back_url=party_monster.sprite_back_url,
            move_slots=refreshed_moves,
        )

    def ensure_trainer_party_initialized(
        self,
        trainer_name: str,
        starter_pokemon_id: int,
    ) -> TrainerPartyPoolState:
        """
        Ensures the trainer has an initialized party pool containing their chosen starter.
        If the trainer already has a pool, ensures the requested starter_pokemon_id is present.
        """
        normalized_trainer_key = trainer_name.strip().lower()
        if normalized_trainer_key not in self.trainer_party_rosters:
            starter_template = self.build_baseline_species_template(pokemon_id=starter_pokemon_id)
            self.trainer_party_rosters[normalized_trainer_key] = {
                starter_template.pokemon_id: starter_template
            }
            self.trainer_active_pokemon_ids[normalized_trainer_key] = starter_template.pokemon_id
        else:
            existing_roster = self.trainer_party_rosters[normalized_trainer_key]
            if starter_pokemon_id not in existing_roster:
                additional_starter = self.build_baseline_species_template(pokemon_id=starter_pokemon_id)
                existing_roster[additional_starter.pokemon_id] = additional_starter
            self.trainer_active_pokemon_ids[normalized_trainer_key] = starter_pokemon_id

        return self.get_trainer_party_pool_state(trainer_name=trainer_name)

    def get_trainer_party_pool_state(self, trainer_name: str) -> TrainerPartyPoolState:
        """
        Returns the trainer's current party roster and whether pre-Turn 1 TEAM swap is enabled.
        """
        normalized_trainer_key = trainer_name.strip().lower()
        roster_map = self.trainer_party_rosters.get(normalized_trainer_key, {})
        if not roster_map:
            # Initialize with Charmander (#4) as default fallback if queried before battle init
            default_starter = self.build_baseline_species_template(pokemon_id=4)
            roster_map = {default_starter.pokemon_id: default_starter}
            self.trainer_party_rosters[normalized_trainer_key] = roster_map
            self.trainer_active_pokemon_ids[normalized_trainer_key] = 4

        party_list = list(roster_map.values())
        active_id = self.trainer_active_pokemon_ids.get(
            normalized_trainer_key,
            party_list[0].pokemon_id,
        )
        total_count = len(party_list)

        return TrainerPartyPoolState(
            trainer_name=trainer_name,
            active_pokemon_id=active_id,
            total_party_count=total_count,
            # Canonical Rule: TEAM swap is disabled when the trainer owns only 1 monster
            is_team_swap_enabled=(total_count > 1),
            party_monsters=party_list,
        )

    def recruit_monster_into_party(
        self,
        trainer_name: str,
        recruited_pokemon_id: int,
    ) -> bool:
        """
        Adds a newly defeated or captured monster into the trainer's party pool.
        Returns True if the species was newly added, or False if already in the pool.
        """
        normalized_trainer_key = trainer_name.strip().lower()
        if normalized_trainer_key not in self.trainer_party_rosters:
            self.trainer_party_rosters[normalized_trainer_key] = {}

        roster_map = self.trainer_party_rosters[normalized_trainer_key]
        if recruited_pokemon_id in roster_map:
            return False

        recruited_template = self.build_baseline_species_template(pokemon_id=recruited_pokemon_id)
        roster_map[recruited_template.pokemon_id] = recruited_template
        return True

    def record_victory_and_auto_recruit(
        self,
        trainer_name: str,
        victorious_pokemon_id: int,
        defeated_opponent_pokemon_id: int,
        defeated_opponent_name: str,
    ) -> VictoryProgressionUpdateResponse:
        """
        Executes Lesson 6 post-victory progression:
        1. Increments the winning monster's victories_count by +1.
        2. Scales HP, Attack, Defense, and Speed by +1% per victory.
        3. Unlocks Move Slot 3 at 10 victories and Move Slot 4 at 20 victories.
        4. Automatically recruits the knocked-out opponent into the trainer's party pool.
        """
        # Ensure trainer party pool exists
        self.ensure_trainer_party_initialized(
            trainer_name=trainer_name,
            starter_pokemon_id=victorious_pokemon_id,
        )
        normalized_trainer_key = trainer_name.strip().lower()
        roster_map = self.trainer_party_rosters[normalized_trainer_key]

        current_monster_record = roster_map[victorious_pokemon_id]
        previously_unlocked_move_ids = {
            slot.move_id for slot in current_monster_record.move_slots if slot.is_unlocked
        }

        # Step 1: Increment victory count by 1
        updated_victories_count = current_monster_record.victories_count + 1

        # Step 2 & 3: Recompute +1% stat boost and evaluate 10/20 win move unlocks
        updated_monster_record = self.apply_victory_count_to_monster(
            party_monster=current_monster_record,
            new_victories_count=updated_victories_count,
        )
        roster_map[victorious_pokemon_id] = updated_monster_record

        # Detect any moves newly unlocked on this exact milestone victory
        newly_unlocked_move_names = [
            slot.move_name
            for slot in updated_monster_record.move_slots
            if slot.is_unlocked and slot.move_id not in previously_unlocked_move_ids
        ]

        # Step 4: Auto-recruit knocked-out opponent into the trainer's party pool
        was_newly_recruited = self.recruit_monster_into_party(
            trainer_name=trainer_name,
            recruited_pokemon_id=defeated_opponent_pokemon_id,
        )

        updated_battle_entity = self.convert_party_monster_to_battle_entity(
            party_monster=updated_monster_record
        )
        updated_pool_state = self.get_trainer_party_pool_state(trainer_name=trainer_name)

        return VictoryProgressionUpdateResponse(
            trainer_name=trainer_name,
            victorious_pokemon_id=victorious_pokemon_id,
            victorious_pokemon_name=updated_monster_record.pokemon_name,
            experience_points_gained=45,
            updated_victories_count=updated_victories_count,
            stat_progression_multiplier=updated_monster_record.stat_progression_multiplier,
            newly_unlocked_move_names=newly_unlocked_move_names,
            was_opponent_auto_recruited=was_newly_recruited,
            recruited_opponent_pokemon_name=defeated_opponent_name,
            updated_monster_entity=updated_battle_entity,
            updated_party_pool=updated_pool_state,
        )

    def execute_pre_turn_team_swap(
        self,
        battle_session: Dict,
        target_pokemon_id: int,
    ) -> TeamSwapResponse:
        """
        Validates and executes a pre-Turn 1 party swap (`TEAM` button):
        - Rejects swap if the battle has already concluded.
        - Rejects swap if Turn 1 has already started (`current_turn_number > 1`).
        - Rejects swap if the trainer only has 1 monster in their party pool.
        - Rejects swap if the target monster is not in the trainer's party pool.
        """
        if battle_session.get("is_battle_concluded", False):
            raise ValueError("Cannot swap party monsters after the battle has concluded.")

        # Canonical Rule: TEAM swap is only permitted before Turn 1 begins
        current_turn_number = battle_session.get("current_turn_number", 1)
        if current_turn_number > 1:
            raise ValueError(
                f"TEAM swap is only permitted before Turn 1 begins (currently on Turn {current_turn_number})."
            )

        trainer_name: str = battle_session["trainer_name"]
        party_pool_state = self.get_trainer_party_pool_state(trainer_name=trainer_name)

        # Canonical Rule: TEAM button is disabled if pool contains only 1 monster
        if party_pool_state.total_party_count <= 1:
            raise ValueError(
                "TEAM swap disabled: Trainer only has 1 monster in party pool."
            )

        normalized_trainer_key = trainer_name.strip().lower()
        roster_map = self.trainer_party_rosters[normalized_trainer_key]

        if target_pokemon_id not in roster_map:
            raise ValueError(
                f"Monster with Pokédex ID {target_pokemon_id} is not in {trainer_name}'s party pool."
            )

        current_player_entity: ActiveBattleEntity = battle_session["player_monster"]
        previous_pokemon_name = current_player_entity.pokemon_name

        # Retrieve target monster from pool and convert to active combat entity
        target_party_monster = roster_map[target_pokemon_id]
        new_active_entity = self.convert_party_monster_to_battle_entity(
            party_monster=target_party_monster
        )

        # Update active session and trainer lead pointer
        battle_session["player_monster"] = new_active_entity
        self.trainer_active_pokemon_ids[normalized_trainer_key] = target_pokemon_id

        updated_pool_state = self.get_trainer_party_pool_state(trainer_name=trainer_name)
        swap_announcement = (
            f"{trainer_name} called back {previous_pokemon_name}! "
            f"Go, {new_active_entity.pokemon_name}!"
        )

        return TeamSwapResponse(
            battle_session_id=battle_session["battle_session_id"],
            previous_pokemon_name=previous_pokemon_name,
            new_active_monster=new_active_entity,
            party_pool_state=updated_pool_state,
            narrative_announcement=swap_announcement,
        )


# Singleton instance for injection across battle engine and route handlers
battle_progression_service = BattleProgressionService()
