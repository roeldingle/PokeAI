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
}

// Battle session wrapper returned upon match initialization
export interface BattleSessionData {
  battle_session_id: string;
  trainer_name: string;
  current_turn_number: number;
  is_battle_concluded: boolean;
  victorious_monster_name?: string | null;
  player_monster: ActiveBattleEntity;
  opponent_monster: ActiveBattleEntity;
}
