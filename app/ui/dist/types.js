// Frontend contract for app/'s first web prototype (docs/v4-migration-decision.md).
// Deliberately NOT a mirror of Planning's own Python shape (PLAN_KEYS,
// step_status, current_step, ...) - this is what the manifestation
// layer (backend/manifestation.py) already reduced a Planning result
// to, and nothing more. See that module's docstring for why.
/** Resolve identity from a view that may still carry the deprecated mirror. */
export function projectIdOf(view) {
    const id = view.project_id ?? view.goal_id;
    if (id == null) {
        throw new Error("missing project_id");
    }
    return id;
}
