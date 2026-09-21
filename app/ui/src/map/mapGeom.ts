/**
 * Shared map spine geometry — DOM indent and SVG nest use the same step
 * so strokes exit box edges and boxes sit on the nest spine.
 */

/** px from a parent box's left edge to the nest vertical under it. */
export const NEST_INSET_PX = 22;

/** rem twin of NEST_INSET_PX (16px root). */
export const NEST_INSET_REM = 1.375;

/** Short horizontal from nest spine into a child box's left edge. */
export const TICK_ARM_REM = 0.75;

/** One nest level = inset under parent + tick into the child box. */
export const NEST_STEP_REM = NEST_INSET_REM + TICK_ARM_REM;

/** Spacer before a bead at the given depth (from trunk's left edge). */
export function indentRem(depth: number): string {
  if (depth <= 0) return `${TICK_ARM_REM}rem`;
  return `${TICK_ARM_REM + depth * NEST_STEP_REM}rem`;
}
