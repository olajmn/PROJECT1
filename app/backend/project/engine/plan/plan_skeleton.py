"""
The named grains a plan's time skeleton is chosen along - the recipe
for *shape*, not the filled labels.

Abstract comparison (not code vocabulary): stacked timeframes work
like a trading chart. Zoom out and one bar stands for a fixed stack of
finer bars underneath; zoom in and those finer bars are what you see.
A Goal's duration picks which face is drawn on top. Crossing a length
threshold changes the face entirely - there is no "sort of a week"
halfway state.

What each slot on that face *says* stays a live fill. This file only
names the faces, the parent/child counts, and the date rules so the
shape does not get re-invented per call.

Data only, no logic and no model call - same split as
goal/planability_slots.py. Nothing reads this yet; live layout is
still foundation/time/.../frozen_duration.py (`week_windows` /
`day_windows`) and planning/plan/plan_structure.py. Numbers here must
stay aligned with WEEK_GRAIN_* there when either side moves.
"""

# Contents
#  1. Parent/child scale (coarse → fine)
#  2. Faces: which scale is drawn for a span length
#  3. Week-face calendar rules
#  4. Ordered face list


# 1. Parent/child scale (coarse → fine)
#
#   year  contains  ~52 week units   (year face not built)
#   week  contains    7 day units    (built; last week may hold more)
#   day   is atomic on the week face (built)
#
# Session is a different face, not another rung on this scale: short
# goals do not draw week/day units at all.

YEAR = "year"
WEEK = "week"
DAY = "day"
SESSION = "session"

WEEKS_PER_YEAR = 52  # approximate; year face not built yet
DAYS_PER_WEEK = 7


class ScaleLevel:
    """One rung on the parent/child scale: what one unit represents,
    and what sits inside it one step finer."""

    def __init__(
        self,
        name: str,
        # Finer unit this one contains, or None if atomic on every
        # built face (day today).
        child: str | None,
        # How many child units make one of this unit when the scale is
        # regular. None when not a fixed ratio (year) or when there is
        # no child. The last week of a span may exceed DAYS_PER_WEEK so
        # leftover calendar days are not dropped - that is the one
        # deliberate irregularity.
        children_per_parent: int | None,
        built: bool,
    ):
        self.name = name
        self.child = child
        self.children_per_parent = children_per_parent
        self.built = built


YEAR_LEVEL = ScaleLevel(YEAR, child=WEEK, children_per_parent=WEEKS_PER_YEAR, built=False)
WEEK_LEVEL = ScaleLevel(WEEK, child=DAY, children_per_parent=DAYS_PER_WEEK, built=True)
DAY_LEVEL = ScaleLevel(DAY, child=None, children_per_parent=None, built=True)

# Coarse → fine. Session is a face, not a scale level.
SCALE = (YEAR_LEVEL, WEEK_LEVEL, DAY_LEVEL)


# 2. Faces: which scale is drawn for a span length
#
# A face is which resolution the plan shows on top. Align min/max with
# frozen_duration.WEEK_GRAIN_*.

WEEK_GRAIN_MIN_DAYS = 5
WEEK_GRAIN_MAX_DAYS = 300


class Face:
    """One resolution: when it applies, which unit is on top, and what
    the model may fill."""

    def __init__(
        self,
        name: str,
        # Inclusive lower bound on span length in calendar days.
        min_days: float,
        # Exclusive upper bound - the next coarser face starts here.
        # None = no upper bound built yet.
        max_days: float | None,
        # Top-level scale unit on this face (week on the week face,
        # year on the year face). None for session - no scale stack.
        top_level: str | None,
        # True where deterministic code lays out the units without the
        # model choosing count or dates.
        skeleton_by_code: bool,
        model_fills: str,
        date_rule: str | None,
        built: bool = True,
    ):
        self.name = name
        self.min_days = min_days
        self.max_days = max_days
        self.top_level = top_level
        self.skeleton_by_code = skeleton_by_code
        self.model_fills = model_fills
        self.date_rule = date_rule
        self.built = built


# 3. Week-face calendar rules
#
# Top units are weeks; one step finer is consecutive calendar days.
# Implemented by week_windows() / day_windows().
#
# Top-level week count: round(calendar_days / DAYS_PER_WEEK), at least 1.
# Blocks abut from the span's start date; the last block runs through
# the span's inclusive last day.
#
# Under each week: consecutive calendar days (never equal clock-slices -
# those skipped weekdays). A short week pads to DAYS_PER_WEEK (padded
# days may be empty/"off"). A long last week keeps every remaining
# calendar day in the span.


SESSION_FACE = Face(
    name=SESSION,
    min_days=0,
    max_days=WEEK_GRAIN_MIN_DAYS,
    top_level=None,
    skeleton_by_code=False,
    model_fills=(
        "however many further steps make sense after the fixed `now` "
        "first step; optional microsteps only where a step warrants them"
    ),
    date_rule=(
        "even slice of the frozen span across the step list at render "
        "time (step_plan), unless a step already carries start/end labels"
    ),
)

WEEK_FACE = Face(
    name=WEEK,
    min_days=WEEK_GRAIN_MIN_DAYS,
    max_days=WEEK_GRAIN_MAX_DAYS,
    top_level=WEEK,
    skeleton_by_code=True,
    model_fills=(
        "one short label per week, plus one string per day under it "
        "(empty or \"off\" allowed - every listed day still appears)"
    ),
    date_rule=(
        "abutting calendar weeks from the span start; "
        "round(calendar_days / 7) weeks (at least 1); each week holds "
        "consecutive calendar days; pad a short week to seven; keep "
        "every remaining day in the last week"
    ),
)

YEAR_FACE = Face(
    name=YEAR,
    min_days=WEEK_GRAIN_MAX_DAYS,
    max_days=None,
    top_level=YEAR,
    skeleton_by_code=True,
    model_fills="one short label per year unit (not built)",
    date_rule=None,
    built=False,
)


# 4. Ordered face list
#
# Match a span to the face whose [min_days, max_days) contains it.
# YEAR_FACE is listed but built=False; do not fall back to SESSION for
# year-scale spans (that mispaints a session tree across years -
# generate_structure() returns None instead).

FACES = (SESSION_FACE, WEEK_FACE, YEAR_FACE)

# Older draft names - same objects, for anything that still says "grain".
SESSION_GRAIN = SESSION_FACE
WEEK_GRAIN = WEEK_FACE
YEAR_GRAIN = YEAR_FACE
GRAINS = FACES
