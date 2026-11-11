"""
Catch Roulette Service Module
Implements Lesson 7 Turn-5 overtime capture mechanics:
1. Weighted roulette wheel tier selection across 4 Pokéball tiers:
   - Gold (90% Catch Rate, 10% Wheel Weight)
   - Silver (75% Catch Rate, 25% Wheel Weight)
   - Bronze (60% Catch Rate, 35% Wheel Weight)
   - Normal (50% Catch Rate, 30% Wheel Weight)
2. Uniform random float evaluation against the chosen tier's capture probability.
3. Automatic party pool recruitment via BattleProgressionService when a catch succeeds.
4. Generation of retro stadium announcer narratives for wobble suspense and outcome resolution.
"""

import random
from typing import Dict, Optional
from src.schemas.catch_schema import CatchRouletteOutcome, CatchRouletteSpinRequest, PokeballTier
from src.schemas.progression_schema import TrainerPartyPoolState
from src.services.battle_progression_service import battle_progression_service


# Tier specifications with exact capture probabilities and wheel distribution weights
TIER_SPECIFICATIONS: Dict[PokeballTier, Dict[str, float]] = {
    PokeballTier.GOLD: {
        # 90% chance of successfully catching the monster when thrown
        "capture_probability": 0.90,
        # 10% chance of the roulette wheel landing on the Gold segment
        "wheel_weight": 0.10,
    },
    PokeballTier.SILVER: {
        # 75% chance of successfully catching the monster when thrown
        "capture_probability": 0.75,
        # 25% chance of the roulette wheel landing on the Silver segment
        "wheel_weight": 0.25,
    },
    PokeballTier.BRONZE: {
        # 60% chance of successfully catching the monster when thrown
        "capture_probability": 0.60,
        # 35% chance of the roulette wheel landing on the Bronze segment
        "wheel_weight": 0.35,
    },
    PokeballTier.NORMAL: {
        # 50% chance of successfully catching the monster when thrown
        "capture_probability": 0.50,
        # 30% chance of the roulette wheel landing on the Normal segment
        "wheel_weight": 0.30,
    },
}


class CatchRouletteService:
    """
    Manages the weighted probability selection of Pokéball tiers and resolves
    overtime capture rolls when a battle reaches the 5-turn limit.
    """

    @staticmethod
    def get_tier_capture_probability(pokeball_tier: PokeballTier) -> float:
        """
        Retrieves the calibrated capture probability for a given Pokéball tier.
        """
        # Look up probability in the canonical specification dictionary
        tier_data = TIER_SPECIFICATIONS.get(pokeball_tier)
        if not tier_data:
            # Fallback to standard 50% if an unrecognized tier is encountered
            return 0.50
        return tier_data["capture_probability"]

    @staticmethod
    def select_pokeball_tier(injected_tier_roll: Optional[float] = None) -> PokeballTier:
        """
        Determines which Pokéball tier the wheel lands on using cumulative distribution.
        Allows an injected roll (0.0 to 1.0) for deterministic unit testing.
        Cumulative boundaries:
        - [0.00, 0.10) -> GOLD   (10% weight)
        - [0.10, 0.35) -> SILVER (25% weight)
        - [0.35, 0.70) -> BRONZE (35% weight)
        - [0.70, 1.00] -> NORMAL (30% weight)
        """
        # Determine the random value to use (either injected test value or real uniform random)
        if injected_tier_roll is not None:
            # Clamp injected roll between 0.0 and 1.0
            wheel_roll = max(0.0, min(1.0, injected_tier_roll))
        else:
            # Generate uniform random float in [0.0, 1.0)
            wheel_roll = random.random()

        # Cumulative probability checkpoints
        gold_boundary = TIER_SPECIFICATIONS[PokeballTier.GOLD]["wheel_weight"]
        silver_boundary = gold_boundary + TIER_SPECIFICATIONS[PokeballTier.SILVER]["wheel_weight"]
        bronze_boundary = silver_boundary + TIER_SPECIFICATIONS[PokeballTier.BRONZE]["wheel_weight"]

        # Evaluate which slice the roll landed in
        if wheel_roll < gold_boundary:
            return PokeballTier.GOLD
        elif wheel_roll < silver_boundary:
            return PokeballTier.SILVER
        elif wheel_roll < bronze_boundary:
            return PokeballTier.BRONZE
        else:
            return PokeballTier.NORMAL

    @staticmethod
    def evaluate_catch_attempt(
        pokeball_tier: PokeballTier,
        injected_catch_roll: Optional[float] = None,
    ) -> bool:
        """
        Evaluates whether the Pokéball successfully captures the target monster.
        A catch succeeds if the roll is strictly less than the tier's capture probability.
        For example, Gold (0.90) succeeds for any roll in [0.0, 0.90).
        """
        # Retrieve the target tier's threshold
        target_threshold = CatchRouletteService.get_tier_capture_probability(pokeball_tier)

        # Determine the catch roll
        if injected_catch_roll is not None:
            # Clamp test roll between 0.0 and 1.0
            catch_roll = max(0.0, min(1.0, injected_catch_roll))
        else:
            # Generate uniform random float in [0.0, 1.0)
            catch_roll = random.random()

        # Catch succeeds if roll lands under the success threshold
        return catch_roll < target_threshold

    def execute_roulette_spin_and_catch(
        self,
        spin_request: CatchRouletteSpinRequest,
    ) -> CatchRouletteOutcome:
        """
        Executes the complete Lesson 7 overtime sequence:
        1. Spins the roulette wheel to determine the Pokéball tier.
        2. Rolls for capture success against the chosen tier's probability.
        3. If caught, recruits the wild monster into the trainer's party pool.
        4. Returns the full outcome envelope with commentator narration.
        """
        # Step 1: Select the Pokéball tier
        selected_tier = self.select_pokeball_tier(
            injected_tier_roll=spin_request.injected_tier_roll
        )

        # Step 2: Retrieve calibrated capture probability
        tier_capture_probability = self.get_tier_capture_probability(selected_tier)

        # Step 3: Evaluate catch success
        is_capture_successful = self.evaluate_catch_attempt(
            pokeball_tier=selected_tier,
            injected_catch_roll=spin_request.injected_catch_roll,
        )

        # Step 4: Handle party recruitment if successful
        updated_party_pool_state: Optional[TrainerPartyPoolState] = None
        if is_capture_successful:
            # Recruit the opponent species into the trainer's active party pool
            battle_progression_service.recruit_monster_into_party(
                trainer_name=spin_request.trainer_name,
                recruited_pokemon_id=spin_request.opponent_pokemon_id,
            )
            # Fetch the updated party pool state to return to the frontend
            updated_party_pool_state = battle_progression_service.get_trainer_party_pool_state(
                trainer_name=spin_request.trainer_name
            )

            # Build victorious commentator narrative with iconic 3-wobble click
            narrative = (
                f"🎰 ROULETTE RESULT: Lands on {selected_tier.value} Ball "
                f"({int(tier_capture_probability * 100)}% Catch Rate)! "
                f"Wobble... Wobble... Wobble... CLICK! ⭐ Gotcha! "
                f"Wild {spin_request.opponent_pokemon_name} was caught!"
            )
        else:
            # Build suspenseful break-free commentator narrative
            narrative = (
                f"🎰 ROULETTE RESULT: Lands on {selected_tier.value} Ball "
                f"({int(tier_capture_probability * 100)}% Catch Rate)! "
                f"Wobble... Wobble... BURST! 💨 Oh no! "
                f"Wild {spin_request.opponent_pokemon_name} broke free and fled!"
            )

        # Return full outcome payload
        return CatchRouletteOutcome(
            selected_pokeball_tier=selected_tier,
            capture_probability=tier_capture_probability,
            capture_successful=is_capture_successful,
            captured_monster_name=spin_request.opponent_pokemon_name,
            narrative_outcome=narrative,
            updated_party_pool=updated_party_pool_state,
        )


# Singleton service instance exported for application routes and dependency injection
catch_roulette_service = CatchRouletteService()
