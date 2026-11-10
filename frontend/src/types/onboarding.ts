/**
 * Onboarding Data Contracts
 * Synchronized with backend Pydantic v2 models (backend/src/schemas/onboarding_schema.py).
 */

// Model representing a single starter monster card
export interface StarterMonsterInfo {
  starter_pokemon_id: number;
  monster_name: string;
  elemental_types: string[];
  starter_description: string;
  base_hit_points: number;
  base_attack_power: number;
  base_defense_rating: number;
  base_speed_velocity: number;
  front_sprite_url: string;
}

// Intake payload sent to backend when registering trainer and starter choice
export interface TrainerRegistrationRequest {
  trainer_name: string;
  selected_starter_id: number;
}

// Response envelope returned by backend after successful registration
export interface TrainerProfileResponse {
  trainer_registration_id: string;
  trainer_name: string;
  selected_starter_monster: StarterMonsterInfo;
  victories_count: number;
  stat_progression_multiplier: number;
  created_at_timestamp: string;
}