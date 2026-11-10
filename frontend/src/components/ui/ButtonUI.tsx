/**
 * Reusable Pokémon GBA Button Component
 * Standardizes button styling across all screens and stages with authentic handheld tactile mechanics.
 */

import React from "react";

export interface ButtonUIProps {
  // Label or elements displayed within the button
  children: React.ReactNode;

  // Click handler callback
  onClick?: () => void;

  // Button type attribute
  type?: "button" | "submit" | "reset";

  // Visual variant: 'default' parchment, 'action' highlighted, or 'subtle'
  variant?: "default" | "action" | "subtle";

  // Display animated Pokémon red pointer arrow(s)
  showArrowPointer?: "left" | "right" | "both" | "none";

  // Disabled state flag
  disabled?: boolean;

  // Optional extra CSS classes for layout adjustments
  additionalClassName?: string;

  // Accessible title tooltip
  title?: string;
}

export const ButtonUI: React.FC<ButtonUIProps> = ({
  children,
  onClick,
  type = "button",
  variant = "default",
  showArrowPointer = "none",
  disabled = false,
  additionalClassName = "",
  title,
}) => {
  const showLeftArrow: boolean =
    showArrowPointer === "left" || showArrowPointer === "both";
  const showRightArrow: boolean =
    showArrowPointer === "right" || showArrowPointer === "both";

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`pokemon-retro-button pokemon-button-${variant} ${additionalClassName}`}
    >
      {showLeftArrow && (
        <span className="pokemon-btn-arrow pokemon-btn-arrow-left">▶</span>
      )}
      <span className="pokemon-btn-label">{children}</span>
      {showRightArrow && (
        <span className="pokemon-btn-arrow pokemon-btn-arrow-right">◀</span>
      )}
    </button>
  );
};
