# Knowledge

**Status: FUTURE** - named and sketched in the prototype, not implemented.

Material the user has supplied - their own documents, notes - that the
agent can draw on when reasoning, distinct from relying on the model's own
training or from the agent's own recorded experience (`../memory/`).

## Owns

Retrieval over user-supplied material and handing relevant context to
`../reasoning/`.

## Boundary

- Not Memory. Different corpus (user-supplied vs. self-recorded), different
  purpose (what the user knows/has told the agent vs. what the agent has
  observed happening).
- Not Vision (`../vision/`) - Vision is direction/intention; Knowledge is
  factual/reference material.
- Does not decide what's true - a future fact-checking capability (verifying
  a claim against retrieved sources) is a separate function built on top of
  retrieval, not retrieval itself. Sketched, not designed, in the
  prototype's own docs.

## Where a retrieval mechanism would go, if ever needed

Not a subfolder here on purpose, same reasoning as `../memory/`. Unlike
Memory, this is the one place embeddings are more plausibly needed sooner -
user-supplied documents are more heterogeneous than the agent's own
structured history - but still not built now.

## Reference implementation

None yet. The prototype's `docs/03-architecture.md` § Knowledge sketches a
retrieval-based design (chunk+vector pairs, local embeddings, brute-force
similarity search) as a future direction, not a decision to build it that
way - see that document, not repeated here.
