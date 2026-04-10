GORGIAS_SPEC = """
## GORGIAS CODE STRUCTURE
A Gorgias program consists of the following elements in this exact order:
1. Dynamic declarations
2. Base rules (for both decisions and beliefs)
3. First-level preferences and meta-preferences (for both decisions and beliefs)
4. Complement declarations
5. Abducible declarations (only if needed)
───────────────────────────────────────────────────────────────────────
### 1. Dynamic declarations
Declare ALL observable runtime facts:
:-dynamic fact1/0, fact2/0, fact3/0.
NEVER declare as dynamic any information that appears in the [] of any rule (base, preference or meta-preference) — those are beliefs or abducibles, not observable facts.
───────────────────────────────────────────────────────────────────────
### 2. Base rules (r rules)
Rules have the form:
rule(RuleID, Conclusion, [Beliefs/Abducibles]) :- Conditions.
- RuleID: unique identifier (r1, r2, ...)
- Conclusion: a decision/action (e.g. go_out, stay_home) OR a belief (e.g. it_will_rain, sunny_day). When an action involves a computed value (e.g. a negotiated price), represent it as a parameterised conclusion: make_concession(NCO).
- [Beliefs/Abducibles]: list of belief names or abducible assumptions involved in this rule. These are defeasible pieces of knowledge that:
* Cannot be directly observed as hard facts
* Beliefs can themselves be derived through base rules and first-level preferences — they have their own rule structure
* Abducibles are atomic assumptions with no rule structure
* Both are named in the [] of every rule they are involved in, whether that rule is an r, p or c rule
- Conditions: observable facts in the rule body (after :-)
- Arithmetic conditions are placed DIRECTLY in the rule body, never as separate derived predicates.
- r rules ONLY reference actions or beliefs as conclusions.
CRITICAL — BASE RULES MUST BE MAXIMALLY GENERAL:
Base rules express ONLY what actions are POSSIBLE under the triggering condition — nothing more. They must NOT include contextual reasons that make one action preferable over another.
WRONG — contextual condition in base rule:
rule(r2, get_restaurant, []) :- day_off, sunny_day.
rule(r3, get_cinema, []) :- day_off, oscar_winner_movie.
RIGHT — maximally general base rules:
rule(r1, stay_home, []) :- day_off.
rule(r2, get_restaurant, []) :- day_off.
rule(r3, get_cinema, []) :- day_off.
Contextual reasons that make one action preferable over another belong EXCLUSIVELY in the preference rules and meta-preferences — never in base rules.
WHEN ARE RULES INTRODUCED IN PAIRS (OR GROUPS)?
Rules with DIFFERENT conclusions are introduced in pairs (or groups when more than two actions are possible) — and their conflicts resolved by first-level preferences — in TWO situations:
SITUATION 1 — Same premises, different conclusions:
All rules share exactly the same conditions. Conflicts arise whenever the shared condition is true and contextual reasons make multiple options applicable. The first-level preferences carry the contextual conditions.
Example:
rule(r1, stay_home, []) :- day_off.
rule(r2, get_restaurant, []) :- day_off.
rule(r3, get_cinema, []) :- day_off.
% contextual reasons go in preferences:
rule(p1a, prefer(r2, r1), []) :- day_off, sunny_day.
rule(p1b, prefer(r3, r1), []) :- day_off, oscar_winner_movie.
SITUATION 2 — Different premises, different conclusions:
Rules have different conditions but the UNION of their premises forms a COHERENT/POSSIBLE scenario. The conflict only arises in that overlapping scenario and the first-level preference carries the union of both sets of premises.
Example:
rule(r1, stay_home, []) :- good_movie_tv.
rule(r2, go_to_restaurant, []) :- friend_offers_restaurant.
% conflict arises when both conditions are simultaneously true:
rule(p1, prefer(r1, r2), []) :- good_movie_tv,
friend_offers_restaurant.
If the premises of two rules are MUTUALLY EXCLUSIVE (can never be simultaneously true), there is no conflict and no first-level preference is needed between them.
OBSERVABLE FACTS vs BELIEFS vs ABDUCIBLES:
Three distinct categories — never confuse them:
OBSERVABLE FACT:
Directly known or computable at runtime without ambiguity.
Goes in :-dynamic declarations and rule bodies.
Examples: day_off, rains, current_month(august)
DERIVED OBSERVABLE FACT (computed, non-defeasible):
Computed from arithmetic or logical conditions that are mutually exclusive by construction — no conflict possible.
Goes DIRECTLY in rule bodies as arithmetic conditions.
NEVER put in [] and NEVER declare as abducible.
Example: CO > PO (offer improved) vs CO =< PO (not improved) — these are mutually exclusive by arithmetic, so they are simply computed conditions in rule bodies, not beliefs.
BELIEF (defeasible derived knowledge):
Can be derived in CONFLICTING ways that require preference rules to resolve. Has its own rule/preference/meta-preference structure. Named in [] of every rule it is involved in.
Example: it_will_rain derived from two conflicting forecasts — requires preference rules to resolve the conflict.
ABDUCIBLE (atomic defeasible assumption):
Cannot be observed or derived — must be assumed.
No rule structure of its own.
Named in [] of rules it is involved in.
Declared with abducible/2.
KEY TEST — ask these questions in order:
1. Is it directly observable at runtime? → :-dynamic + body
2. Is it computable from mutually exclusive arithmetic/logical
conditions with no possible conflict? → body only (derived observable fact)
3. Can it be derived in conflicting ways requiring preference resolution? → [] + belief rule structure
4. Must it be assumed with no derivation possible? → [] + abducible
───────────────────────────────────────────────────────────────────────
### 3. First-level preferences (p rules) and meta-preferences (c rules)
TERMINOLOGY:
- p rules = FIRST-LEVEL PREFERENCES
They resolve conflicts between base rules (r rules).
They express which r rule is preferred over another.
→ prefer(ri, rj)
- c rules = META-PREFERENCES
They resolve conflicts between first-level preferences (p rules) or between other meta-preferences (c rules).
They express which preference rule is preferred over another.
→ prefer(px, py) or prefer(cx, cy)
The hierarchy is ordered from lowest to highest priority:
r1, r2, r3 base rules (lowest priority)
p1 default first-level preference
p2 exception first-level preference
c1 meta-preference resolving p1/p2
c2 exception meta-preference
c3 meta-preference resolving c1/c2
c4 exception meta-preference
c5 meta-preference resolving c3/c4
... (highest priority)
GENERAL FORM (applies to ALL p and c rules):
rule(ID, prefer(A, B), [Beliefs/Abducibles]) :- Conditions.
The [Beliefs/Abducibles] slot is available in EVERY rule — base rules, first-level preferences AND meta-preferences alike.
A belief or abducible must be listed in the [] of every rule in which it plays a role.
LEVEL SEPARATION — the most critical structural rule:
- p rules: preferences between r rules ONLY → prefer(ri, rj)
- c rules: preferences between p or c rules ONLY → prefer(px, py) or prefer(cx, cy)
- NEVER mix levels: a c rule must NEVER reference an r rule directly, and a p rule must NEVER reference a c rule.
- NEVER write prefer(p_x, c_y) or prefer(c_x, p_y) — always wrong.
This level separation applies INDEPENDENTLY to:
(a) the decision/action reasoning chain
(b) the belief reasoning chain
Each chain has its own r, p, c rules and they never mix.
CONFLICT EXISTENCE CONSTRAINT — the most fundamental rule:
A meta-preference can ONLY be placed between two preference rules that express OPPOSITE preferences between THE SAME PAIR of actions.
This means:
- prefer(rA, rB) conflicts with prefer(rB, rA) ✓
- prefer(rA, rB) does NOT conflict with prefer(rB, rC) ✗
- prefer(rA, rB) does NOT conflict with prefer(rC, rD) ✗
A preference ordering chain is NOT a conflict:
p2: prefer(r4, r2) — r4 beats r2
p3: prefer(r3, r4) — r3 beats r4
These are COMPATIBLE — they form a transitivity chain r3 > r4 > r2. Writing c1 = prefer(p3, p2) would be MEANINGLESS because p3 and p2 never contradict each other — they resolve conflicts between DIFFERENT pairs of actions. A genuine conflict only exists between:
p3: prefer(r3, r4) — make concession wins
p4: prefer(r4, r3) — accept wins (critical situation)
These ARE opposite — same pair (r3,r4), opposite directions.
Only THESE deserve a meta-preference resolver:
c1: prefer(p3, p4) ✓ genuine conflict resolved
BEFORE writing any meta-preference, always verify:
Do the two rules it resolves express OPPOSITE preferences between the SAME pair of actions?
YES → genuine conflict → meta-preference is valid
NO → no conflict → meta-preference is meaningless and wrong
OPPOSITION CONSTRAINT:
At every level, the two meta-preferences resolved by an unconditional resolver MUST express OPPOSITE preferences.
This means one must favour action A over action B and the other must favour action B over action A — for THE SAME PAIR.
WRONG — p3 and p2 resolve different pairs, not opposite:
rule(p2, prefer(r4, r2), []). % r4 vs r2
rule(p3, prefer(r3, r4), []). % r3 vs r4 — different pair!
rule(c1, prefer(p3, p2), []). % MEANINGLESS — no genuine conflict
WRONG — c6 and c5 are not opposites:
rule(c5, prefer(c4, c3), []). % c4 = prefer(c1,c2) = stay home
rule(c6, prefer(c2, c1), []). % c6 also means go out via c2/c1
rule(c7, prefer(c6, c5), []). % MEANINGLESS — no genuine conflict
RIGHT — p3 and p4 resolve the same pair oppositely:
rule(p3, prefer(r3, r4), []). % r3 beats r4
rule(p4, prefer(r4, r3), []). % r4 beats r3 — genuine opposite ✓
rule(c1, prefer(p3, p4), []). % valid — resolves genuine conflict
RIGHT — c6 and c5 are opposites:
rule(c5, prefer(c4, c3), []). % c4 = prefer(c1,c2) = stay home
rule(c6, prefer(c3, c4), []). % c6 = prefer(c3,c4) = go out ✓
rule(c7, prefer(c6, c5), []). % valid — resolves genuine conflict
CHECK: before writing any resolver, verify that the two rules it resolves express genuinely opposite preferences between
THE SAME PAIR of actions.
PREFERENCE ORDERING CHAINS vs CONFLICTS:
When the text establishes a total ordering among three or more actions (e.g. A > B > C), this is expressed as INDEPENDENT preference rules — one per pair — with NO meta-preference between them:
p_AB: prefer(rA, rB) — A beats B
p_BC: prefer(rB, rC) — B beats C
% NO meta-preference between p_AB and p_BC — they are not in conflict A meta-preference is only needed when TWO rules express CONFLICTING preferences about THE SAME PAIR and a context determines which one should win.
FIRST-LEVEL PREFERENCES (p rules):
rule(PrefID, prefer(RuleA, RuleB), [Beliefs/Abducibles]) :- Conditions.
- PrefID: unique identifier (p1, p1a, p1b, p2, ...)
- prefer(RuleA, RuleB): r rule A is preferred over r rule B
- [Beliefs/Abducibles]: beliefs or abducibles involved in this preference
- When more than two actions are possible, multiple first-level preference pairs are needed — one for each conflicting pair of base rules (e.g. p1a for r2 vs r1, p1b for r3 vs r1, p3 for r2 vs r3).
- Each pair of conflicting first-level preferences (e.g. p3 and p4 both about r3 vs r4) gets its own meta-preference chain.
- Independent pairs (e.g. p2 about r4 vs r2, p3 about r3 vs r4) do NOT get a meta-preference between them.
- The DEFAULT first-level preference carries no body when one option always beats another regardless of context. It carries a body when the conflict only arises under specific conditions.
- Exception preferences (p2, p2a, p2b, ...) always carry conditions in their body.
META-PREFERENCES (c rules):
rule(MetaPrefID, prefer(PrefA, PrefB), [Beliefs/Abducibles]) :- Conditions.
- MetaPrefID: unique identifier (c1, c1a, c1b, c2, ...)
- prefer(PrefA, PrefB): preference rule A is preferred over preference rule B — where A and B are both p rules or both c rules, NEVER mixed, and ALWAYS expressing opposite preferences about THE SAME PAIR of actions
- [Beliefs/Abducibles]: beliefs or abducibles involved in this meta-preference — propagated cumulatively just like body conditions
- TWO types of meta-preferences:
TYPE A — UNCONDITIONAL (the default):
One preference always beats the other regardless of any context.
These meta-preferences have NO body but MAY still have [] content if a belief or abducible is involved.
The two rules they resolve MUST express opposite preferences about THE SAME PAIR (see CONFLICT EXISTENCE CONSTRAINT above).
rule(c1, prefer(p2, p1), []). % p2 and p1 both about same pair ✓
rule(c3, prefer(c2, c1), []).
rule(c5, prefer(c4, c3), []).
TYPE B — CONDITIONAL (exception):
The conflict between two preference rules only arises under SPECIFIC circumstances — when the union of the premises of the conflicting rules forms a coherent scenario. There are two cases:
CASE 1 — Same premises, different conclusions at preference level:
The meta-preference carries that shared condition.
CASE 2 — Different premises that can be simultaneously true:
The body of the meta-preference is the UNION of:
(a) all conditions of the two preference rules it resolves
(b) its own specific condition (if any)
The [] of the meta-preference carries the UNION of:
(a) all beliefs/abducibles of the two rules it resolves
(b) its own specific beliefs/abducibles (if any)
Both body and [] propagate cumulatively into all higher levels.
When in doubt, meta-preferences are unconditional. Only make a meta-preference conditional when the premises of the conflicting preference rules can be simultaneously true, forming a coherent scenario that must be explicitly handled.
───────────────────────────────────────────────────────────────────────
### 4. Cumulative context rule — when to add a new level vs same level
The key question at every step is:
Does this new condition/belief REVERSE a preference already established at a lower-priority level of the hierarchy?
YES — it introduces a NEW meta-preference level (new c rule):
The new condition actively overrides a preference that was already established separately at a lower-priority level.
Signal in text: "however", "unless", "except when", "despite" — a new overriding exception stated separately.
The new c rule MUST express the OPPOSITE preference to the c rule it conflicts with at the level below it — AND must concern THE SAME PAIR of actions.
Example:
c4 says prefer(c1, c2) — stay home wins [same pair A/B]
c6 must say prefer(c3, c4) — go out wins [same pair A/B, opposite]
c7 then resolves: prefer(c6, c5)
NO — it stays at the SAME level, added to existing rule body:
The new condition jointly triggers a preference together with existing conditions, without reversing any previously established lower-priority preference.
Signal in text: "and", "also", "both" — conditions stated together as a single joint exception.
Each new exception level that IS introduced inherits ALL conditions AND ALL beliefs/abducibles of ALL previous levels, and adds its own new condition and/or belief/abducible on top:
p1 [bel_A] :- cond_A.
p2 [bel_B] :- cond_B, cond_C.
c1 [bel_A, bel_B] :- cond_A, cond_B, cond_C.
% union of p1+p2 conditions and beliefs
% p1 and p2 MUST be about the same pair ✓
c2 [bel_A, bel_B] :- cond_A, cond_B, cond_C, cond_D.
% inherits full c1 union, adds cond_D
% c2 expresses OPPOSITE preference to c1,
% same pair ✓
c3 [] % unconditional — c2 beats c1
c4 [bel_A, bel_B] :- cond_A, cond_B, cond_C, cond_D, cond_E.
% inherits c1+c2 union, adds cond_E
% c4 expresses OPPOSITE preference to c2,
% same pair ✓
c5 [] % unconditional — c4 beats c3
───────────────────────────────────────────────────────────────────────
### 5. Alternative triggers at the same level
When two independent conditions lead to the same preference at the same level, create parallel meta-preferences with their own unconditional resolvers:
rule(c2, prefer(px, py), [bel_A]) :- cond_A, cond_B.
rule(c2b, prefer(px, py), [bel_B]) :- cond_A, cond_C.
rule(c3, prefer(c2, c1), []).
rule(c3b, prefer(c2b, c1), []).
Both c2 and c2b must express the SAME preference direction (both must be opposite to c1) and about THE SAME PAIR of actions.
Do NOT link parallel branches unless the text explicitly states an interaction between them.
───────────────────────────────────────────────────────────────────────
### 6. Handling more than two actions
When a scenario has three or more possible actions, a separate preference chain is needed for EACH CONFLICTING PAIR of base rules.
Name preference rules with suffixes (p1a, p1b, p2a, p2b, c1a, c1b, ...) to keep each chain identifiable.
CRITICAL: each chain is entirely independent and handles ONE
specific pair of actions. Rules from different chains are NEVER combined in a meta-preference — doing so would violate the conflict existence constraint (the rules would not be about the same pair).
Within each chain:
- The opposition constraint applies independently
- The alternation pattern applies independently
- The conflict existence constraint applies independently
Chains only interact when the text explicitly states a preference between them (e.g. "if both occur simultaneously prefer X").
───────────────────────────────────────────────────────────────────────
### 7. Complement declarations
Declare ALL mutually exclusive pairs of conclusions in BOTH directions:
complement(action1, action2).
complement(action2, action1).
When more than two actions are possible, declare ALL pairs:
complement(stay_home, get_restaurant).
complement(get_restaurant, stay_home).
complement(stay_home, get_cinema).
complement(get_cinema, stay_home).
complement(get_restaurant, get_cinema).
complement(get_cinema, get_restaurant).
When actions are parameterised, use wildcards:
complement(make_concession(_), accept_below_acceptable).
complement(accept_below_acceptable, make_concession(_)).
This applies to both decisions and beliefs.
───────────────────────────────────────────────────────────────────────
### 8. Abducible declarations
Abducibles are the simplest form of belief — atomic assumptions with no further rule structure. They appear in the [] of ANY rule (base, first-level preference or meta-preference) and are declared with both positive and negative forms.
CRITICAL RULES:
- An abducible is ONLY what appears in the [] of some rule AND has no rule structure of its own (no r/p/c rules deriving it).
- If a belief has its own rule structure → it is a belief with rules, NOT a simple abducible.
- Beliefs and abducibles can appear in the [] of r, p AND c rules.
- If no information appears in [] in any rule, there are NO abducibles.
- NEVER declare as abducible any fact that appears in a rule body (:-)
- those are observable facts belonging in :-dynamic declarations.
- NEVER declare as abducible any derived fact computed from mutually exclusive arithmetic/logical conditions — those are derived observable facts and belong directly in rule bodies.
- Always declare both positive and negative forms:
abducible(assumption, []).
abducible(neg(assumption), []).
───────────────────────────────────────────────────────────────────────
## FULL STRUCTURAL PATTERN
:-dynamic ... observable facts ONLY — never beliefs
% ── BELIEF RULES (if beliefs are present) ──────────────────────
% Beliefs have their own independent r/p/c structure
% They are DEFEASIBLE — can be derived in conflicting ways
rule(r_b1, belief_A, []) :- source_1.
rule(r_b2, belief_B, []) :- source_2.
% conditional meta-preference: conflict when both sources available
rule(p_b1, prefer(r_b1, r_b2), []) :- source_1, source_2.
complement(belief_A, belief_B).
complement(belief_B, belief_A).
% ── DECISION RULES ──────────────────────────────────────────────
% Base rules — maximally general, NO contextual conditions
rule(r1, action_A, []) :- triggering_condition.
rule(r2, action_B, []) :- triggering_condition.
% p1: default — prefer action_B over action_A [action_B wins]
rule(p1, prefer(r2, r1), []).
% p2: exception — prefer action_A over action_B [action_A wins]
% p1 and p2 are about THE SAME PAIR (r1,r2) — genuine conflict ✓
rule(p2, prefer(r1, r2), []) :- cond_A.
% c1: unconditional — p2 beats p1
% p2 = prefer(r1,r2) opposite to p1 = prefer(r2,r1) ✓
% same pair (r1,r2) ✓
rule(c1, prefer(p2, p1), []).
% c2: exception — prefer action_B again [action_B wins]
% OPPOSITE direction to c1's resolved winner
% cumulative: cond_A + cond_B
rule(c2, prefer(p1, p2), []) :- cond_A, cond_B.
% c3: unconditional — c2 beats c1
% c2 = prefer(p1,p2) opposite to c1 = prefer(p2,p1) ✓
rule(c3, prefer(c2, c1), []).
% c4: exception — prefer action_A again [action_A wins]
% OPPOSITE direction to c2
% cumulative: cond_A + cond_B + cond_C
rule(c4, prefer(c1, c2), []) :- cond_A, cond_B, cond_C.
% c5: unconditional — c4 beats c3
% c4 = prefer(c1,c2) opposite to c3 = prefer(c2,c1) ✓
rule(c5, prefer(c4, c3), []).
% Complements — always both directions
complement(action_A, action_B).
complement(action_B, action_A).
% Abducibles — ONLY if something appears in [] with no rule
% structure AND cannot be derived from mutually exclusive conditions
abducible(belief_x, []).
abducible(neg(belief_x), []).
───────────────────────────────────────────────────────────────────────
## PREFERENCE ALTERNATION PATTERN
A key structural property of correctly encoded Gorgias hierarchies is that preferences ALTERNATE direction at each level AND always concern THE SAME PAIR of actions:
p1 prefer(r2, r1) → action_B wins [default, pair r1/r2]
p2 prefer(r1, r2) → action_A wins [exception, same pair ✓]
c1 prefer(p2, p1) → action_A wins [p2 beats p1, same pair ✓]
c2 prefer(p1, p2) → action_B wins [opposite of c1, same pair ✓]
c3 prefer(c2, c1) → action_B wins [c2 beats c1, same pair ✓]
c4 prefer(c1, c2) → action_A wins [opposite of c2, same pair ✓]
c5 prefer(c4, c3) → action_A wins [c4 beats c3, same pair ✓]
c6 prefer(c3, c4) → action_B wins [opposite of c4, same pair ✓]
c7 prefer(c6, c5) → action_B wins [c6 beats c5, same pair ✓]
TWO FAILURE MODES to check at every level:
1. Same direction: two adjacent rules favour the same action → no genuine conflict → resolver is meaningless
2. Different pairs: two rules are about different pairs of actions → no genuine conflict → resolver is meaningless If either failure mode is detected, the encoding has an error.
───────────────────────────────────────────────────────────────────────
## TRANSLATION GUIDE (format: natural language pattern → Gorgias element)
1. "When X, possible actions A/B/C" → r1,r2,r3 share X premise (max general)
2. "sunny/reason for X" → context in p rule body — NEVER r rule
3. "generally/default prefer A" → p1: prefer(rA,rB) []
4. "but if X AND Y prefer B" → p2: prefer(rB,rA) :- X,Y (same level)
5. "but if X... however/unless Y" → p2 for X, c1 new level for Y (reverse)
6. "one always beats other" → c1: prefer(p2,p1) [] (unconditional)
7. "same condition, two conclusions" → p1 conditional: shared cond
8. "both situations occur" → c1 conditional: union p1+p2 premises
9. "A>B>C total order" → p_AB + p_BC independent (NO meta between)
10. "two independent reasons same choice" → c2 + c2b parallel branches
11. "3+ actions" → separate chain per conflicting pair (NEVER mix)
12. "both events simultaneous" → explicit preference between chains
13. "computed value action" → make_concession(NCO)
14. "I believe/I think" → belief chain in []
15. "CO>PO arithmetic" → body condition only (NEVER [])
16. "assumption conditions preference" → abducible in [] of p/c rule
17. "direct observable" → :-dynamic + rule body
───────────────────────────────────────────────────────────────────────
## WORKED EXAMPLE
Input text:
"An agent has two options when the weather is nice: stay home or go out. Default is to go out. However if they have homework for an exam they prefer to stay home. They can go out either when the exam date is not close or when the material is not extensive. In the first case if they are sick they prefer to stay home. However if they have no fever they can go out. If they have no fever they may stay home if it is raining or if there is a nice movie on tv."
Output:
:-dynamic nice_weather/0, homework_exam/0,
exam_date_not_close/0, sick/0,
no_fever/0, its_raining/0,
nice_movie_on_tv/0.
rule(r1, stay_home, []) :- nice_weather.
rule(r2, go_out, []) :- nice_weather.
% p1 and p2 both about pair (r1,r2) ✓
rule(p1, prefer(r2, r1), []).
rule(p2, prefer(r1, r2), []) :- homework_exam.
% c1: p2 opposite to p1, same pair ✓
rule(c1, prefer(p2, p1), []).
% c2: opposite to c1, same pair ✓
rule(c2, prefer(p1, p2), []) :- homework_exam, exam_date_not_close.
% c3: c2 beats c1 ✓
rule(c3, prefer(c2, c1), []).
% c4: opposite to c2, same pair ✓
rule(c4, prefer(c1, c2), []) :- homework_exam,
exam_date_not_close, sick.
% c5: c4 beats c3 ✓
rule(c5, prefer(c4, c3), []).
% c6: opposite to c4, same pair ✓
rule(c6, prefer(c3, c4), []) :- homework_exam,
exam_date_not_close,
sick, no_fever.
% c7: c6 beats c5 ✓
rule(c7, prefer(c6, c5), []).
% c8, c8b: both opposite to c6, same pair ✓ — parallel branches
rule(c8, prefer(c5, c6), []) :- homework_exam,
exam_date_not_close,
sick, no_fever, its_raining.
rule(c8b, prefer(c5, c6), []) :- homework_exam,
exam_date_not_close,
sick, no_fever, nice_movie_on_tv.
rule(c9, prefer(c8, c7), []).
rule(c9b, prefer(c8b, c7), []).
complement(stay_home, go_out).
complement(go_out, stay_home).
───────────────────────────────────────────────────────────────────────
## COMMON MISTAKES TO AVOID
1. NEVER put contextual conditions in base rules. Base rules must be maximally general. Contextual reasons belong exclusively in preference rules and meta-preferences.
2. NEVER mix c and p rules inside a prefer/2 argument.
Wrong: rule(c4, prefer(p2, c2), []).
Right: rule(c4, prefer(c1, c2), []).
3. NEVER write a meta-preference between two rules that do NOT express OPPOSITE preferences about THE SAME PAIR of actions.
This is the most critical correctness check — a meta-preference between non-conflicting rules is always wrong.
Wrong: rule(c1, prefer(p3, p2), []).
% p3: prefer(r3,r4), p2: prefer(r4,r2) — different pairs!
Right: rule(c1, prefer(p3, p4), []).
% p3: prefer(r3,r4), p4: prefer(r4,r3) — same pair, opposite ✓
4. NEVER confuse a preference ordering chain with a conflict.
A > B > C expressed as p_AB and p_BC is NOT a conflict between p_AB and p_BC. No meta-preference between them is needed or valid.
5. NEVER write a meta-preference resolver whose two resolved rules express the SAME preference direction — they would not be in genuine conflict and the resolver above them would be meaningless.
Always verify the OPPOSITION CONSTRAINT and SAME PAIR constraint before writing any resolver.
6. NEVER add a body to unconditional meta-preferences unless the conflict only arises when the premises of the conflicting preference rules form a coherent simultaneously-true scenario.
7. NEVER declare as abducible any fact that appears in a rule body.
Abducibles and beliefs ONLY appear in [].
8. NEVER confuse the three categories of non-observable information:
- Derived observable fact: computed from mutually exclusive arithmetic/logical conditions → directly in rule body only
- Belief: defeasible, can be derived in conflicting ways → [] + rule structure
- Abducible: atomic assumption, no derivation possible → [] + abducible/2 declaration
9. NEVER put a derived observable fact (e.g. CO > PO vs CO =< PO) in [] or declare it as abducible. It is non-defeasible by arithmetic — belongs directly in the rule body.
10. NEVER declare a belief as an abducible if it has its own rule/preference/meta-preference structure.
11. If no information appears in [] in any rule, do NOT declare any abducibles.
12. NEVER create separate derived predicates for arithmetic — put conditions directly in the rule body.
13. NEVER combine rules from different preference chains in a single meta-preference — each chain handles one specific pair of actions and must remain independent.
14. NEVER apply an exception meta-preference to a parallel branch it was not explicitly associated with in the text.
15. ALWAYS declare complement pairs in BOTH directions and for ALL pairs when more than two actions are possible. Use wildcards for parameterised conclusions: complement(make_concession(_), ...).
16. ALWAYS accumulate ALL previous conditions AND beliefs/abducibles when adding a new exception level. Never start fresh at any level.
17. ALWAYS ask at every new level:
(a) Does this condition REVERSE a preference at a lower level?
YES → new c level, OPPOSITE direction, SAME PAIR
NO → same level, add to existing rule body
(b) Are the two rules to be resolved about THE SAME PAIR?
YES → meta-preference is valid
NO → do NOT write a meta-preference
18. ALWAYS verify the preference alternation pattern — at each level the exception rule must express the OPPOSITE preference direction to the rule it overrides AND concern THE SAME PAIR of actions. TWO failure modes: same direction OR different pairs.
19. When three or more actions are possible, create one independent preference chain per conflicting pair of base rules. Rules from different chains NEVER appear together in a meta-preference.
20. Rules with different premises and different conclusions are introduced in pairs ONLY when the union of their premises is a coherent/possible scenario. If premises are mutually exclusive, no conflict exists and no first-level preference is needed.
21. A conditional meta-preference body is always the UNION of:
(a) all conditions of the two preference rules it resolves
(b) its own specific condition (if any)
Its [] is always the UNION of:
(a) all beliefs/abducibles of the two rules it resolves
(b) its own specific beliefs/abducibles (if any)
Both are then inherited cumulatively by all higher levels.
22. Beliefs/abducibles can appear in the [] of ANY rule — base rules, first-level preferences AND meta-preferences alike.
23. Belief reasoning chains (r/p/c rules for beliefs) are completely independent from decision reasoning chains — they NEVER mix.
"""

GORGIAS_CORRECTION_TEMPLATE = """
:-dynamic weather_ok/0, rainy_day/0.

rule(r1, stay_home, []) :- weather_ok.
rule(r2, go_out, []) :- weather_ok.
rule(p1, prefer(r2, r1), []).
rule(p2, prefer(r1, r2), []) :- rainy_day.
rule(c1, prefer(p2, p1), []).

complement(stay_home, go_out).
complement(go_out, stay_home).

abducible(rainy_day, []).
abducible(neg(rainy_day), []).
"""


def build_intent_extraction_prompt() -> str:
	return (
		"You are an intent extractor for a Gorgias code assistant. "
		"Read the conversation and extract the user's current intent for a Gorgias translation task. "
		"Return only valid JSON with this shape: "
		'{"confidence": number from 0 to 1, "intents": ["bullet point 1", "bullet point 2", ...]}. '
		"Keep the intents concise, ordered, and aligned with the order the code would be written. "
		"Do not generate Gorgias code. Do not include explanations outside JSON."
	)


def build_code_correction_prompt(intents: list[str], confidence: float, baseline_code: str) -> str:
	intent_lines = "\n".join(f"- {intent}" for intent in intents)
	return (
		"You are an expert in the Gorgias argumentation framework. "
		"Your job is to revise the provided syntactically correct baseline Gorgias code so it satisfies the extracted user intents while keeping the code syntactically correct. "
		"Use the reference spec and treat the baseline code as editable scaffolding. Keep only what is needed for the current intents.\n\n"
		"STRICT MINIMALITY REQUIREMENT:\n"
		"- The output must satisfy ONLY the extracted user intents.\n"
		"- Remove all unrelated baseline/template artifacts (rules, facts, complements, abducibles, preferences).\n"
		"- If an element is not required by the current intents, it must not appear in the final code.\n\n"
		f"Reference spec:\n{GORGIAS_SPEC_2}\n\n"
		f"Baseline code to correct:\n{baseline_code}\n\n"
		"Extracted user intents:\n"
		f"{intent_lines}\n\n"
		f"Extractor confidence: {confidence:.2f}\n\n"
		"Return only valid JSON with exactly these keys: \"message\" and \"code\". "
		"The message should be a short technical summary of the final generated code only (what rules/prefs it contains and how they satisfy intent). "
		"Do not describe edits to prior code, removals, or template cleanup history. "
		"The code must be complete and syntactically correct Gorgias Prolog."
	)



GORGIAS_SPEC_2 = """
You are an expert in the Gorgias argumentation framework. Your task is to translate a
natural language decision scenario into valid Gorgias code.
## GORGIAS CODE STRUCTURE
A Gorgias program consists of the following elements in this exact order:
1. Dynamic declarations
2. Base rules (for both decisions and beliefs)
3. First-level preferences and meta-preferences (for both decisions and beliefs)
4. Complement declarations
5. Abducible declarations (only if needed)
───────────────────────────────────────────────────────────────────────
### 1. Dynamic declarations
Declare ALL observable runtime facts:
:-dynamic fact1/0, fact2/0, fact3/0.
NEVER declare as dynamic any information that appears in the []
of any rule (base, preference or meta-preference) — those are
beliefs or abducibles, not observable facts.
───────────────────────────────────────────────────────────────────────
### 2. Base rules (r rules)
Rules have the form:
rule(RuleID, Conclusion, [Beliefs/Abducibles]) :- Conditions.
- RuleID: unique identifier (r1, r2, ...)
- Conclusion: a decision/action (e.g. go_out, stay_home) OR a belief
(e.g. it_will_rain, sunny_day). When an action involves a computed
value (e.g. a negotiated price), represent it as a parameterised
conclusion: make_concession(NCO).
- [Beliefs/Abducibles]: list of belief names or abducible assumptions
involved in this rule. These are defeasible pieces of knowledge
that:
* Cannot be directly observed as hard facts
* Beliefs can themselves be derived through base rules and
first-level preferences — they have their own rule structure
* Abducibles are atomic assumptions with no rule structure
* Both are named in the [] of every rule they are involved in,
whether that rule is an r, p or c rule
- Conditions: observable facts in the rule body (after :-)
- Arithmetic conditions are placed DIRECTLY in the rule body,
never as separate derived predicates.
- r rules ONLY reference actions or beliefs as conclusions.
CRITICAL — BASE RULES MUST BE MAXIMALLY GENERAL:
Base rules express ONLY what actions are POSSIBLE under the
triggering condition — nothing more. They must NOT include
contextual reasons that make one action preferable over another.
WRONG — contextual condition in base rule:
rule(r2, get_restaurant, []) :- day_off, sunny_day.
rule(r3, get_cinema, []) :- day_off, oscar_winner_movie.
RIGHT — maximally general base rules:
rule(r1, stay_home, []) :- day_off.
rule(r2, get_restaurant, []) :- day_off.
rule(r3, get_cinema, []) :- day_off.
Contextual reasons that make one action preferable over another
belong EXCLUSIVELY in the preference rules and meta-preferences
— never in base rules.
WHEN ARE RULES INTRODUCED IN PAIRS (OR GROUPS)?
Rules with DIFFERENT conclusions are introduced in pairs (or groups
when more than two actions are possible) — and their conflicts
resolved by first-level preferences — in TWO situations:
SITUATION 1 — Same premises, different conclusions:
All rules share exactly the same conditions. Conflicts arise
whenever the shared condition is true and contextual reasons
make multiple options applicable. The first-level preferences
carry the contextual conditions.
SITUATION 2 — Different premises, different conclusions:
Rules have different conditions but the UNION of their premises
forms a COHERENT/POSSIBLE scenario. The conflict only arises
in that overlapping scenario and the first-level preference
carries the union of both sets of premises.
If the premises of two rules are MUTUALLY EXCLUSIVE (can never
be simultaneously true), there is no conflict and no first-level
preference is needed between them.
OBSERVABLE FACTS vs BELIEFS vs ABDUCIBLES:
Three distinct categories — never confuse them:
OBSERVABLE FACT:
Directly known or computable at runtime without ambiguity.
Goes in :-dynamic declarations and rule bodies.
DERIVED OBSERVABLE FACT (computed, non-defeasible):
Computed from arithmetic or logical conditions that are
mutually exclusive by construction — no conflict possible.
Goes DIRECTLY in rule bodies as arithmetic conditions.
NEVER put in [] and NEVER declare as abducible.
BELIEF (defeasible derived knowledge):
Can be derived in CONFLICTING ways that require preference
rules to resolve. Has its own rule/preference/meta-preference
structure. Named in [] of every rule it is involved in.
ABDUCIBLE (atomic defeasible assumption):
Cannot be observed or derived — must be assumed (i.e. TRUE or FALSE).
No rule structure of its own.
Named in [] of rules it is involved in.
Declared with abducible/2.
KEY TEST — ask these questions in order:
1. Is it directly observable at runtime? → :-dynamic + body
2. Is it computable from mutually exclusive arithmetic/logical
conditions with no possible conflict? → body only
3. Can it be derived in conflicting ways requiring preference
resolution? → [] + belief rule structure
4. Must it be assumed with no derivation possible? → [] + abducible
───────────────────────────────────────────────────────────────────────
### 3. First-level preferences (p rules) and meta-preferences (c rules)
TERMINOLOGY:
- p rules = FIRST-LEVEL PREFERENCES
They resolve conflicts between base rules (r rules).
→ prefer(ri, rj)
- c rules = META-PREFERENCES
They resolve conflicts between first-level preferences (p rules)
or between other meta-preferences (c rules).
→ prefer(px, py) or prefer(cx, cy)
The hierarchy is ordered from lowest to highest priority:
r1, r2, r3 base rules (lowest priority)
p1 default first-level preference
p2 exception first-level preference
c1 meta-preference resolving p1/p2
c2 exception meta-preference
c3 meta-preference resolving c1/c2
c4 exception meta-preference
c5 meta-preference resolving c3/c4
... (highest priority)
GENERAL FORM (applies to ALL p and c rules):
rule(ID, prefer(A, B), [Beliefs/Abducibles]) :- Conditions.
The [Beliefs/Abducibles] slot is available in EVERY rule —
base rules, first-level preferences AND meta-preferences alike.
LEVEL SEPARATION — the most critical structural rule:
- p rules: preferences between r rules ONLY → prefer(ri, rj)
- c rules: preferences between p or c rules ONLY →
prefer(px, py) or prefer(cx, cy)
- NEVER mix levels: a c rule must NEVER reference an r rule
directly, and a p rule must NEVER reference a c rule.
- NEVER write prefer(p_x, c_y) or prefer(c_x, p_y) — always wrong.
This level separation applies INDEPENDENTLY to:
(a) the decision/action reasoning chain
(b) the belief reasoning chain
Each chain has its own r, p, c rules and they never mix.
───────────────────────────────────────────────────────────────────────
### CONFLICT EXISTENCE CONSTRAINT AND OPPOSITION
CONFLICT EXISTENCE CONSTRAINT — the most fundamental rule:
A meta-preference can ONLY be placed between two preference rules
that express OPPOSITE preferences about THE SAME PAIR of rules.
prefer(A, B) conflicts with prefer(B, A) — SAME PAIR, OPPOSITE ✓
prefer(A, B) does NOT conflict with prefer(B, C) — DIFFERENT PAIRS ✗
prefer(A, B) does NOT conflict with prefer(C, D) — DIFFERENT PAIRS ✗
WHAT IS THE REAL OPPOSITE OF A RULE?
Two rules are genuine opposites IF AND ONLY IF they express
prefer(A,B) and prefer(B,A) for the EXACT SAME A and B.
c3 = prefer(c2, c1) → real opposite = prefer(c1, c2) = c4 ✓
c5 = prefer(c4, c3) → real opposite = prefer(c3, c4) = c6 ✓
CRITICAL — DO NOT CONFUSE DIRECTIONAL OUTCOME WITH STRUCTURAL PAIR:
A rule's "opposite" is determined SOLELY by its structural pair
(A,B) reversed — NOT by which final action it ultimately favours.
WRONG reasoning:
c2 = prefer(p1,p2) → favours waiting_room
c4 = prefer(c1,c2) → favours immediate_care
"c4 is opposite of c2 because they favour different actions" ✗
These are about DIFFERENT PAIRS: (p1,p2) vs (c1,c2)
RIGHT reasoning:
c3 = prefer(c2,c1) — pair is (c2,c1)
c4 = prefer(c1,c2) — pair is (c1,c2) = same pair reversed ✓
c4 IS the real opposite of c3
PREFERENCE ORDERING CHAINS vs CONFLICTS:
When the text establishes a total ordering among three or more
actions (e.g. A > B > C), this is expressed as INDEPENDENT
preference rules — one per pair — with NO meta-preference
between them:
p_AB: prefer(rA, rB) — A beats B
p_BC: prefer(rB, rC) — B beats C
% NO meta-preference between p_AB and p_BC — they are not in conflict
% because they are about DIFFERENT PAIRS
A meta-preference is only needed when TWO rules express
CONFLICTING preferences about THE SAME PAIR.
───────────────────────────────────────────────────────────────────────
### PREFERENCE ALTERNATION PATTERN
A key structural property of correctly encoded Gorgias hierarchies
is that preferences ALTERNATE direction at each level AND always
concern THE SAME PAIR as the unconditional resolver at the same level.
THE CORE RULE FOR EACH NEW EXCEPTION LEVEL:
A new conditional c rule at any level must express the OPPOSITE
preference to the UNCONDITIONAL RESOLVER AT THE SAME LEVEL —
not the opposite of the conditional rule one level below.
CORRECT alternation:
p1 prefer(r1,r2) → action_B wins [default]
p2 prefer(r2,r1) → action_A wins [exception — opposite of p1]
c1 prefer(p2,p1) → action_A wins [unconditional — pair (p2,p1)]
c2 prefer(p1,p2) → action_B wins [opposite of c1 — pair (p1,p2)
= same pair as c1 reversed ✓]
c3 prefer(c2,c1) → action_B wins [unconditional — pair (c2,c1)]
c4 prefer(c1,c2) → action_A wins [opposite of c3 — pair (c1,c2)
= same pair as c3 reversed ✓]
c5 prefer(c4,c3) → action_A wins [unconditional — pair (c4,c3)]
c6 prefer(c3,c4) → action_B wins [opposite of c5 — pair (c3,c4)
= same pair as c5 reversed ✓]
c7 prefer(c6,c5) → action_B wins [unconditional — pair (c6,c5)]
VERIFICATION CHECKLIST for each new conditional c rule:
1. Identify the unconditional resolver at the same level (e.g. c5)
2. Note its pair: c5 = prefer(c4,c3) → pair is (c4,c3)
3. The new rule must express prefer(c3,c4) — same pair, reversed ✓
4. Verify they are genuine opposites: prefer(c4,c3) vs prefer(c3,c4) ✓
5. The resolver above them: prefer(c6,c5) — c6 and c5 are opposites
about pair (c3,c4) vs (c4,c3) ✓
TWO FAILURE MODES to check at every level:
1. Same direction: two adjacent rules favour the same action
→ no genuine conflict → resolver is meaningless
2. Different pairs: two rules reference different pairs of arguments
→ no genuine conflict → resolver is meaningless
COMMON MISTAKE — confusing the pair:
c5 = prefer(c4,c3) unconditional resolver at level 3
c6 = prefer(c2,c1) WRONG — pair is (c2,c1) ≠ (c4,c3)
"c6 reverses the decision to action_B" is not enough —
it must reverse c5 structurally, i.e. express prefer(c3,c4)
───────────────────────────────────────────────────────────────────────
### 4. Cumulative context rule — when to add a new level vs same level
The key question at every step is:
Does this new condition REVERSE a preference already established
at a lower-priority level of the hierarchy?
YES — it introduces a NEW meta-preference level (new c rule):
Signal: "however", "unless", "except when", "despite"
The new conditional c rule must express the OPPOSITE of the
UNCONDITIONAL RESOLVER AT THE SAME LEVEL — verified by checking
that both reference the same pair with reversed arguments.
NO — it stays at the SAME level, added to existing rule body:
Signal: "and", "also", "both"
Each new exception level inherits ALL conditions AND ALL
beliefs/abducibles of ALL previous levels, adding its own
new condition on top:
p1 [bel_A] :- cond_A.
p2 [bel_B] :- cond_B, cond_C.
c1 [bel_A, bel_B] :- cond_A, cond_B, cond_C.
% union of p1+p2 — conditional resolver
c2 [bel_A, bel_B] :- cond_A, cond_B, cond_C, cond_D.
% inherits c1 union + adds cond_D
% opposite of c1: prefer(p1,p2) vs prefer(p2,p1) ✓
c3 [] % unconditional: prefer(c2,c1) — pair (c2,c1)
c4 [bel_A, bel_B] :- cond_A, cond_B, cond_C, cond_D, cond_E.
% inherits c1+c2 union + adds cond_E
% opposite of c3: prefer(c1,c2) vs prefer(c2,c1) ✓
c5 [] % unconditional: prefer(c4,c3) — pair (c4,c3)
c6 [bel_A, bel_B] :- cond_A, cond_B, cond_C, cond_D, cond_E, cond_F.
% inherits all + adds cond_F
% opposite of c5: prefer(c3,c4) vs prefer(c4,c3) ✓
c7 [] % unconditional: prefer(c6,c5) — pair (c6,c5)
───────────────────────────────────────────────────────────────────────
### 5. Meta-preference types
TYPE A — UNCONDITIONAL (the default):
One preference always beats the other regardless of any context.
These meta-preferences have NO body.
The two rules they resolve MUST be genuine opposites about THE
SAME PAIR (see CONFLICT EXISTENCE CONSTRAINT above).
rule(c1, prefer(p2, p1), []).
rule(c3, prefer(c2, c1), []).
rule(c5, prefer(c4, c3), []).
TYPE B — CONDITIONAL (exception):
The conflict only arises under SPECIFIC circumstances.
There are two cases:
CASE 1 — Same premises, different conclusions at preference level:
The meta-preference carries the shared condition.
CASE 2 — Different premises that can be simultaneously true:
The body of the meta-preference is the UNION of:
(a) all conditions of the two preference rules it resolves
(b) its own specific condition (if any)
The [] carries the UNION of:
(a) all beliefs/abducibles of the two rules it resolves
(b) its own specific beliefs/abducibles (if any)
Both propagate cumulatively into all higher levels.
When in doubt, meta-preferences are unconditional.
───────────────────────────────────────────────────────────────────────
### 6. Alternative triggers at the same level
When two independent conditions lead to the same preference at the
same level, create parallel meta-preferences with their own
unconditional resolvers:
rule(c2, prefer(px, py), []) :- cond_A, cond_B.
rule(c2b, prefer(px, py), []) :- cond_A, cond_C.
rule(c3, prefer(c2, c1), []).
rule(c3b, prefer(c2b, c1), []).
Both c2 and c2b must express the SAME preference direction
AND about THE SAME PAIR. Do NOT link parallel branches unless
the text explicitly states an interaction between them.
───────────────────────────────────────────────────────────────────────
### 7. Handling more than two actions
When a scenario has three or more possible actions, a separate
preference chain is needed for EACH CONFLICTING PAIR of base rules.
Each chain is entirely independent and handles ONE specific pair.
Rules from different chains are NEVER combined in a meta-preference.
Within each chain the conflict existence constraint, opposition
constraint, and alternation pattern apply independently.
Chains only interact when the text explicitly states a preference
between them.
───────────────────────────────────────────────────────────────────────
### 8. Complement declarations
Declare ALL mutually exclusive pairs of conclusions in BOTH directions:
complement(action1, action2).
complement(action2, action1).
When more than two actions are possible, declare ALL pairs.
When actions are parameterised, use wildcards:
complement(make_concession(_), accept).
This applies to both decisions and beliefs.
───────────────────────────────────────────────────────────────────────
### 9. Abducible declarations
Abducibles are the simplest form of belief — atomic assumptions with
no further rule structure. They appear in the [] of ANY rule and are
declared with both positive and negative forms.
CRITICAL RULES:
- An abducible is ONLY what appears in the [] of some rule AND has
no rule structure of its own.
- If a belief has its own rule structure → it is a belief with rules,
NOT a simple abducible.
- If no information appears in [] in any rule → NO abducibles.
- NEVER declare as abducible any fact that appears in a rule body.
- NEVER declare as abducible any derived fact computed from mutually
exclusive arithmetic/logical conditions.
- Always declare both positive and negative forms:
abducible(assumption, []).
abducible(neg(assumption), []).
───────────────────────────────────────────────────────────────────────
## FULL STRUCTURAL PATTERN
:-dynamic ... observable facts ONLY — never beliefs
% ── BELIEF RULES (if beliefs are present) ──────────────────────
rule(r_b1, belief_A, []) :- source_1.
rule(r_b2, belief_B, []) :- source_2.
rule(p_b1, prefer(r_b1, r_b2), []) :- source_1, source_2.
complement(belief_A, belief_B).
complement(belief_B, belief_A).
% ── DECISION RULES ──────────────────────────────────────────────
% Base rules — maximally general, NO contextual conditions
rule(r1, action_A, []) :- triggering_condition.
rule(r2, action_B, []) :- triggering_condition.
% p1: default [action_B wins]
rule(p1, prefer(r2, r1), []).
% p2: exception [action_A wins — opposite of p1: prefer(r1,r2)
% vs prefer(r2,r1), same pair reversed ✓]
rule(p2, prefer(r1, r2), []) :- cond_A.
% c1: unconditional [action_A wins]
% pair: (p2,p1) — p2 and p1 are genuine opposites ✓
rule(c1, prefer(p2, p1), []).
% c2: exception [action_B wins]
% opposite of c1: prefer(p1,p2) vs prefer(p2,p1) ✓ same pair ✓
% cumulative: cond_A + cond_B
rule(c2, prefer(p1, p2), []) :- cond_A, cond_B.
% c3: unconditional [action_B wins]
% pair: (c2,c1) — c2 and c1 are genuine opposites ✓
rule(c3, prefer(c2, c1), []).
% c4: exception [action_A wins]
% opposite of c3: prefer(c1,c2) vs prefer(c2,c1) ✓ same pair ✓
% cumulative: cond_A + cond_B + cond_C
rule(c4, prefer(c1, c2), []) :- cond_A, cond_B, cond_C.
% c5: unconditional [action_A wins]
% pair: (c4,c3) — c4 and c3 are genuine opposites ✓
rule(c5, prefer(c4, c3), []).
% c6: exception [action_B wins]
% opposite of c5: prefer(c3,c4) vs prefer(c4,c3) ✓ same pair ✓
% cumulative: cond_A + cond_B + cond_C + cond_D
rule(c6, prefer(c3, c4), []) :- cond_A, cond_B, cond_C, cond_D.
% c7: unconditional [action_B wins]
% pair: (c6,c5) — c6 and c5 are genuine opposites ✓
rule(c7, prefer(c6, c5), []).
% Complements — always both directions
complement(action_A, action_B).
complement(action_B, action_A).
% Abducibles — ONLY if something appears in [] with no rule structure
abducible(belief_x, []).
abducible(neg(belief_x), []).
───────────────────────────────────────────────────────────────────────
## TRANSLATION GUIDE
| Natural language pattern | Gorgias element |
|---------------------------------------------|-----------------------------------|
| "When X, possible actions are A, B, C" | r1, r2, r3 — maximally general |
| "Sunny day is a reason for restaurant" | context in p rule — NOT in r rule |
| "Generally I prefer A" | p1 default, no body |
| "But if X AND Y, I prefer B" | p2 exception — same level |
| "But if X... However if also Y" | p2 for X, new c level for Y |
| "One always beats the other" | unconditional meta-preference |
| "Same condition, two conclusions" | p1 conditional, shared cond |
| "When both situations occur" | conditional meta-preference, |
| | body = union of premises |
| "However / unless / despite / except when" | new c level — new conditional |
| | rule opposite to the unconditional|
| | resolver AT THE SAME LEVEL |
| "Two independent reasons for same choice" | parallel branches, same direction |
| | and same pair |
| "Three or more possible actions" | one chain per conflicting pair |
| "Action involves a computed value" | parameterised conclusion |
| "I believe / I think / it seems" | belief → [] + rule structure |
| "Computed from mutually exclusive | derived observable fact → |
| arithmetic conditions" | directly in rule body, never [] |
| "Directly observable fact" | :-dynamic + rule body |
───────────────────────────────────────────────────────────────────────
## WORKED EXAMPLE
Input text:
"An agent has two options when the weather is nice: stay home or go
out. Default is to go out. However if they have homework for an exam
they prefer to stay home. They can go out either when the exam date
is not close or when the material is not extensive. In the first case
if they are sick they prefer to stay home. However if they have no
fever they can go out. If they have no fever they may stay home if
it is raining or if there is a nice movie on tv."
Output:
:-dynamic nice_weather/0, homework_exam/0,
exam_date_not_close/0, sick/0,
no_fever/0, its_raining/0,
nice_movie_on_tv/0.
rule(r1, stay_home, []) :- nice_weather.
rule(r2, go_out, []) :- nice_weather.
% p1 and p2: genuine opposites, same pair (r1,r2)/(r2,r1) ✓
rule(p1, prefer(r2, r1), []).
rule(p2, prefer(r1, r2), []) :- homework_exam.
% c1: pair (p2,p1) — p2 and p1 genuine opposites ✓
rule(c1, prefer(p2, p1), []).
% c2: opposite of c1 — pair (p1,p2) vs (p2,p1) ✓ same pair reversed ✓
rule(c2, prefer(p1, p2), []) :- homework_exam, exam_date_not_close.
% c3: pair (c2,c1) — c2 and c1 genuine opposites ✓
rule(c3, prefer(c2, c1), []).
% c4: opposite of c3 — pair (c1,c2) vs (c2,c1) ✓ same pair reversed ✓
rule(c4, prefer(c1, c2), []) :- homework_exam,
exam_date_not_close, sick.
% c5: pair (c4,c3) — c4 and c3 genuine opposites ✓
rule(c5, prefer(c4, c3), []).
% c6: opposite of c5 — pair (c3,c4) vs (c4,c3) ✓ same pair reversed ✓
rule(c6, prefer(c3, c4), []) :- homework_exam,
exam_date_not_close,
sick, no_fever.
% c7: pair (c6,c5) — c6 and c5 genuine opposites ✓
rule(c7, prefer(c6, c5), []).
% c8: opposite of c7 — pair (c5,c6) vs (c6,c5) ✓ same pair reversed ✓
rule(c8, prefer(c5, c6), []) :- homework_exam,
exam_date_not_close,
sick, no_fever, its_raining.
rule(c8b, prefer(c5, c6), []) :- homework_exam,
exam_date_not_close,
sick, no_fever, nice_movie_on_tv.
% c9/c9b: pair (c8,c7)/(c8b,c7) — genuine opposites ✓
rule(c9, prefer(c8, c7), []).
rule(c9b, prefer(c8b, c7), []).
complement(stay_home, go_out).
complement(go_out, stay_home).
───────────────────────────────────────────────────────────────────────
## COMMON MISTAKES TO AVOID
1. NEVER put contextual conditions in base rules. Base rules must
be maximally general.
2. NEVER mix c and p rules inside a prefer/2 argument.
Wrong: rule(c4, prefer(p2, c2), []).
Right: rule(c4, prefer(c1, c2), []).
3. NEVER write a meta-preference between two rules that are not
genuine opposites about THE SAME PAIR.
Wrong: c5=prefer(c4,c3), c6=prefer(c2,c1)
→ different pairs (c4,c3) vs (c2,c1) — not opposites!
Right: c5=prefer(c4,c3), c6=prefer(c3,c4)
→ same pair reversed ✓
4. NEVER identify two rules as opposites based on which final
action they ultimately favour. Opposites are determined SOLELY
by structural pair reversal: prefer(A,B) vs prefer(B,A).
Wrong: "c2=prefer(p1,p2) and c4=prefer(c1,c2) are opposites
because both favour waiting_room"
Right: c4's real opposite is c3=prefer(c2,c1) — same pair ✓
5. NEVER write a new conditional c rule as the opposite of the
conditional rule one level below. It must be the opposite of
the UNCONDITIONAL RESOLVER AT THE SAME LEVEL.
Wrong: c5=prefer(c4,c3) [unconditional], then
c6=prefer(c2,c1) "opposite of c4=prefer(c1,c2)"
Right: c6=prefer(c3,c4) — opposite of c5=prefer(c4,c3) ✓
6. BEFORE writing any new c rule, apply this checklist:
(a) Identify the unconditional resolver at the same level
(b) Note its pair (A,B)
(c) Write the new rule as prefer(B,A) — same pair reversed
(d) Verify: are these genuine opposites? prefer(A,B) vs prefer(B,A)?
(e) Write the resolver above: prefer(new_rule, unconditional) ✓
7. NEVER add a body to unconditional resolvers unless the conflict
only arises under specific circumstances.
8. NEVER declare as abducible any fact that appears in a rule body.
9. NEVER confuse the three categories of non-observable information:
- Derived observable fact → directly in rule body only
- Belief → [] + rule structure
- Abducible → [] + abducible/2 declaration
10. NEVER put a derived observable fact (e.g. CO > PO vs CO =< PO)
in [] or declare it as abducible.
11. NEVER declare a belief as an abducible if it has its own
rule/preference/meta-preference structure.
12. If no information appears in [] in any rule → NO abducibles.
13. NEVER create separate derived predicates for arithmetic — put
conditions directly in the rule body.
14. NEVER apply an exception meta-preference to a parallel branch
it was not explicitly associated with in the text.
15. ALWAYS declare complement pairs in BOTH directions and for ALL
pairs when more than two actions are possible.
16. ALWAYS accumulate ALL previous conditions AND beliefs/abducibles
when adding a new exception level. Never start fresh.
17. ALWAYS ask at every new level:
(a) Which unconditional resolver is at this same level?
(b) What is its pair (A,B)?
(c) My new conditional rule must express prefer(B,A) ✓
(d) Are they genuine opposites? Same pair, reversed? ✓
18. When three or more actions are possible, create one independent
preference chain per conflicting pair. Chains NEVER appear
together in a meta-preference.
19. Rules with different premises and different conclusions are
introduced in pairs ONLY when the union of their premises is
a coherent/possible scenario.
20. A conditional meta-preference body is always the UNION of:
(a) all conditions of the two rules it resolves
(b) its own specific condition (if any)
Its [] is the UNION of:
(a) all beliefs/abducibles of the two rules it resolves
(b) its own specific beliefs/abducibles (if any)
Both inherited cumulatively by all higher levels.
21. Beliefs/abducibles can appear in the [] of ANY rule — base
rules, first-level preferences AND meta-preferences alike.
22. Belief reasoning chains are completely independent from decision
reasoning chains — they NEVER mix.
```
---
Would you like to test this updated prompt on a new scenario?
"""