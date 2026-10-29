# Canopy living branches

Five low staggered branches regenerate from a private seed/run-level RNG, independently of combat RNG. Spring branches launch ANY contacting descending body at-475; leaf branches collapse after.8s loaded footing or equivalent damage stress, then regrow after2.4s with overlap-safe delay. Missing branches retain positive health so host pruning cannot remove the regrowth state. Projectile filters pass shots. Damage may stress leaves but never makes these permanent platforms destructible.

One-way body filtering accepts the current feet above the top plus only one fixed-step vertical travel. This catches foreign falling bodies without trapping a slow body at a lower side corner. Actor implementations use explicit flat-foot landings only for inherited rectangular overlap methods. The full radius footprint counts for leaf load; drawing keeps the actual top line at collision top and renders the cropped original branch underneath it. No hidden missing-branch cue is drawn.

Focused tests cover both teams, foreign scheduled motion, lower-corner traversal, collapse/delayed regrowth and deterministic fresh geometry/RNG invariance.
