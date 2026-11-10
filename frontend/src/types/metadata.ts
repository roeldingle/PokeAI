/**
 * Stadium Metadata Type Definition
 * Strict contract representation matching backend Pydantic model:
 * backend/src/schemas/metadata_schema.py -> GameMetadataResponse
 */

export interface GameMetadataResponse {
  // Runtime environment classification: 'local', 'develop', or 'production'
  application_environment: string;

  // Semantic version string of the PokeAI battler engine
  game_version: string;

  // Pedagogical mission of the AI Engineering track
  project_learning_goal: string;

  // Name and branding of the game
  game_title: string;

  // Narrative summary and description
  game_description: string;

  // Name of our AI Game Guide (Shaneil)
  game_guide_name: string;
}
