# Adding a module

NUS Skill Issue is the organisation. Each module is an independent repository containing one skill. Skill Issue Labs is the umbrella brand.

A module skill should change how an assistant handles that module's work. It should carry the terminology, distinctions, source rules and recurring workflows that generic prompting misses.

## Minimum package

Create a separate repository under the NUS Skill Issue organisation for each module. Use the lowercase module code as the repository and skill name where available. Put `SKILL.md` at the repository root with a matching frontmatter name and a concise description of when it applies. Put longer, conditional guidance in `references/`. Add scripts only for repeatable operations that benefit from deterministic handling. Keep course files and student submissions outside the distributed package unless redistribution is authorised.

Add a `module.json` file containing the module code, verified title, skill path, organisation URL when known, concrete capabilities, current status, official course URL, verification date, academic year or semester when established, and known gaps. Use `null` for an unknown semester. Do not infer semester coverage from a file's creation date.

## Separate three kinds of guidance

| Kind | Example | Evidence needed |
|---|---|---|
| Course requirement | A specified word limit or required method | Current brief, rubric or tutor instruction with its date |
| Framework knowledge | What an assumption is | Course material or an identifiable primary source |
| Package convention | A suggested review sequence | Explain its purpose and allow adaptation |

The module code is a routing boundary. An ES2631 writing request can use ES2631. A generic request for a PEEL paragraph should not silently inherit ES2631 assessment assumptions.

## Review before widening use

Check one ordinary task, one narrow task, one missing information case and one conflicting source case. For instance, a request for one paragraph must stay one paragraph even if a reference illustrates a full essay. A request using an older brief must not produce a claim about this semester's deadline.

Record the prompt, materials, observed behaviour, reviewer and limitations in `evals/`. Synthetic fixtures are suitable for checks and should be labelled. A successful script test is evidence about the script, not evidence of better grades or better model performance.

Use `experimental` for an initial package. Use `reviewed` only after a documented independent behaviour review and source check within the declared scope. Reserve `maintained` for modules with an identified maintainer and a current term review process. Do not describe a whole module as complete when only one assignment type is covered.

## Course changes

Keep stable reasoning guidance in the skill. Store term specific rules in a dated reference only when they are known. When a new brief conflicts with an older one, identify the conflict and use the applicable newer instruction. If applicability is unclear, ask for the missing detail while continuing work that does not depend on it.

## Sharing

Keep the core skill portable. Host metadata can sit in `agents/`, while connectors and host specific installation instructions remain optional. Do not make an account connection or a paid product a silent prerequisite.

Before public distribution, record who supplied or authored the content and resolve the licence for reused material. Do not bundle private course readings, Canvas exports, marked submissions or personal data as examples. Use a synthetic example where it tests the same behaviour.
