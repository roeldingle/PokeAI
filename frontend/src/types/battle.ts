/**
 * Battle TypeScript Contracts
 * Mirrors Pydantic schemas in backend/src/schemas/battle_schema.py.
 */

// Represents one of the 4 classic GBA move slots
export interface PokemonMoveSlot {
  move_id: number;
  move_name: string;
  elemental_type: string;
  base_power: number;
  accuracy_percentage: number;
  current_power_points: number;
  maximum_power_points: number;
  is_unlocked: boolean;
  unlock_victory_threshold: number;
}

// Represents a combatant in the battle ring (Player or Opponent)
export interface ActiveBattleEntity {
  pokemon_id: number;
  pokemon_name: string;
  level: number;
  elemental_types: string[];
  current_health_points: number;
  maximum_health_points: number;
  attack_stat: number;
  defense_stat: number;
  speed_stat: number;
  sprite_front_url: string;
  sprite_back_url: string;
  move_slots: PokemonMoveSlot[];
}

// Payload returned when a single attack action resolves
export interface SingleMoveResolution {
  attacker_name: string;
  defender_name: string;
  move_name: string;
  is_hit_successful: boolean;
  calculated_damage: number;
  type_effectiveness_multiplier: number;
  is_critical_hit: boolean;
  defender_remaining_health_points: number;
  defender_maximum_health_points: number;
  narrative_announcement: string;
}

// Represents an individual monster in the trainer's party pool with +1% victory stat scaling
export interface RecruitedPartyMonster {
  pokemon_id: number;
  pokemon_name: string;
  level: number;
  elemental_types: string[];
  victories_count: number;
  stat_progression_multiplier: number;
  base_health_points: number;
  base_attack_stat: number;
  base_defense_stat: number;
  base_speed_stat: number;
  effective_health_points: number;
  effective_attack_stat: number;
  effective_defense_stat: number;
  effective_speed_stat: number;
  sprite_front_url: string;
  sprite_back_url: string;
  move_slots: PokemonMoveSlot[];
}

// Complete roster of monsters recruited by the trainer and pre-turn TEAM swap state
export interface TrainerPartyPoolState {
  trainer_name: string;
  active_pokemon_id: number;
  total_party_count: number;
  is_team_swap_enabled: boolean;
  party_monsters: RecruitedPartyMonster[];
}

// Response returned after a pre-Turn 1 party swap
export interface TeamSwapResponse {
  battle_session_id: string;
  previous_pokemon_name: string;
  new_active_monster: ActiveBattleEntity;
  party_pool_state: TrainerPartyPoolState;
  narrative_announcement: string;
}

// Post-battle progression summary awarded upon knockout victory
export interface VictoryProgressionUpdateResponse {
  trainer_name: string;
  victorious_pokemon_id: number;
  victorious_pokemon_name: string;
  experience_points_gained: number;
  updated_victories_count: number;
  stat_progression_multiplier: number;
  newly_unlocked_move_names: string[];
  was_opponent_auto_recruited: boolean;
  recruited_opponent_pokemon_name?: string | null;
  updated_monster_entity: ActiveBattleEntity;
  updated_party_pool: TrainerPartyPoolState;
}

// Comprehensive response returned after a round of combat
export interface BattleTurnResolutionResponse {
  battle_session_id: string;
  current_turn_number: number;
  first_action_resolution: SingleMoveResolution;
  second_action_resolution?: SingleMoveResolution | null;
  player_monster: ActiveBattleEntity;
  opponent_monster: ActiveBattleEntity;
  is_battle_concluded: boolean;
  victorious_monster_name?: string | null;
  maximum_turns_allowed?: number;
  is_turn_limit_reached?: boolean;
  progression_update?: VictoryProgressionUpdateResponse | null;
}

// Battle session wrapper returned upon match initialization
export interface BattleSessionData {
  battle_session_id: string;
  trainer_name: string;
  current_turn_number: number;
  maximum_turns_allowed?: number;
  is_turn_limit_reached?: boolean;
  is_battle_concluded: boolean;
  victorious_monster_name?: string | null;
  player_monster: ActiveBattleEntity;
  opponent_monster: ActiveBattleEntity;
  party_pool?: TrainerPartyPoolState;
  progression_update?: VictoryProgressionUpdateResponse | null;
}

// Lesson 7: Pokéball Roulette Wheel Tiers
export type PokeballTier = "GOLD" | "SILVER" | "BRONZE" | "NORMAL";

// Lesson 7: Request payload to spin the overtime capture roulette wheel
export interface CatchRouletteSpinRequest {
  trainer_name: string;
  opponent_pokemon_id: number;
  opponent_pokemon_name: string;
  opponent_pokemon_sprite_url: string;
  opponent_level?: number;
  injected_tier_roll?: number;
  injected_catch_roll?: number;
}

// Lesson 7: Full outcome returned after spinning the roulette wheel
export interface CatchRouletteOutcome {
  selected_pokeball_tier: PokeballTier;
  capture_probability: number;
  capture_successful: boolean;
  captured_monster_name: string;
  narrative_outcome: string;
  updated_party_pool?: TrainerPartyPoolState | null;
}

