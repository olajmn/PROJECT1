# Session TODO — 2026-08-21

Working list of things we've identified but deliberately paused, so we
can keep exploring without losing track. Not part of the docs/ vault
(that's permanent project documentation) - this is scratch, meant to
be cleared once everything on it is done or has been moved into a
proper dev log / decision entry.

## Open

- [x] **Remove `YEAR_FRACTIONS`** - done 2026-08-21. Dropped from
      `timesegments.py` (table + `NAMED_FRACTION_RE`'s "year"
      alternative) and `timeperiod.py` (`_FRACTION_TABLES` entry,
      `_named_fraction_end()`'s year branch, simplified now that it
      always returns a `datetime`). "half a year"/"quarter of a year"
      honestly fall through to "not parsed" now. See
      docs/12-decisions.md for why (hour/minute/day fractions earn
      their keep as real speech patterns, year didn't clear that bar).
- [x] **Move `DAY_SEGMENTS` to section 4** - done 2026-08-21: it's
      matched directly by its own key (self-contained), same mechanism
      as `PERIOD_PHRASES`, not a value table needing a separate
      matching regex the way `HOUR_SEGMENTS`/`DAY_FRACTIONS`/etc.
      (still in section 3) are. Section 3's banner rewritten to only
      describe the regular-mathematical-fraction kind now that the one
      irregular-segment table moved out.
- [x] **Split "Phrase Recognition" into 2 sections** - done 2026-08-21:
      section 4 (Point-in-time recognition: `PERIOD_PHRASES`,
      `MONTH_NUMBERS`/`WEEKDAY_NUMBERS`/`WEEKDAY_PREFIXES`,
      `CLOCK_12H_RE`/`CLOCK_24H_RE`, `DEADLINE_RE` - all answer
      "WHEN") vs section 5 (Duration/quantity recognition:
      `DURATION_LENGTH_RE`, `NAMED_FRACTION_RE` - answer "HOW LONG").
      5 sections total now. Purely cosmetic, re-verified.
- [x] **Recognize literal clock times** - done 2026-08-21.
      `CLOCK_12H_RE` ("1 o'clock", "3pm", "11:30am") + `CLOCK_24H_RE`
      ("14:30", "00:00") added to `timesegments.py`;
      `_matched_clock_time()`/`_clock_time_date()` added to
      `timeperiod.py`, combining with the existing day-offset mechanism
      so "tomorrow at 3pm" resolves correctly too. Bare "o'clock" with
      no am/pm ("1 o'clock") is a deliberate, documented convention
      (resolves to PM) - same trade as `WEEKS_PER_MONTH = 4`, not a
      guess.
- [x] **Reorganize `timesegments.py` into 4 sections** - done
      2026-08-21: Basic time-unit facts / Calendar names
      (`WEEKDAY_NAMES`/`MONTH_NAMES`, split into their own section since
      they name a unit's individual slots, not a fraction of it) /
      Named segments-fractions / Phrase recognition. Purely cosmetic,
      re-verified after each reshuffle.
- [x] **Wire `timesegments.py`'s newer tables into actual recognition**
      (`HOUR_SEGMENTS`, `MINUTE_SEGMENTS`, `DAY_FRACTIONS`,
      `YEAR_FRACTIONS`) - done 2026-08-21. One combined
      `NAMED_FRACTION_RE` (same alternation style as
      `DURATION_LENGTH_RE`) added to `timesegments.py`;
      `_matched_named_fraction()`/`_named_fraction_end()` added to
      `timeperiod.py`, dispatching to whichever of the four tables the
      matched unit belongs to. "half an hour"/"quarter of a day"/
      "three quarters of a year" etc now resolve to a real clock time
      or date, same as every other recognized phrase. Deliberately
      does NOT match a bare unit word alone ("an hour") - that's
      already `DURATION_LENGTH_RE`'s job via "1 hour".
- [x] **Wire `MONTH_NAMES`/`WEEKDAY_NAMES` into phrase recognition** -
      done 2026-08-21. `MONTH_NUMBERS`/`WEEKDAY_NUMBERS` (derived
      reverse lookups) + `WEEKDAY_PREFIXES` added to `timesegments.py`;
      `_matched_month_name()`/`_month_name_range()` and
      `_matched_weekday_name()`/`_weekday_name_date()` added to
      `timeperiod.py`, wired into `_resolve_duration()` and
      `describe_duration()`. Real bug found + fixed during this: bare
      month-name matching let "I may go" silently "resolve" to next
      May ("may"/"march"/"august" collide with common English words) -
      fixed by requiring literal "in" before the month name, same
      trade `DEADLINE_RE` already makes with "before". Not yet logged
      in docs/11-experiments.md.
- [x] **Catch up `docs/10-development.md`** - done, all of
      2026-08-20's 4 commits (goal_id, chat-thread UI, diagram rebuild,
      architecture_mapper) and today's (2026-08-21) module split +
      drift fix + classifier + time-phrase recognition now logged.
- [x] **Log real findings in `docs/11-experiments.md`** - done, all 3
      entries added, cited against the real stored history
      (goal_id 11/12) rather than from memory.
- [x] **Commit today's (2026-08-21) work** - done, pushed as
      `e277f1a` on `multi-goal-ui-and-goal-id`.

- [x] **Clean up test goals created while building the timer** - done.
      `goal_id 14`/`15` marked complete (user's choice), same pattern
      as the 2026-08-19 board cleanup.

## Done, just noting for the record

- goal_id identity, per-goal feedback, chat-thread UI, outcome
  classifier, drift fix, Goal/Plan/Timeperiod/Task/Conversation model
  view, module split, week/month/year/day-offset time recognition -
  all built and tested this session, see conversation history for
  specifics until the dev log/experiments log catch up.
