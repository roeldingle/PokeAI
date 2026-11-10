/**
 * Reusable Animated Character UI Component
 * Renders an animated Pokémon or Trainer sprite with a ground pedestal shadow.
 * Designed to be reused across screens (Title Screen, Starter Selection, Battle Arena).
 */

import React from "react";

export interface CharacterUIProps {
  // National Pokédex ID (e.g. 25 for Pikachu, 1 for Bulbasaur, 4 for Charmander, 7 for Squirtle)
  pokemonNationalPokedexId?: number | string;

  // Optional direct URL override for custom animated assets or guide portraits
  customSpriteUrl?: string;

  // Accessible descriptive alt text for screen readers
  characterAltDescription?: string;

  // Pixel width and height dimensions for the animated sprite container
  pixelDimensionSize?: number;

  // Whether to render the subtle grounded pedestal shadow beneath the character
  shouldDisplayPedestalShadow?: boolean;

  // Optional extra CSS class names for contextual positioning
  additionalClassName?: string;
}

export const CharacterUI: React.FC<CharacterUIProps> = ({
  pokemonNationalPokedexId = 25,
  customSpriteUrl,
  characterAltDescription = "Animated Pokémon Mascot Sprite",
  pixelDimensionSize = 96,
  shouldDisplayPedestalShadow = true,
  additionalClassName = "",
}) => {
  // Construct canonical Gen-5 animated sprite URL if no custom URL override is provided
  const resolvedSpriteUrl: string =
    customSpriteUrl ||
    `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/${pokemonNationalPokedexId}.gif`;

  return (
    <div className={`mascot-sprite-container ${additionalClassName}`}>
      {/* Animated Sprite with pixelated retro scaling */}
      <img
        src={resolvedSpriteUrl}
        alt={characterAltDescription}
        className="mascot-pikachu-sprite"
        style={{
          width: `${pixelDimensionSize}px`,
          height: `${pixelDimensionSize}px`,
        }}
      />

      {/* Grounding circular pedestal shadow */}
      {shouldDisplayPedestalShadow && (
        <div
          className="mascot-pedestal-shadow"
          style={{
            width: `${Math.round(pixelDimensionSize * 0.75)}px`,
          }}
        />
      )}
    </div>
  );
};
