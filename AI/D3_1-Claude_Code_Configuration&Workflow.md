# Domain 3 · Task 3.1 — Claude Code Configuration & Workflows
## CLAUDE.md Hierarchy, Scoping, Imports, Rules, and Diagnostics: A Complete Study Guide for CCAR-F

> **Task statement covered:** *Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization.*
> **Docs verified against:** `code.claude.com/docs/en/memory` and `code.claude.com/docs/en/debug-your-config`, fetched on **20 October 2026**. Claude Code ships frequently, so re-check version-specific details before the exam.

---

## How to Read This Document

### Evidence labels

Every non-trivial claim carries one of these labels so you always know how much weight to give it.

| Label | Meaning |
|---|---|
| 📘 **Documented** | Stated in the official Claude Code documentation. Source tag in brackets, e.g. `[S1]`. |
| 🛠 **Recommended** | Good engineering practice. Not stated as a rule by the docs. |
| 🧩 **Teaching model** | A simplification built to help you reason. Not literal product behavior. |
| 🎓 **Exam-guide claim** | Reported by community study material about the exam. **I could not open the official exam-guide PDF**, so treat these as *probable*, not confirmed. |
| ❓ **Uncertain** | Not verifiable from the sources I read, or the sources disagree. Test it yourself in a scratch repo. |

### A note on the exam name

You wrote **CCAR-F**. Every public source I found calls the credential **CCA-F** (*Claude Certified Architect – Foundations*) `[S5]`. I assume they are the same exam. The exam guide itself is distributed through Anthropic's learning platform, which I could not access. That means **I cannot quote the exact "Knowledge of / Skills in" bullets of Task 3.1**. Instead, this guide is built from the ten learning outcomes you gave me, which closely match what community summaries say Task 3.1 covers: user vs project vs directory hierarchy, `@import`, `.claude/rules/`, diagnosing "teammate doesn't see my instructions" as a scope problem, and `/memory` `[S6][S7]`.

### Sources

Sources are listed at the end (Section "Source List"). Tags: `[S1]` memory docs, `[S2]` debug-your-config docs, `[S3]`–`[S4]` related official pages, `[S5]`–`[S8]` community exam material (unofficial).

---

## Table of Contents

1. [Module 1 — Claude Code and CLAUDE.md Fundamentals](#module-1--claude-code-and-claudemd-fundamentals)
2. [Module 2 — Configuration Hierarchy and Scoping](#module-2--configuration-hierarchy-and-scoping)
3. [Module 3 — The @import Syntax and Modular Instructions](#module-3--the-import-syntax-and-modular-instructions)
4. [Module 4 — Organizing Instructions with .claude/rules/](#module-4--organizing-instructions-with-clauderules)
5. [Module 5 — Diagnosing Configuration Problems](#module-5--diagnosing-configuration-problems)
6. [Module 6 — Using /memory to Investigate Loaded Instructions](#module-6--using-memory-to-investigate-loaded-instructions)
7. [Module 7 — Practical Monorepo Case Study](#module-7--practical-monorepo-case-study)
8. [Module 8 — Hands-On Labs](#module-8--hands-on-labs)
9. [Module 9 — Certification Exam Preparation](#module-9--certification-exam-preparation)
10. [Module 10 — Assessment and Answer Key](#module-10--assessment-and-answer-key)
11. [Source List](#source-list)
12. [One-Page Revision Sheet](#one-page-revision-sheet)

---

# Module 1 — Claude Code and CLAUDE.md Fundamentals

## 1.1 What Claude Code is

**Concept.** Claude Code is Anthropic's agentic coding tool. You run it in a terminal (it is also available in desktop, IDE, and mobile surfaces) and give it a goal such as "add a pagination endpoint". It then reads files, edits files, runs commands, and iterates on test failures to reach that goal.

**How it differs from a conventional IDE assistant.**

| | Prompt-by-prompt IDE assistant | Claude Code |
|---|---|---|
| Unit of work | A single completion or chat reply | A multi-step task: read, plan, edit, run, verify |
| Knowledge of your repo | Whatever is in the open file or pasted into chat | Explores the repo itself with file and shell tools |
| Persistent guidance | Usually none, or a single global "system prompt" box | Layered instruction files that load automatically |
| Where conventions live | In your head, re-typed each time | In files that are versioned, reviewed, and shared |

**Why it matters.** An agent that works autonomously across many files needs standing context: how to build, how to test, what style to follow, what never to touch. Typing that into every prompt does not scale across sessions or teammates. `CLAUDE.md` is the mechanism built for exactly this.

> 📘 **Documented:** "Each Claude Code session begins with a fresh context window." Two mechanisms carry knowledge across sessions: **CLAUDE.md files** (instructions *you* write) and **auto memory** (notes *Claude* writes for itself) `[S1]`.

## 1.2 What CLAUDE.md is

A `CLAUDE.md` is an ordinary markdown file. Claude Code reads it at the start of a session (or, for some locations, when Claude starts working in a directory) and places its contents in Claude's context so the guidance applies to everything that follows `[S1]`.

Think of it as **the onboarding note you would hand a new teammate**. The docs say the same thing: add to it when Claude repeats a mistake, when a code review catches something Claude should have known, when you retype the same correction, or when a new teammate would need the same context `[S1]`.

### The most important caveat in the whole topic

> 📘 **Documented:** Claude treats CLAUDE.md files as **context, not enforced configuration**. CLAUDE.md content is delivered as a user message after the system prompt, and "there's no guarantee of strict compliance, especially for vague or conflicting instructions." To block an action regardless of what Claude decides, use a **PreToolUse hook** (or permissions) instead `[S1][S2]`.

Exam consequence: if a scenario says an action "must never happen" or "must run before every commit", CLAUDE.md is the wrong tool. Hooks and permissions are the guarantee layer. CLAUDE.md is the guidance layer.

## 1.3 Four things people confuse

| Concept | What it is | Who writes it | Loaded into Claude's context? | Example |
|---|---|---|---|---|
| **Instructions** (CLAUDE.md, rules) | Standing guidance for behavior | You | Yes: at launch, on demand, or when matching files are touched | "Run `pnpm test` before declaring a task done" |
| **Configuration settings** (`settings.json`) | Machine-readable switches: permissions, hooks, env vars, model | You | **No.** The client reads them; they are not prose for Claude | `permissions.deny`, `autoMemoryEnabled` |
| **Memory** (auto memory) | Notes Claude saves from your corrections and preferences | Claude | Yes: first 200 lines or 25 KB of `MEMORY.md` at session start | "User prefers pnpm over npm" |
| **Project documentation** (README, ADRs, wikis) | Human-oriented docs | Humans | **Only if** referenced by an `@import` or read by Claude during work | `docs/architecture.md` |

> 📘 **Documented:** Use settings for technical enforcement and CLAUDE.md for behavioral guidance. "Settings rules are enforced by the client regardless of what Claude decides to do. CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer." `[S1]`

📘 The word **"memory"** in Claude Code is used loosely. In docs and in the `/memory` command, it covers both CLAUDE.md-family files **and** auto memory `[S1]`. In this guide: *CLAUDE.md files* = instructions you write; *auto memory* = notes Claude writes; *memory files* = the umbrella term the UI uses.

## 1.4 How instructions influence real workflows

| Workflow | What a good CLAUDE.md contributes | Example line |
|---|---|---|
| **Coding** | Style, naming, architecture, where files go | "API handlers live in `apps/api/src/handlers/`" |
| **Testing** | Runner, command, file naming, mocking rules | "Run a single file with `pnpm vitest run <path>`" |
| **Code review** | What reviewers care about; what to flag | "Flag any `any` type introduced in a diff" |
| **Deployment** | Safe commands, environments, what needs a human | "Never run `terraform apply`; run `terraform plan` only" |

🛠 *Recommended wording rule from the docs:* write instructions concrete enough to verify. "Use 2-space indentation" beats "format code properly" `[S1]`.

## 1.5 Practical example: a repo without and with CLAUDE.md

### Without CLAUDE.md

```text
acme-shop/
├── package.json
├── pnpm-lock.yaml
├── apps/api/
└── apps/web/
```

You ask: *"Add a GET /orders/:id endpoint with tests."*

🧩 *Likely outcome (illustrative):* Claude has to infer everything. It may use `npm install` although the repo uses pnpm, pick Jest although the repo uses Vitest, put the handler in a new folder, and invent an error format. Each guess is plausible and each is wrong for this team. You correct them in chat. Tomorrow you correct them again.

### With CLAUDE.md

```text
acme-shop/
├── CLAUDE.md          ← new
├── package.json
├── pnpm-lock.yaml
├── apps/api/
└── apps/web/
```

Same request. Claude starts the session already knowing the package manager, test runner, folder conventions, and error format. The first draft is closer to mergeable.

## 1.6 A sample CLAUDE.md, explained line by line

```markdown
# Acme Shop

Monorepo: React frontend, Node.js API, shared TypeScript utilities.

## Commands
- Install: `pnpm install`
- Build all: `pnpm -r build`
- Test all: `pnpm -r test`
- Test one file: `pnpm vitest run path/to/file.test.ts`
- Lint and typecheck: `pnpm lint && pnpm typecheck`

## Layout
- `apps/web/`: React app (Vite)
- `apps/api/`: Express API
- `packages/shared/`: types and utilities used by both apps
- `infra/`: Terraform and deployment workflows

## Conventions
- TypeScript strict mode everywhere; never introduce `any`
- Use named exports, not default exports
- Run `pnpm lint && pnpm typecheck` before saying a task is done

## Boundaries
- Do not edit files under `infra/` unless the task explicitly mentions infrastructure
- Never commit directly to `main`
```

| Line(s) | Why it is there |
|---|---|
| `# Acme Shop` and the one-line summary | Orients Claude. A project identity costs few tokens and prevents wrong assumptions about the stack. |
| `## Commands` | The highest-value content. Claude cannot discover your non-standard commands reliably, and wrong commands waste whole iterations. |
| `## Layout` | Tells Claude where things belong. Keep it short; the docs note that content Claude can derive from the codebase (like full directory listings) is a candidate for trimming `[S1]`. |
| `## Conventions` | Concrete, checkable rules. "Never introduce `any`" can be verified; "write clean code" cannot. |
| "Run `pnpm lint && pnpm typecheck` before saying a task is done" | Encodes a workflow step. It is *guidance*. If you need a guarantee, use a hook. |
| `## Boundaries` | States what to avoid. Again guidance, not enforcement. For a hard block, use `permissions.deny` or a hook `[S1]`. |

🛠 Keep each file **under about 200 lines** `[S1]` (📘 target stated in the docs; longer files "consume more context and reduce adherence").

## 1.7 Common misconceptions

| Misconception | Reality |
|---|---|
| "CLAUDE.md is a config file, so Claude must obey it." | 📘 It is **context**. Adherence depends on clarity, size, and absence of conflicts `[S1]`. |
| "Every CLAUDE.md in the repo is loaded at startup." | 📘 Files in the working directory and **above** load at launch. Files in **subdirectories** load **on demand** `[S1]`. |
| "`~/.claude/CLAUDE.md` is shared with my team." | 📘 It applies only to you, in all your projects. Teams share via source control `[S1]`. |
| "Imports save context." | 📘 Imports help organization but **do not reduce context cost**, because imported files load at launch too `[S1]`. |
| "Later files always override earlier ones." | 📘 Files are **concatenated**, not overridden. Conflicting instructions: "Claude may pick one arbitrarily" `[S1]`. |
| "`/memory` tells Claude which section to prioritize." | ❌ Not a documented function. `/memory` lists and opens memory files and toggles auto memory `[S1]`. |
| "CLAUDE.md and `settings.json` are interchangeable." | ❌ Different jobs. See 1.3. |

## 1.8 Exam-relevant distinctions from this module

1. **Instructions you write** (CLAUDE.md) vs **notes Claude writes** (auto memory).
2. **Guidance** (CLAUDE.md) vs **enforcement** (settings, permissions, hooks).
3. **Personal** (`~/.claude/CLAUDE.md`, `CLAUDE.local.md`) vs **shared** (project files in Git).

---

# Module 2 — Configuration Hierarchy and Scoping

## 2.0 Four words you must keep apart

Most wrong exam answers come from blurring these. Learn them before the file locations.

| Term | Question it answers | Example |
|---|---|---|
| **Scope** | *Who* or *what area* is this file meant for? | `~/.claude/CLAUDE.md` is scoped to one developer across all projects. `apps/api/CLAUDE.md` is scoped to the API area. |
| **Discovery** | Does Claude Code *find* the file at all? | A CLAUDE.md two levels above your working directory is discovered. One in an unrelated sibling folder is not. |
| **Loading (timing)** | *When* does a discovered file enter context? | At launch, on demand when Claude touches a file in that subtree, or when a matching file is opened (path-scoped rules). |
| **Applicability** | Once loaded, does the content *relate to the current task*? | A loaded backend rule is irrelevant to a CSS tweak, though it still occupies context. |
| **Precedence** | If two instructions conflict, which wins? | 📘 **There is no documented "winner" rule.** See 2.6. |

> 🧩 **Teaching model:** *Scope* is the author's intent. *Discovery* and *loading* are mechanical. *Applicability* is Claude's judgment. *Precedence* is mostly **ordering in context, not overriding**. Never answer a question about "what wins" by assuming a universal priority order.

## 2.1 User-level: `~/.claude/CLAUDE.md`

- **Concept.** Personal instructions that follow *you* into every project on your machine.
- 📘 Table entry: "Personal preferences for all projects", shared with "Only you (all projects)" `[S1]`.
- **Why it matters.** It stops you from polluting a team file with "I like verbose explanations" or "explain git commands as you run them."
- **Not in Git.** It lives in your home directory, so no repository commits it. A teammate cloning the repo will never receive it.

```markdown
# ~/.claude/CLAUDE.md  (personal; applies to every project I open)

## Communication
- Keep explanations short. Show the diff first, rationale after.
- Ask before running anything that touches the network.

## Tooling habits
- I use fish shell; show commands in fish syntax when it differs from bash
- Prefer `rg` over `grep` in suggested commands
```

**Common mistake:** putting *team* standards here. They work perfectly on your machine and silently vanish for everyone else. This is the single most-cited trap in community exam material `[S5][S8]` (🎓).

📘 Related: personal **rules** can live in `~/.claude/rules/`. They load before project rules, and neither set overrides the other `[S1]`.

## 2.2 Project-level: `./CLAUDE.md` and `./.claude/CLAUDE.md`

- 📘 "A project CLAUDE.md can be stored in either `./CLAUDE.md` or `./.claude/CLAUDE.md`." Both are listed as the *Project instructions* location, "Team-shared instructions for the project", shared "via source control" `[S1]`.
- **Content that belongs here:** build and test commands, coding standards, architecture decisions, naming conventions, common workflows `[S1]`.

### Practical differences between the two locations

| | `./CLAUDE.md` (repo root) | `./.claude/CLAUDE.md` |
|---|---|---|
| Documented as project instructions? | ✅ Yes `[S1]` | ✅ Yes `[S1]` |
| Visibility | Prominent; shows in the root listing and on GitHub | Tucked in the `.claude/` folder with other Claude Code config |
| Natural neighbors | README, package.json | `.claude/rules/`, `.claude/settings.json`, skills |
| Documented difference in *behavior* | **None found** | **None found** |

🛠 **Recommendation:** pick one location per repo and stay consistent. Use the root file if you want it as visible as the README. Use `.claude/CLAUDE.md` if you want all Claude Code assets in one folder.

❓ **Uncertain:** the docs I read do not describe what happens when *both* files exist in the same repo. Do not rely on a particular merge or ordering. Avoid the situation, and if you must test it, use `/context` in a scratch repo.

⚠️ A related, documented subtlety: `.claude/rules/*.md` files **without** `paths` frontmatter "are loaded at launch with the same priority as `.claude/CLAUDE.md`" `[S1]`.

## 2.3 Local-level: `./CLAUDE.local.md` (the often-forgotten fourth file)

📘 "Personal project-specific preferences; add to `.gitignore`." Shared with "Only you (current project)" `[S1]`.

Use it for your sandbox URLs, preferred test data, or personal notes about *this* repo. It loads alongside CLAUDE.md, and within a directory it is appended **after** `CLAUDE.md`, so your personal notes are the last thing read at that level `[S1]`.

```gitignore
# .gitignore
CLAUDE.local.md
```

The user-level vs project-level distinction your task statement names is the *core* one. `CLAUDE.local.md` is the bridge case: personal **and** project-specific.

## 2.4 Directory-level: CLAUDE.md files in subdirectories

- **Concept.** A `CLAUDE.md` placed inside `apps/api/` or `apps/web/` holds guidance for just that area.
- 📘 "Claude also discovers `CLAUDE.md` and `CLAUDE.local.md` files in subdirectories under your current working directory. Instead of loading them at launch, Claude Code loads each one once Claude reads, writes, or edits another file in that subdirectory." `[S1]`

> ❓ **Documentation discrepancy to know about.** The memory page says **reads, writes, or edits** trigger the load `[S1]`. The debug page's troubleshooting table says subdirectory files load when Claude reads a file there with the **Read tool**, "not at launch and not when writing or creating files there" `[S2]`. The pages were fetched on the same day and disagree on writes. **Safe teaching rule:** a *read* of an existing file in that directory is the one trigger both pages agree on. To test a nested file, create it from your shell and then ask Claude to **read** a file in that folder `[S1]`.

**Two directions of discovery, easy to confuse:**

| Direction | Files involved | Loaded |
|---|---|---|
| **Upward** from the working directory | CLAUDE.md / CLAUDE.local.md in the cwd and every ancestor | **At launch** |
| **Downward** under the working directory | CLAUDE.md / CLAUDE.local.md in subdirectories | **On demand**, after Claude reads a file there |

## 2.5 How discovery and relevance work in practice

📘 "All discovered files are concatenated into context rather than overriding each other. Across the directory tree, content is ordered from the filesystem root down to your working directory… instructions closer to where you launched Claude are read last." `[S1]`

Take this repo:

```text
acme-shop/
├── CLAUDE.md                 (R) root: repo-wide
├── apps/
│   ├── api/
│   │   ├── CLAUDE.md         (A) backend-specific
│   │   └── src/handlers/orders.ts
│   └── web/
│       ├── CLAUDE.md         (W) frontend-specific
│       └── src/components/Button.tsx
```

| You launch `claude` from… | Loaded at launch | Loaded later, on demand |
|---|---|---|
| `acme-shop/` | R | A when Claude reads a file under `apps/api/`; W when it reads under `apps/web/` |
| `acme-shop/apps/api/` | R (ancestor) **and** A (cwd) | Nothing from `apps/web/` (not under cwd), unless you navigate or add directories |
| `acme-shop/apps/web/` | R **and** W | Nothing from `apps/api/` |

**Behavior consequences.**

1. Launch from the root and ask for a backend change. Claude reads `apps/api/...`, which triggers (A). The backend rules arrive *during* the task, not before it.
2. Launch from `apps/api/` and the backend rules are present from the first message.
3. Launch from the root and ask only about CSS. (A) may never load, which is exactly why directory-level files are good for scoping.

📘 Extra directories added with `--add-dir` do **not** load their CLAUDE.md files by default. Set `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` to include them `[S1]`.

## 2.6 Precedence: what the docs actually say

| Question | Documented answer |
|---|---|
| Do deeper files *override* shallower ones? | **No.** Files are concatenated `[S1]`. |
| Which is read last? | Content closest to the working directory; `CLAUDE.local.md` after `CLAUDE.md` in the same directory `[S1]`. |
| Load order across scopes | Broadest to most specific: managed policy → user → project → local. "A project instruction appears in context after a user instruction." `[S1]` |
| If a user rule and a project rule conflict | "Neither set overrides the other… Claude may follow either one, so keep the two consistent." `[S1]` |
| If two files contradict | "Claude may pick one arbitrarily." `[S1]` |
| Can a managed (organization) CLAUDE.md be excluded? | **No.** `claudeMdExcludes` cannot exclude managed policy files `[S1]`. |

> 🧩 **Teaching model:** "Later in context" gives a *mild* edge, never a guarantee. The reliable fix for a conflict is **removing the conflict**, not engineering around ordering.

⚠️ **Do not confuse with settings precedence.** For `settings.json`, the docs do define an order: managed first, then local over project over user `[S2]`. That is a different system. CLAUDE.md instructions are not merged key-by-key like settings.

## 2.7 Comparison table

| Configuration location | Intended audience | Scope | Shared through Git? | Typical use case | Common mistake |
|---|---|---|---|---|---|
| **Managed policy** (`/Library/Application Support/ClaudeCode/CLAUDE.md` on macOS, `/etc/claude-code/CLAUDE.md` on Linux/WSL, `C:\Program Files\ClaudeCode\CLAUDE.md` on Windows `[S1]`) | Everyone in an organization | All sessions on that machine | No (deployed by IT via MDM and similar) | Company security and compliance guidance | Expecting an individual to override or exclude it. They cannot `[S1]`. |
| **`~/.claude/CLAUDE.md`** | One developer | All of that developer's projects | **No** | Personal style, communication, shell habits | Storing team standards here |
| **`~/.claude/rules/*.md`** | One developer | All projects on that machine | No | Personal preference files split by topic | Assuming they override project rules. They don't `[S1]`. |
| **`./CLAUDE.md`** | Whole team | The project; loaded when cwd is at or below it | **Yes** | Commands, architecture, shared conventions | Letting it grow to hundreds of lines |
| **`./.claude/CLAUDE.md`** | Whole team | Same as above | **Yes** | Same, with other `.claude/` assets | Creating both this and the root file without a reason |
| **`./CLAUDE.local.md`** | One developer | This project only | **No**, if gitignored | Sandbox URLs, personal test data | Forgetting to gitignore it |
| **`subdir/CLAUDE.md`** | People working in that area | That subtree | **Yes** | API-only or frontend-only conventions | Expecting it at launch when you started elsewhere |
| **`.claude/rules/*.md` (no `paths`)** | Whole team | Whole project | **Yes** | Topic file kept always on | Thinking it is optional or lazily loaded. It loads at launch `[S1]`. |
| **`.claude/rules/*.md` (with `paths`)** | Team, narrowed to file patterns | Matching files only | **Yes** | Frontend-only or test-only rules | Glob that matches nothing, so the rule never loads |
| *(contrast)* **Auto memory** `~/.claude/projects/<project>/memory/` | Claude, for one developer | Per git repository on one machine | **No** (machine-local) `[S1]` | Learned preferences and corrections | Treating it as a team knowledge base |

## 2.8 Deciding where an instruction belongs

Work down this list and stop at the first "yes". 🛠 *(Decision procedure is a recommendation built on the documented scopes.)*

```text
Q1. Is it an organization-wide policy that nobody should override?
    → Managed policy CLAUDE.md (IT-deployed).
Q2. Does it apply only to ME, across every project?
    → ~/.claude/CLAUDE.md  (or ~/.claude/rules/…)
Q3. Does it apply only to ME, in THIS project?
    → ./CLAUDE.local.md  (gitignored)
Q4. Should every teammate get it, for the whole repo?
    → ./CLAUDE.md  or  ./.claude/CLAUDE.md
Q5. Does it matter only for one subdirectory (e.g. apps/api)?
    → apps/api/CLAUDE.md  — or a path-scoped rule.
Q6. Does it matter only for certain FILE TYPES across many directories (e.g. all *.test.ts)?
    → .claude/rules/<topic>.md with `paths:` frontmatter.
Q7. Is it a long standards document reused by several CLAUDE.md files?
    → Put it in docs/ and @import it.
Q8. Must it be GUARANTEED (never push to main; always run lint before commit)?
    → Not CLAUDE.md. Use permissions or a hook.
Q9. Is it a multi-step procedure used only sometimes?
    → A skill, not CLAUDE.md.
```

📘 The last two come straight from the docs: multi-step procedures or single-area content belong in a skill or path-scoped rule; guarantees belong in hooks `[S1]`.

### Concrete placement examples

| Instruction | Best home | Reasoning |
|---|---|---|
| "I prefer concise answers and diffs first" | `~/.claude/CLAUDE.md` | Personal, all projects |
| "Use `http://localhost:4010` as my API sandbox" | `CLAUDE.local.md` | Personal and project-specific |
| "TypeScript strict mode; no `any`; named exports" | Root `CLAUDE.md` | Team-wide convention |
| "Every endpoint validates input with zod and returns `{ error: { code, message } }`" | `apps/api/CLAUDE.md` or a path-scoped rule on `apps/api/**` | Backend-only |
| "Use React Testing Library; query by role, not test id" | Path-scoped rule on `apps/web/**/*.test.tsx` | Frontend tests only |
| "Never run `terraform apply`" | `permissions.deny` or a hook, with a note in CLAUDE.md for context | Needs a guarantee |

## 2.9 Why scope changes behavior

| Situation | What happens | Why |
|---|---|---|
| Backend rule written in **root** CLAUDE.md | It also colors frontend work | Root content loads for everything below it |
| Same rule in **`apps/api/CLAUDE.md`** | Present only after Claude touches `apps/api/` (or when launched there) | Directory-level loading is conditional |
| Team convention in **`~/.claude/CLAUDE.md`** | Works for you, missing for new hires | User-level never leaves your machine |
| Frontend test rule in **path-scoped** rule | Appears when Claude opens a matching test file | Path-scoped loading is file-triggered |

**Exam application.** When a scenario describes *inconsistent behavior between people*, think **scope** (user vs project). Between *directories*, think **directory-level or path scoping**. Between *sessions on one machine*, think **working directory, on-demand loading, and auto memory**.

---

# Module 3 — The @import Syntax and Modular Instructions

## 3.1 Concept and motivation

An **import** lets one CLAUDE.md pull in the contents of another file with an `@path` reference. Instead of copying a standards document into five CLAUDE.md files, you write it once and reference it five times.

**Why it matters.**

| Without imports | With imports |
|---|---|
| The same TypeScript rules are pasted into root, `api`, and `web` files | One `docs/standards/typescript.md`, referenced three times |
| Copies drift apart; two versions disagree | One source of truth |
| Long CLAUDE.md files that are hard to review | Short CLAUDE.md files that point to focused documents |

> ⚠️ **The trap everyone falls into.** Imports organize *authoring*. They do **not** reduce *context cost*. 📘 "Imports help you organize a long file but don't reduce its context cost, because imported files also load at launch." `[S1]` If your goal is to load instructions *less often*, you need **path-scoped rules** (Module 4), not imports.

## 3.2 Documented syntax and behavior

All of the following is 📘 from `[S1]`, "Import additional files":

| Aspect | Documented behavior |
|---|---|
| Syntax | `@path/to/import` anywhere in the CLAUDE.md text |
| When loaded | "Expanded and loaded into context at launch alongside the CLAUDE.md that references them" |
| Path types | Relative and absolute are both allowed. Home-directory paths such as `@~/.claude/my-project-instructions.md` appear in the docs |
| Relative path base | "Relative paths resolve relative to the file containing the import, **not the working directory**" |
| Recursion | Imported files can import other files, to a **maximum depth of four hops** |
| Spaces in paths | Put a **backslash before each space**: `@Design\ Docs/api-conventions.md`. Without it the path ends at the first space. |
| Quotes | "A path wrapped in quotes isn't imported at all, with or without the backslashes." |
| Code spans and fenced blocks | **Skipped.** `` `@README` `` stays literal; `@README` outside backticks imports the file |
| External imports | An import in a *project-level* file whose path resolves **outside your working directory** triggers a one-time approval dialog. If you decline, those imports stay disabled and the dialog doesn't reappear |
| User-level files | Imports from `~/.claude/CLAUDE.md` and `~/.claude/rules/` load without the dialog (you wrote them yourself), except in Cowork sessions |
| HTML comments | Block-level `<!-- … -->` comments in CLAUDE.md are stripped before injection, so they cost no context. Comments inside code blocks are preserved |

### Documented example from the docs

```markdown
See @README for project overview and @package.json for available npm commands for this project.

# Additional Instructions
- git workflow @docs/git-instructions.md
```

### Cross-tool example: sharing AGENTS.md

📘 If your repo already has an `AGENTS.md` for other coding tools and also a `CLAUDE.md`, put `@AGENTS.md` at the top of CLAUDE.md and add Claude-specific content below `[S1]`:

```markdown
@AGENTS.md

## Claude Code

Use plan mode for changes under `src/billing/`.
```

## 3.3 Syntax drills: what imports and what does not

| Text in CLAUDE.md | Imports a file? | Why |
|---|---|---|
| `- Standards: @docs/standards/typescript.md` | ✅ | Relative path from this file's directory |
| ``- Standards: `@docs/standards/typescript.md` `` | ❌ | Inside a code span |
| `"@docs/standards/typescript.md"` | ❌ | Wrapped in quotes |
| `@Design Docs/api.md` | ❌ (wrong file) | Path stops at the first space; need `@Design\ Docs/api.md` |
| `@Design\ Docs/api.md` | ✅ | Backslash-escaped space |
| A fenced ```` ``` ```` block containing `@docs/x.md` | ❌ | Fenced blocks are skipped |
| A package name such as `@anthropic-ai/claude-code` in plain prose | ❓ Unclear; the docs only guarantee that backticked text stays literal | Wrap such text in backticks `[S1]`. |

---

## 3.4 Example A: Importing a general coding standard (beginner)

### Directory structure

```text
acme-lib/
├── CLAUDE.md
├── docs/
│   └── coding-standards.md
├── package.json
└── src/
    └── index.ts
```

### File contents

**`docs/coding-standards.md`**

```markdown
# Coding Standards

## TypeScript
- `strict` mode is on; do not disable it
- No `any`. Use `unknown` and narrow it
- Prefer `type` aliases for object shapes and `interface` only when extending
- Named exports only

## Naming
- Files: `kebab-case.ts`
- Types and classes: `PascalCase`
- Functions and variables: `camelCase`

## Errors
- Throw `Error` subclasses from `src/errors.ts`; never throw strings
```

**`CLAUDE.md`**

```markdown
# Acme Lib

Small TypeScript library, built with tsup, tested with Vitest.

## Commands
- Install: `pnpm install`
- Test: `pnpm test`
- Build: `pnpm build`

## Standards
Follow the team coding standards:
@docs/coding-standards.md
```

### How the files relate

`CLAUDE.md` contains one import line. The path `docs/coding-standards.md` is relative to the folder containing `CLAUDE.md` (the repo root), which is also where you launch Claude, so both interpretations coincide here.

### Expected behavior

At launch, Claude's context contains the CLAUDE.md text **plus** the full text of `coding-standards.md` (📘 imports are expanded at launch `[S1]`). Asking "add a helper that parses a date" yields kebab-case file names, named exports, and no `any`.

### Common failure modes

| Failure | Cause | Fix |
|---|---|---|
| Standards ignored | Path typo (`docs/coding-standard.md`) | Match the real filename exactly |
| Import written inside backticks | Parser skips code spans | Remove the backticks |
| File renamed, import not updated | Dangling reference | Search for `@docs/` after renames |
| Standards contradict a line in CLAUDE.md | Two sources of truth | Keep each rule in exactly one place |

### Exercise A

Create the structure above in a scratch folder. Start `claude` there, run `/context`, and find the memory file entries. Then change the import to a wrong filename, restart, and note what changes. *(See Lab 4 for a full verification procedure.)*

---

## 3.5 Example B: Importing API conventions into a backend package (intermediate)

### Directory structure

```text
acme-shop/
├── CLAUDE.md
├── docs/
│   └── standards/
│       ├── typescript.md
│       └── api-conventions.md
└── apps/
    ├── api/
    │   ├── CLAUDE.md
    │   ├── docs/
    │   │   └── error-codes.md
    │   └── src/handlers/orders.ts
    └── web/
        └── src/App.tsx
```

### File contents

**`docs/standards/typescript.md`**

```markdown
# TypeScript Standards
- Strict mode; no `any`
- Named exports only
- Prefer `readonly` for data that should not change
```

**`docs/standards/api-conventions.md`**

```markdown
# REST API Conventions
- Resource names are plural nouns: `/orders`, `/orders/:id`
- Validate every request body and params with zod before use
- Success: `200` with `{ data: ... }`. Creation: `201`
- Errors always use `{ error: { code: string, message: string } }`
- Never return stack traces to clients
- Pagination: `?limit=` (max 100) and `?cursor=`
```

**`apps/api/docs/error-codes.md`**

```markdown
# Error Codes
| code | HTTP | meaning |
|---|---|---|
| ORDER_NOT_FOUND | 404 | No order with that id |
| VALIDATION_FAILED | 400 | Request failed zod validation |
| UNAUTHENTICATED | 401 | Missing or invalid token |
```

**Root `CLAUDE.md`**

```markdown
# Acme Shop
Monorepo: `apps/web` (React), `apps/api` (Express), `packages/shared`.

## Commands
- Install: `pnpm install`
- Test all: `pnpm -r test`

## Standards (apply everywhere)
@docs/standards/typescript.md
```

**`apps/api/CLAUDE.md`**

```markdown
# API Package

## Commands
- Run API: `pnpm --filter api dev`
- Test API: `pnpm --filter api test`

## Conventions
@../../docs/standards/api-conventions.md
@docs/error-codes.md
```

### How the files relate

```text
Root CLAUDE.md ───@──▶ docs/standards/typescript.md
apps/api/CLAUDE.md ──@──▶ ../../docs/standards/api-conventions.md   (up two levels from apps/api/)
                   └─@──▶ apps/api/docs/error-codes.md              (relative to apps/api/CLAUDE.md)
```

Key point: both import paths in `apps/api/CLAUDE.md` resolve **from that file's directory**, not from where you launched `claude` `[S1]`. That is why `@../../docs/...` is correct even if you launched from the repo root.

### Expected behavior

| Launch directory | Backend conventions present at launch? | Notes |
|---|---|---|
| `acme-shop/apps/api/` | ✅ yes | `apps/api/CLAUDE.md` is in the cwd, so it loads at launch, with its imports |
| `acme-shop/` | ❌ not at launch | Loads after Claude reads a file under `apps/api/` (📘 on-demand rule `[S1]`). That its imports expand at the same moment is a reasonable reading, but ❓ the docs state import expansion only for launch-time loading. Verify with `/context` or the `Loaded` line |
| `acme-shop/apps/web/` | ❌ no | API conventions never load, which is the point |

### Common failure modes

| Failure | Cause | Fix |
|---|---|---|
| `@docs/standards/api-conventions.md` written in `apps/api/CLAUDE.md` | Resolves to `apps/api/docs/standards/...`, which doesn't exist | Use `@../../docs/standards/api-conventions.md` |
| Conventions "ignored" when launched from root | Nested file loads on demand and Claude hasn't read an API file yet | Launch from `apps/api/` or begin by reading a file there |
| Import to a shared folder outside the working directory | External-import approval dialog was declined | Re-approve, or move the file inside the project |
| Spaces in a folder name | Unescaped space truncates the path | `@Design\ Docs/...` |

### Exercise B

Add `@docs/standards/api-conventions.md` (the wrong, root-style path) to `apps/api/CLAUDE.md`. Predict where Claude would look for it. Fix it using a path relative to the importing file.

---

## 3.6 Example C: Monorepo with shared standards and package-specific imports (advanced)

### Directory structure

```text
acme-shop/
├── CLAUDE.md
├── docs/
│   └── standards/
│       ├── typescript.md
│       ├── testing.md
│       └── api-conventions.md
├── apps/
│   ├── api/
│   │   ├── CLAUDE.md
│   │   └── src/
│   └── web/
│       ├── CLAUDE.md
│       └── src/
└── packages/
    └── shared/
        ├── CLAUDE.md
        └── src/
```

### File contents

**Root `CLAUDE.md`** (small on purpose)

```markdown
# Acme Shop
pnpm workspace. React web app, Express API, shared TypeScript package.

## Commands
- Install: `pnpm install`
- Build/test everything: `pnpm -r build` / `pnpm -r test`

## Shared standards
@docs/standards/typescript.md
```

**`apps/api/CLAUDE.md`**

```markdown
# API
- Run: `pnpm --filter api dev`
@../../docs/standards/api-conventions.md
@../../docs/standards/testing.md
```

**`apps/web/CLAUDE.md`**

```markdown
# Web
- Run: `pnpm --filter web dev`
- Components live in `src/components/`; one component per file
@../../docs/standards/testing.md
```

**`packages/shared/CLAUDE.md`**

```markdown
# Shared package
- Zero runtime dependencies on React or Express
- Every export needs a unit test
@../../docs/standards/testing.md
```

### How the files relate

```text
                     docs/standards/typescript.md
                              ▲
                              │ @  (root, loaded for every session in this repo)
                         CLAUDE.md (root)
                              │
        ┌─────────────────────┼──────────────────────┐
  apps/api/CLAUDE.md    apps/web/CLAUDE.md    packages/shared/CLAUDE.md
     │        │                │                         │
     │        └────────────────┴──────────┬──────────────┘
     │                                    ▼
     ▼                          docs/standards/testing.md   (one file, three importers)
docs/standards/api-conventions.md   (one importer)
```

`testing.md` is written once and reused by three packages. `api-conventions.md` is imported only by the backend, so frontend work does not carry it.

### Expected behavior

| Task | Launched from | Context contains |
|---|---|---|
| Edit a React component | `acme-shop/` | Root + TypeScript standards at launch; `apps/web/CLAUDE.md` + testing standards after Claude reads a `apps/web/` file |
| Edit an API handler | `acme-shop/apps/api/` | Root + TypeScript at launch; `apps/api/CLAUDE.md` + API conventions + testing standards at launch |
| Edit a shared util | `acme-shop/` | Root at launch; `packages/shared/CLAUDE.md` once a file there is read |

### Common failure modes

| Failure | Cause | Fix |
|---|---|---|
| Frontend suggests REST-style error envelopes | `api-conventions.md` imported from the **root** file | Move that import into `apps/api/CLAUDE.md` |
| Contradictory testing advice | Two copies of testing rules (one inline, one imported) | Keep only the imported file |
| Chain of imports too deep | More than four hops | Flatten; 📘 max depth is four `[S1]` |
| CLAUDE.md files still "too heavy" | Assuming imports cut context | Use path-scoped rules for conditional loading (Module 4) |
| Shared file lives outside the repo | External import approval needed | Keep shared files inside the repo |

### Exercise C

Add `packages/shared` to the repo and give it a CLAUDE.md that imports `testing.md`. Then explain, in two sentences, why `api-conventions.md` should **not** be imported from the root.

---

## 3.7 When an import appears not to work: verification checklist

Work in this order (🛠 procedure; each check is based on documented behavior):

1. **Is the parent file loaded at all?** Run `/context` and look under **Memory files** `[S1][S2]`. Nested files will not be listed at launch, so look for the terminal `Loaded` line after Claude reads a file in that folder `[S1]`.
2. **Is the `@` outside backticks and quotes?** Code spans, fenced blocks, and quoted paths are not imported `[S1]`.
3. **Is the path relative to the importing file?** Re-derive it by hand from that file's directory `[S1]`.
4. **Do spaces in the path have backslashes?** `[S1]`
5. **Does the target exist, with the exact filename and case?** Run `ls -l <resolved path>`.
6. **Is the chain deeper than four hops?** `[S1]`
7. **Does the path resolve outside the working directory?** An approval dialog may have been declined `[S1]`.
8. **Does an `Instruction file not loaded` notice appear?** The docs point to an errors page for this notice `[S1]`; I did not read that page, so ❓ consult it directly.
9. **Run `/doctor prompt-audit`** to have Claude look for references to files that don't exist (📘 requires v2.1.283 or later) `[S1]`.

## 3.8 Documented behavior vs recommendations

| Statement | Category |
|---|---|
| `@path` syntax; relative to the importing file; four-hop limit; backslash for spaces; code spans skipped; launch-time expansion; external approval dialog | 📘 Documented `[S1]` |
| "Put each standard in exactly one file and import it" | 🛠 Recommended |
| "Keep root CLAUDE.md small and import topic files" | 🛠 Recommended |
| "Import `api-conventions.md` only from the backend package" | 🛠 Recommended |
| "Imports in a nested file expand when that file loads on demand" | ❓ Reasonable inference; not stated explicitly |

---

# Module 4 — Organizing Instructions with .claude/rules/

## 4.1 Purpose

**Concept.** `.claude/rules/` is a folder of small markdown files, each covering one topic. Claude Code discovers them automatically. Some load at launch; others load only when Claude works with matching files.

**Why it matters.** A single 600-line CLAUDE.md has three problems: reviewers can't see who changed what, unrelated rules dilute attention, and every session pays the context cost. 📘 "Rules can also be scoped to specific file paths, so they only load into context when Claude works with matching files, reducing noise and saving context space." `[S1]`

## 4.2 Documented mechanics

All 📘 from `[S1]` unless marked:

| Aspect | Behavior |
|---|---|
| Location | `.claude/rules/` in the project; personal rules in `~/.claude/rules/` |
| Discovery | **All `.md` files are discovered recursively**, so subfolders like `frontend/` and `backend/` work |
| File granularity | "Each file should cover one topic, with a descriptive filename like `testing.md` or `api-design.md`" |
| Without `paths` frontmatter | Loaded **unconditionally at launch**, "with the same priority as `.claude/CLAUDE.md`" |
| With `paths` frontmatter | Loaded when Claude uses the **Read, Write, or Edit** tool on a matching file, and also when it views one matching file with a Bash command that counts as a read (`cat`, `head`) |
| Frontmatter fields | `paths` is **the only field Claude Code reads**. Other fields are ignored without error. The frontmatter is stripped before the rule enters context |
| `paths` format | A YAML list **or** a comma-separated string |
| Invalid YAML | Frontmatter is ignored and the rule loads **as if it had no `paths`**. Run `claude --debug` to see the parse error |
| Brace expansion | Supported (`src/**/*.{ts,tsx}`), with a shared budget of 1,000 expanded patterns and 4 MiB per rule |
| Invalid bracket patterns | A `[` that can't parse as a bracket expression makes that pattern match nothing; other patterns still work. Escape a literal `[` as `\[` |
| Symlinks | Supported. A symlink whose target is **outside** the working directory is treated like an external import: approval needed, and then only rules **without** `paths` load |
| Compaction | Rules with `paths` frontmatter load again on demand after `/compact` |

> 📘 Note from the docs: "Rules load into context every session or when matching files are opened. For task-specific instructions that don't need to be in context all the time, use **skills** instead." `[S1]`

### Path-pattern table (from the docs)

| Pattern | Matches |
|---|---|
| `**/*.ts` | All TypeScript files in any directory |
| `src/**/*` | All files under `src/` |
| `*.md` | Markdown files in the project root |
| `src/components/*.tsx` | React components in one directory |

❓ **Match root:** the docs' examples are all written relative to the project root (e.g. `src/api/**/*.ts`), so treat patterns as root-relative. The docs do not spell out the anchor explicitly. Test with `claude --debug` or an `InstructionsLoaded` hook if it matters.

## 4.3 Rules vs the other mechanisms

| | `.claude/rules/` (no paths) | `.claude/rules/` (paths) | Subdirectory CLAUDE.md | `@import` |
|---|---|---|---|---|
| Loads | At launch | When a matching file is read/edited | After Claude reads a file in that subdirectory | At launch, with its parent file |
| Trigger | None | **File pattern** | **Directory location** | Parent file loading |
| Reduces idle context? | No | **Yes** | **Yes** (for untouched areas) | **No** |
| Best for | Always-on topics split into files | Cross-cutting file types (tests, migrations) | Self-contained packages | Reusing one document across several CLAUDE.md files |

## 4.4 Realistic repository: topic-based rules

### Directory structure

```text
acme-shop/
├── CLAUDE.md
└── .claude/
    └── rules/
        ├── testing.md
        ├── api-conventions.md
        └── deployment.md
```

**`CLAUDE.md`**

```markdown
# Acme Shop

pnpm monorepo: `apps/web` (React + Vite), `apps/api` (Express), `packages/shared`, `infra/` (Terraform).

## Commands
- Install: `pnpm install`
- Build all: `pnpm -r build`
- Typecheck and lint: `pnpm typecheck && pnpm lint`

## Global conventions
- TypeScript strict; no `any`; named exports only
- Conventional Commits: `feat:`, `fix:`, `chore:`
- Never commit directly to `main`

## Where detailed guidance lives
Topic rules are in `.claude/rules/` (testing, API conventions, deployment).
```

**`.claude/rules/testing.md`**

```markdown
---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/tests/**/*"
---

# Testing Rules

- Runner: Vitest. Run one file with `pnpm vitest run <path>`
- Name tests `<unit>.test.ts` next to the source file
- Arrange / Act / Assert, with a blank line between sections
- Do not mock the module under test; mock only network and clock
- Frontend tests use React Testing Library; query by role or label, never by test id
- A bug fix must come with a test that fails before the fix
```

**`.claude/rules/api-conventions.md`**

```markdown
---
paths:
  - "apps/api/src/**/*.ts"
---

# API Conventions

- Resource paths are plural nouns: `/orders`, `/orders/:id`
- Validate body, params, and query with zod before use
- Success: `{ data: ... }`. Errors: `{ error: { code, message } }`
- Never return stack traces or internal ids in error messages
- Handlers stay thin: parse input, call a service in `src/services/`, return the result
- New endpoints need an entry in `apps/api/openapi.yaml`
```

**`.claude/rules/deployment.md`**

```markdown
---
paths:
  - "infra/**/*"
  - ".github/workflows/**/*"
  - "**/Dockerfile"
---

# Deployment Rules

- Infrastructure is Terraform in `infra/terraform/`
- Run `terraform fmt` and `terraform validate`; run `terraform plan` and show the output
- Never run `terraform apply`; a human applies from the pipeline
- Pin GitHub Action versions to a commit SHA
- Do not add secrets to workflow files; reference the existing secret names only
```

### How the files relate

- The root `CLAUDE.md` is always loaded and holds only repo-wide facts.
- Each rule file has **one job** and a **narrow `paths`**, so it enters context only when Claude touches matching files.
- Because all three have `paths`, an empty-feeling launch (`/context` shows only CLAUDE.md under **Memory files**) is **expected**, not broken.

### Expected behavior

| Claude is working on… | Rules that load |
|---|---|
| `apps/api/src/handlers/orders.ts` | `api-conventions.md` |
| `apps/api/src/handlers/orders.test.ts` | `api-conventions.md` **and** `testing.md` (both patterns match) |
| `infra/terraform/main.tf` | `deployment.md` |
| `README.md` | None of the three |

### Common mistakes

| Mistake | Effect |
|---|---|
| Putting `paths` in a rule that should always apply | It silently stops loading until a matching file is touched |
| Forgetting `paths` on a niche rule | It loads every session and adds noise |
| One giant `rules/everything.md` | Defeats the point; hard to scope |
| Glob that matches nothing (`apps/api/**/*.js` in a TS project) | Rule never loads |

## 4.5 Path-scoped example: frontend and backend

Use subfolders for discoverability. The docs explicitly support recursive discovery `[S1]`.

```text
.claude/rules/
├── frontend/
│   ├── react-components.md
│   └── styling.md
└── backend/
    ├── handlers.md
    └── database.md
```

**`.claude/rules/frontend/react-components.md`**

```markdown
---
paths:
  - "apps/web/src/**/*.{ts,tsx}"
---

# React Component Rules

- Function components only; no class components
- One component per file; filename matches the component (`OrderCard.tsx`)
- Props typed with a named `type`, not inline
- Keep data fetching in hooks under `src/hooks/`, never in presentational components
- No `useEffect` for derived state; compute during render
```

**`.claude/rules/frontend/styling.md`**

```markdown
---
paths: "apps/web/src/**/*.{css,tsx}"
---

# Styling Rules

- Use CSS modules; class names in camelCase
- No inline `style` except for dynamic values
- Use design tokens from `apps/web/src/tokens.css`
```

*(This file uses the **comma-separated string** form to show it is allowed; 📘 `paths` accepts a YAML list or a comma-separated string `[S1]`.)*

**`.claude/rules/backend/handlers.md`**

```markdown
---
paths:
  - "apps/api/src/handlers/**/*.ts"
---

# Handler Rules

- Signature: `(req, res) => Promise<void>`; wrap with `asyncHandler`
- Call services; do not touch the database from a handler
- Return errors with `sendError(res, code, status)` from `src/http/errors.ts`
```

**`.claude/rules/backend/database.md`**

```markdown
---
paths:
  - "apps/api/src/db/**/*"
  - "apps/api/migrations/**/*.sql"
---

# Database Rules

- Migrations are append-only; never edit an applied migration
- Use parameterized queries; no string-built SQL
- Every migration has a matching rollback file
```

**Behavior check.** Editing `apps/web/src/components/OrderCard.tsx` loads `react-components.md` and `styling.md` and **none** of the backend rules. That is the "backend instruction unexpectedly influencing frontend work" problem *solved by design*.

## 4.6 How to tell which rules are relevant to a task

1. Ask: *which files will Claude touch?* Match them against each rule's `paths`.
2. Unconditional rules (no `paths`) always apply: check `/context` at launch `[S1][S2]`.
3. Path-scoped rules appear only after a matching read/edit. 📘 The docs suggest an **`InstructionsLoaded` hook** to log "which `CLAUDE.md` and rules files are loaded, when they load, and why", which is useful for path-specific and lazy-loaded files `[S1]`.
4. 📘 `claude --debug` surfaces frontmatter parse errors `[S1]`.

## 4.7 Keeping rules focused, discoverable, maintainable (🛠 recommendations)

- One topic per file; filename describes the topic.
- Use `paths` whenever a rule is meaningless outside certain files.
- Keep each file short (the docs' 200-line target applies per file; each rule file and import counts as a separate file in the size warning `[S1]`).
- Write concrete, verifiable statements.
- Review rules like code: they live in Git, so use pull requests and CODEOWNERS.
- Delete rules that conflict with CLAUDE.md. 📘 Contradictions let Claude "pick one arbitrarily" `[S1]`.

## 4.8 Trade-off matrix: four ways to organize

| Approach | Strengths | Weaknesses | Choose when |
|---|---|---|---|
| **One large CLAUDE.md** | Simple; easy to grep; one place to look | Context cost every session; adherence drops with length (📘 under 200 lines recommended); merge conflicts; unrelated guidance mixed | Small repo; early project |
| **Multiple directory-level CLAUDE.md** | Natural ownership per package; not loaded for untouched areas; can be maintained by that package's team | Loading is on demand, so not present until Claude reads there; scattered; easy to forget | Self-contained packages with different teams or stacks |
| **Topic `.claude/rules/` files** | Small, reviewable, one topic each; `paths` gives file-pattern scoping that crosses directories | Needs discipline on naming and `paths`; unscoped rules still load at launch | Cross-cutting topics (testing, security, deployment); file-type rules |
| **`@import` shared files** | One source of truth reused in many places; keeps CLAUDE.md files short | **Does not reduce context** (loads at launch); path mistakes fail silently; four-hop limit | Same standard needed by several packages |

> 🧩 **Rule of thumb:** *Reuse → import. Location-based narrowing → directory CLAUDE.md. File-pattern narrowing → path-scoped rule. Topic organization → rules folder. Guarantee → hook.*

---

# Module 5 — Diagnosing Configuration Problems

## 5.0 Commands used in this module (all verified against `[S1][S2]`)

| Command | What it does | Notes |
|---|---|---|
| `/context` | Shows everything occupying the context window by category, **including Memory files** | Run first. Nested CLAUDE.md files won't appear at launch (they load on demand) |
| `/memory` | Lists CLAUDE.md, CLAUDE.local.md and other memory file locations across user and project scopes (including entries for files that don't exist yet), opens them in your editor, toggles auto memory, opens the auto memory folder | Locations and editing. For *what loaded*, use `/context` |
| `/status` | Shows active **settings** sources | Settings, not CLAUDE.md |
| `/doctor` | Setup checkup: invalid settings files, unused extensions, derivable content in a checked-in CLAUDE.md, with proposed fixes | Asks before applying |
| `/doctor prompt-audit [path]` | Audits instruction files for outdated or conflicting content and references to non-existent files; read-only until you ask | 📘 Requires v2.1.283 or later |
| `claude doctor` (terminal) | Read-only installation and settings diagnostics without starting a session | |
| `claude --debug` | Debug logging; shows frontmatter parse errors for rules | |
| `claude --safe-mode` | Launches with all customizations disabled (CLAUDE.md, skills, plugins, hooks, MCP, custom commands/agents) | If the problem vanishes, a customization is the cause |
| `cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-clean claude` | Clean session with no user/project config | Managed settings still apply |
| `InstructionsLoaded` hook | Logs which CLAUDE.md and rules files load, when and why | A hook, so configured in settings, not CLAUDE.md |
| `/config` | Settings panel (includes **Project instructions** for AGENTS.md behavior) | |
| `/init` | Generates a starter CLAUDE.md; suggests improvements if one exists | |

Standard shell helpers (`ls`, `git status`, `git check-ignore -v`, `git ls-files`) are ordinary tools, not Claude Code features.

> ❓ **Documentation drift to remember.** The debug page's table describes `/memory` as showing "which `CLAUDE.md` and rules files loaded" in one place and as listing "memory file locations" in another, while the memory page says to use `/context` "to check which CLAUDE.md and rules files loaded at launch" `[S1][S2]`. **Use both commands**: `/context` for what is *in the window*, `/memory` for *where the files are and to edit them*. If an exam question hinges on this, choose the answer that uses `/memory` to *inspect and open* the files rather than to *instruct* Claude.

## 5.1 Scenario format

Each scenario follows: **Symptoms → Likely cause → How to investigate → Corrective action → How to verify → Certification lesson.**

---

### Scenario 1 — A new teammate doesn't receive instructions that exist in another developer's home directory

**Symptoms.** Alice's Claude always uses `pnpm vitest run` and the `{ error: { code, message } }` format. Bob joined yesterday; his Claude uses `npm test` and returns `{ message }`.

**Likely cause.** The guidance lives in Alice's `~/.claude/CLAUDE.md`. 📘 User-level files are "Only you (all projects)" `[S1]`; Git never carries them.

**How to investigate.**
```bash
# On Alice's machine: where do the instructions actually live?
grep -n "vitest\|error:" ~/.claude/CLAUDE.md CLAUDE.md .claude/CLAUDE.md 2>/dev/null
# In the repo: is anything shared at all?
git ls-files | grep -i "claude"
```
On Bob's machine, run `/context` and compare **Memory files** with Alice's.

**Corrective action.** Move team-relevant lines from `~/.claude/CLAUDE.md` into the project `CLAUDE.md` (or `.claude/CLAUDE.md`, or a rule file), commit, and let Bob pull. Leave personal habits behind.

**How to verify.** Bob pulls, restarts `claude` in the repo, runs `/context` (project CLAUDE.md appears), then asks for a new endpoint and checks the command and error format.

**Certification lesson.** "Teammate doesn't get my instructions" = **scope bug**: user-level vs project-level. 🎓 This is the most commonly reported Task 3.1 pattern `[S5][S8]`. Wrong answer patterns: "update Claude Code", "put the file in `.claude/` or the root is ignored", "import user-level files from the project file".

---

### Scenario 2 — Team-wide instructions were mistakenly placed in `~/.claude/CLAUDE.md`

**Symptoms.** Standards are applied consistently for the author but not for CI runs or other contributors. The author *also* sees the standards applied in unrelated personal projects, where they shouldn't be.

**Likely cause.** Same root cause as Scenario 1, with a second symptom: user-level scope is "all projects", so team rules leak into unrelated repos.

**How to investigate.** `cat ~/.claude/CLAUDE.md` and sort each line: *personal*, *project-specific*, or *team-wide*.

**Corrective action.**
1. Team-wide lines → project `CLAUDE.md`.
2. Area-specific lines → directory CLAUDE.md or path-scoped rule.
3. Personal-in-this-project lines → `CLAUDE.local.md` (gitignored).
4. Remaining personal lines stay in `~/.claude/CLAUDE.md`.

**How to verify.** Open a different, unrelated repo and confirm the team rules no longer appear in `/context`; open the team repo and confirm they still do, from the project file.

**Certification lesson.** Placement follows **audience and breadth**. Use the Section 2.8 decision list.

---

### Scenario 3 — A backend instruction unexpectedly influences frontend work

**Symptoms.** While building a React component, Claude suggests zod request validation and `{ error: { code } }` envelopes.

**Likely cause (check in this order).**
1. The backend rule lives in the **root** `CLAUDE.md`, which loads for everything below it.
2. The rule file in `.claude/rules/` has **no `paths`**, so it loads at launch for all work `[S1]`.
3. A **user-level** file has the same guidance.
4. The glob is too broad (`**/*.ts` matches frontend TypeScript as well).

**How to investigate.** `/context`, then look under **Memory files** for the offending file. Use `grep -rn "zod\|error: {" CLAUDE.md .claude ~/.claude 2>/dev/null` to find the text.

**Corrective action.** Move the rule to `apps/api/CLAUDE.md` or add `paths: ["apps/api/**/*.ts"]`. Tighten overly broad globs.

**How to verify.** Restart, open `apps/web/...`, run `/context`; the backend text should be absent. Repeat in `apps/api/...` and confirm it appears after a read or edit there.

**Certification lesson.** Unwanted influence is almost always **over-broad scope** (too high in the hierarchy or an unscoped rule), not a bug.

---

### Scenario 4 — A nested CLAUDE.md is not taking effect as expected

**Symptoms.** `apps/api/CLAUDE.md` contains API rules. Launched from the repo root, Claude's first reply on an API question ignores them.

**Likely cause.** 📘 Subdirectory files load **on demand**, after Claude reads (per the memory page: reads, writes, or edits) a file in that subtree `[S1]`; the debug page narrows this to the Read tool `[S2]`. Also check:
- You launched in a *different* branch of the tree (a sibling is not an ancestor).
- Claude used a built-in **Explore** or **Plan** subagent. 📘 Those skip CLAUDE.md `[S2]`.
- `claudeMdExcludes` skips the file `[S1]`.
- The file was *created by Claude* in the same session and never read afterward `[S1]`.

**How to investigate.**
1. `/context`: the nested file is **not expected** in the launch list.
2. Ask Claude to **read** `apps/api/src/handlers/orders.ts`.
3. Watch for the terminal **`Loaded`** line showing the CLAUDE.md path `[S1]`.
4. Check for exclusions: look for `claudeMdExcludes` in `.claude/settings.local.json`, `.claude/settings.json`, `~/.claude/settings.json`.

**Corrective action.** Launch from `apps/api/` for sessions that always need the rules, or move truly repo-wide content up to the root file. For file-type behavior independent of location, use a path-scoped rule.

**How to verify.** The `Loaded` line appears; a follow-up answer reflects the nested rules.

**Certification lesson.** **Discovery ≠ loading.** Upward = at launch. Downward = on demand.

---

### Scenario 5 — An imported standards file is missing or has an incorrect path

**Symptoms.** CLAUDE.md says `@docs/standards/api-conventions.md`, but Claude never applies those conventions.

**Likely cause.** Path relative to the *wrong base* (📘 relative to the importing file, not the cwd), typo, case mismatch, import inside backticks or quotes, unescaped space, more than four hops deep, or an external import whose approval dialog was declined `[S1]`.

**How to investigate.**
```bash
# From the directory that CONTAINS the importing CLAUDE.md:
cd apps/api
ls -l ../../docs/standards/api-conventions.md   # does the resolved path exist?
grep -n "@" CLAUDE.md                             # list candidate imports
```
Then `/context` to confirm the parent file loaded; then `/doctor prompt-audit` for references to files that don't exist `[S1]`.

**Corrective action.** Fix the path (`@../../docs/standards/api-conventions.md`), remove backticks or quotes, escape spaces, flatten deep chains, or re-approve external imports.

**How to verify.** Restart; ask "what error format do endpoints use?" and compare with the imported file; confirm in `/context`.

**Certification lesson.** Import failures are **path-resolution** failures far more often than product bugs.

---

### Scenario 6 — A rule file exists in `.claude/rules/` but seems irrelevant to the current task

**Symptoms.** `.claude/rules/testing.md` has the right content. Claude writes a test with no regard for it.

**Likely cause.**
- It has `paths:` that **doesn't match** the file Claude is working on (`**/*.spec.ts` vs actual `*.test.ts`).
- It hasn't loaded yet because Claude hasn't read/edited a matching file `[S1]`.
- The YAML is invalid, so frontmatter is ignored and the rule loads *unscoped* (surprise: loaded when you didn't expect) `[S1]`.
- A non-`.md` extension. 📘 Only `.md` files are discovered `[S1]`.
- It sits outside `.claude/rules/`.

**How to investigate.**
```bash
ls -R .claude/rules
head -n 8 .claude/rules/testing.md      # inspect frontmatter
claude --debug                          # look for a frontmatter parse error
```
Compare each `paths` glob against the real file path, from the project root.

**Corrective action.** Fix globs (use brace expansion: `**/*.{test,spec}.{ts,tsx}`), fix YAML (quote globs that start with `*` or contain `{`), rename to `.md`.

**How to verify.** Have Claude open a matching test file; confirm via the `InstructionsLoaded` hook log or by asking Claude to state the rule. Then check unrelated files do **not** trigger it.

**Certification lesson.** Path-scoped rules load on **file access**, not at launch. An empty launch list is normal.

---

### Scenario 7 — Claude behaves differently across sessions

**Symptoms.** Monday: Claude uses pnpm. Tuesday: npm. Same repo, same developer.

**Likely cause (ranked).**
1. **Different working directory.** Different ancestors/descendants load at launch.
2. **Nested files not yet loaded** in one session.
3. **Auto memory differences.** 📘 It is machine-local and per repository; a correction made once may be saved, or not `[S1]`.
4. **`CLAUDE.local.md`** present on one worktree only. 📘 A gitignored `CLAUDE.local.md` exists only in the worktree where you created it `[S1]`.
5. **Unreproducible instructions**: given only in chat, lost after `/compact` `[S1]`.
6. **`--add-dir` directories** whose CLAUDE.md loaded in one session but not another `[S1]`.
7. **Vague or conflicting instructions** let Claude "pick one arbitrarily" `[S1]`.

**How to investigate.** In each session: `pwd`, `/context` (Memory files), `/memory` (open the auto-memory folder and read `MEMORY.md`), and `git status` to see which worktree you're in.

**Corrective action.** Make the convention an explicit CLAUDE.md line ("Package manager: pnpm; never use npm"), launch from a consistent directory, and prune conflicting auto-memory entries.

**How to verify.** Start three fresh sessions from the same directory; all three should show the same Memory files list and the same behavior.

**Certification lesson.** Cross-session inconsistency is a **loading-context** problem before it is a model problem.

---

### Scenario 8 — Two instructions appear to contradict one another

**Symptoms.** Root says "use default exports"; `apps/web/CLAUDE.md` says "named exports only". Claude flips between them.

**Likely cause.** 📘 Files are concatenated, not overridden. "If two instructions contradict each other, Claude may pick one arbitrarily." `[S1]` A user-level vs project rule conflict is similarly unresolved `[S1]`.

**How to investigate.**
```bash
grep -rn "default export\|named export" CLAUDE.md .claude apps packages ~/.claude 2>/dev/null
```
Or run `/doctor prompt-audit`, which looks for files that contradict each other `[S1]`.

**Corrective action.** **Delete the conflict.** Keep the rule in the narrowest correct location, state exceptions explicitly ("Use named exports. Exception: Next.js pages require default exports"), and remove the duplicate.

**How to verify.** Re-run the audit; ask Claude for a new module in each area and confirm consistent output.

**Certification lesson.** Don't "solve" a conflict by relying on ordering. Remove it.

---

### Scenario 9 — CLAUDE.md is huge and Claude ignores half of it

**Symptoms.** 700-line root file; adherence is spotty; a startup warning about file length.

**Likely cause.** 📘 Files over 200 lines "consume more context and may reduce adherence". Imports don't help since they load at launch `[S1]`.

**How to investigate.** `wc -l CLAUDE.md .claude/rules/*.md`; check `/status` for the size warning `[S1]`; run `/doctor` for trimming proposals `[S1]`.

**Corrective action.** Move file-type or area-specific rules to **path-scoped rules**; move multi-step procedures to **skills**; delete derivable content (directory listings, dependency lists).

**How to verify.** Re-run `wc -l`; confirm the warning is gone; spot-check adherence.

**Certification lesson.** Reduce *loaded* content; don't merely reshuffle it.

---

### Scenario 10 — "Claude ignored a must-never rule"

**Symptoms.** CLAUDE.md says "Never run `terraform apply`." One day Claude runs it.

**Likely cause.** 📘 CLAUDE.md is context, not enforcement `[S1][S2]`.

**How to investigate.** `/context` confirms it was loaded. If it was, the issue is the guarantee level, not loading.

**Corrective action.** Add a `permissions.deny` rule or a **PreToolUse hook** for the command. Keep the CLAUDE.md line for context and intent.

**How to verify.** `/permissions` shows the deny rule in effect `[S2]`; try the command in a scratch repo.

**Certification lesson.** **Guidance vs guarantee.** If a question says "must never" or "every time", look for hooks or permissions.

---

### Bonus Scenario 11 — AGENTS.md exists but Claude doesn't seem to know it

**Symptoms.** Repo has `AGENTS.md` for another tool. Claude ignores it.

**Likely cause.** 📘 By default Claude reads `AGENTS.md` **only** when there is no `CLAUDE.md` or `CLAUDE.local.md` in the working directory or above. Your `~/.claude/CLAUDE.md` doesn't count in that check `[S1]`.

**Fix.** Add `@AGENTS.md` to a `CLAUDE.md` next to it, or set **Project instructions** to `claude-md-and-agents-md` via `/config` `[S1]`.

**Lesson.** Know the default; read-both is an explicit setting.

---

## 5.2 General investigation ladder

```text
1. Did the right file LOAD?          → /context (Memory files), "Loaded" line for nested files
2. Is it in a DISCOVERED location?   → compare path with "How CLAUDE.md files load"
3. Is the SCOPE right?               → user vs project vs directory vs path-scoped
4. Does an IMPORT resolve?           → path relative to the importing file
5. Is there a CONFLICT?              → grep; /doctor prompt-audit
6. Is it WRITTEN well?               → specific, short, verifiable
7. Does it need a GUARANTEE?         → permissions or hooks, not CLAUDE.md
8. Still unexplained?                → claude --safe-mode, then clean CLAUDE_CONFIG_DIR session
```

---

# Module 6 — Using /memory to Investigate Loaded Instructions

## 6.1 What "memory" means in Claude Code

📘 Two systems, both loaded at the start of every conversation, both treated as context `[S1]`:

| | CLAUDE.md files | Auto memory |
|---|---|---|
| Written by | **You** | **Claude** |
| Contains | Instructions and rules | Learnings and patterns (four types: `user`, `feedback`, `project`, `reference`) |
| Scope | Project, user, or organization | Per repository, shared across worktrees on **one machine** |
| Loaded | Per the rules in Module 2 | First **200 lines or 25 KB** of `MEMORY.md` at every session start |
| Location | See Module 2 | `~/.claude/projects/<project>/memory/` |
| Shared via Git? | Project files: yes | **No** (machine-local) |

Auto memory details worth knowing 📘 `[S1]`:
- `MEMORY.md` is an index; topic files (e.g. `feedback_testing.md`) are **not** loaded at startup. Claude reads them on demand.
- Toggle in `/memory`, or set `autoMemoryEnabled: false` in settings, or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- If you say "remember that…", Claude usually saves it to **auto memory**. To put it in CLAUDE.md, say so: "add this to CLAUDE.md".

## 6.2 How memory files relate to CLAUDE.md

Three kinds of "remembered" content, and the exam wants you to tell them apart:

| Kind | Who maintains it | How it gets there | Example | Shared? |
|---|---|---|---|---|
| **Automatic memory** | Claude | Saved during sessions after corrections | "User prefers pnpm" in `MEMORY.md` | No |
| **Manually maintained project instructions** | The team | You edit and commit CLAUDE.md, `.claude/CLAUDE.md`, rule files | "Package manager: pnpm" in CLAUDE.md | Yes (Git) |
| **Imported instruction files** | The team | An `@path` line in a CLAUDE.md pulls them in | `@docs/standards/typescript.md` | Yes (Git) |

🛠 If a convention matters to the *team*, it belongs in a manually maintained or imported file. Auto memory is a personal convenience, not a team contract.

## 6.3 The /memory command: purpose and current behavior

📘 From `[S1]`:

> The `/memory` command lists your CLAUDE.md, CLAUDE.local.md, and other memory file locations across user and project scopes, including user and project CLAUDE.md entries for files that don't exist yet. It also lets you toggle auto memory on or off and provides an option to open the auto memory folder. Select any file to open it in your editor; selecting one that doesn't exist yet creates it first. To check which CLAUDE.md and rules files loaded at launch, run `/context`.

What it **is**: an inspection and editing entry point.
What it **is not**: a way to instruct Claude to prioritize sections, reload files, or reset memory. (A community practice-exam distractor proposes exactly that; treat such options as wrong `[S6]` 🎓.)

| Task | Use |
|---|---|
| See where memory files live, open one to edit | `/memory` |
| Toggle auto memory | `/memory` |
| Browse what Claude saved | `/memory` → open the auto-memory folder |
| Confirm a file is actually in the context window | `/context` → **Memory files** |
| Verify nested file loading | Terminal **`Loaded`** line after a read in that directory |
| Settings sources | `/status` |

## 6.4 Distinguishing memory problems from discovery and scoping problems

| Symptom | Category | First check |
|---|---|---|
| File isn't in `/context` Memory files | **Discovery or loading** | Is it in an upward-discovered location? Is it nested (on-demand)? Excluded? |
| File is in `/context`, instruction not followed | **Wording or conflict** | Specific? Short? Contradicted elsewhere? |
| Behavior differs by launch directory | **Scoping and loading timing** | Compare ancestors, nested files, and cwd |
| Behavior differs between two developers | **Scope (user vs project)** | `~/.claude/CLAUDE.md`, auto memory, `CLAUDE.local.md` |
| A "remembered" preference you never wrote appears | **Auto memory** | `/memory` → auto-memory folder |
| Behavior differs across sessions on one machine | **Mix** | Cwd, auto memory, compaction, worktrees |
| Instruction disappeared after `/compact` | **Persistence** | 📘 Project-root CLAUDE.md survives; conversation-only instructions don't; nested files reload on demand `[S1]` |

## 6.5 Why behavior may differ across projects, directories, and sessions

| Dimension | Why it changes |
|---|---|
| **Project** | Different repo means different project files; auto memory is per repository `[S1]` |
| **Directory** | Different cwd means different ancestors loaded at launch and different on-demand subtrees |
| **Session** | Fresh context each time; auto memory may have changed; nested files load only after being read |
| **Machine** | User-level files and auto memory are local |
| **Worktree** | 📘 `CLAUDE.local.md` is per worktree; auto memory is shared across worktrees of one repo `[S1]` |

## 6.6 Diagnostic example: "Claude forgot our convention"

**Situation.** Dana says: *"Claude used to write tests with Vitest. Today it generated Jest tests. It forgot our convention."* The team convention is "Vitest, colocated `*.test.ts`".

### Step 1: Reproduce and record the context

```text
$ pwd
/home/dana/acme-shop/apps/web
$ claude
> /context
```
Note: working directory, and which entries appear under **Memory files**.

### Step 2: Is the convention written down where it can load?

```bash
cd ~/acme-shop
grep -rn -i "vitest" CLAUDE.md .claude apps/*/CLAUDE.md packages/*/CLAUDE.md docs 2>/dev/null
```

**Possible findings and what each means**

| Finding | Meaning |
|---|---|
| **A. No hit anywhere** | The convention was **never written down**. It lived in someone's chat or auto memory. Not a bug; a documentation gap. |
| **B. Hit only in `~/.claude/CLAUDE.md`** | Scope bug: personal, not team-shared (Scenario 1). |
| **C. Hit in `apps/api/CLAUDE.md` only** | Dana launched in `apps/web/`; the backend file never loaded. Scope or directory issue. |
| **D. Hit in `.claude/rules/testing.md` with `paths: ["**/*.spec.ts"]`** | Pattern doesn't match `*.test.ts`. Glob bug (Scenario 6). |
| **E. Hit in root CLAUDE.md, and it's in `/context`** | Loaded fine. Check for a conflicting instruction (Step 3). |

### Step 3: Look for conflicts and auto memory

```bash
grep -rn -i "jest" CLAUDE.md .claude apps packages ~/.claude 2>/dev/null
```
In the session, run `/memory`, open the auto-memory folder, and read `MEMORY.md` and any `feedback_*.md` for a stale "use Jest" note. If one exists, it is **automatic memory conflicting with project instructions**. 📘 Auto memory is skipped for things CLAUDE.md already says, but a stale entry can still exist `[S1]`.

### Step 4: Rule out environmental causes

```bash
claude --safe-mode          # all customizations off: does Jest still appear?
cd /tmp && CLAUDE_CONFIG_DIR=/tmp/claude-clean claude   # clean config session
```
If Jest disappears in safe mode, a customization is responsible; reintroduce items one at a time `[S2]`.

### Step 5: Corrective actions mapped to findings

| Finding | Fix |
|---|---|
| A | Add to root `CLAUDE.md`: "Tests: Vitest; colocated `*.test.ts`; run with `pnpm vitest run <path>`" |
| B | Move the line to project `CLAUDE.md`; commit |
| C | Move to root `CLAUDE.md` (repo-wide) or a path-scoped rule on `**/*.test.{ts,tsx}` |
| D | Fix glob to `**/*.test.{ts,tsx}` |
| E + stale auto memory | Delete the stale auto-memory file via `/memory`; keep the project instruction |

### Step 6: Verify

1. Restart `claude` from the same directory (`apps/web/`).
2. `/context`: confirm the relevant file appears (or, for a path-scoped rule, ask Claude to read a `.test.ts` file first).
3. Ask: "Add a unit test for `formatPrice`." Confirm Vitest and colocated naming.
4. Repeat from the repo root and from `apps/api/` to confirm consistency.
5. Optionally run `/doctor prompt-audit` for lingering conflicts.

### What the example teaches

"Claude forgot" is usually one of: *never written down*, *wrong scope*, *wrong location*, *glob mismatch*, *conflicting auto memory*, or *a different launch directory*. It is rarely literal forgetting, because each session starts fresh `[S1]`.

## 6.7 Systematic troubleshooting workflow

```text
START: instruction not behaving as expected
 │
 ├─ 1. /context → is the file under "Memory files"?
 │      ├─ NO  → is it a nested file? (expected: not listed until read)
 │      │          ├─ yes → make Claude READ a file there; look for the "Loaded" line
 │      │          └─ no  → location problem: compare with "How CLAUDE.md files load";
 │      │                    check claudeMdExcludes, AGENTS.md rule, cwd
 │      └─ YES → continue
 │
 ├─ 2. Is it a path-scoped rule? → only loads after a matching file is read/edited; check globs
 ├─ 3. Does it import something? → verify every @path relative to the importing file
 ├─ 4. grep for CONFLICTS across project, user, local, rules → remove them
 ├─ 5. /memory → check auto memory for stale notes; toggle if needed
 ├─ 6. Rewrite vague wording; shorten the file
 ├─ 7. Must it be guaranteed? → permissions / hooks
 └─ 8. claude --safe-mode → clean CLAUDE_CONFIG_DIR session
```

---

# Module 7 — Practical Monorepo Case Study

**Scenario.** *Acme Shop* is a pnpm TypeScript monorepo: React frontend, Node.js backend, shared utilities, automated tests, and Terraform-based deployment. Five teams touch it. We design the instruction architecture, then walk five requests through it.

## 7.1 Design principles (🛠 recommendations)

1. **Root stays small.** Only facts true for *every* task.
2. **Narrow by location** when a package is self-contained (directory CLAUDE.md).
3. **Narrow by file pattern** when a topic cuts across directories (path-scoped rules).
4. **Reuse by import** when several files need the same document.
5. **Personal stays personal** (`~/.claude/`, `CLAUDE.local.md`).
6. **Guarantees go to hooks and permissions.**

## 7.2 Directory tree

```text
acme-shop/
├── CLAUDE.md                                  # repo-wide, small
├── CLAUDE.local.md                            # personal, gitignored (not committed)
├── .gitignore
├── .github/
│   ├── CODEOWNERS
│   └── workflows/deploy.yml
├── .claude/
│   ├── settings.json                          # permissions/hooks (settings, NOT instructions)
│   └── rules/
│       ├── testing.md                         # paths: all test files
│       ├── security.md                        # no paths: always on, short
│       ├── frontend/
│       │   └── react-components.md            # paths: apps/web/src/**
│       ├── backend/
│       │   └── api-conventions.md             # paths: apps/api/src/**
│       └── deployment.md                      # paths: infra/**, workflows, Dockerfile
├── docs/
│   └── standards/
│       ├── typescript.md                      # imported by root
│       └── error-handling.md                  # imported by api and shared
├── apps/
│   ├── web/
│   │   ├── CLAUDE.md                          # frontend-specific
│   │   └── src/
│   └── api/
│       ├── CLAUDE.md                          # backend-specific
│       └── src/
├── packages/
│   └── shared/
│       ├── CLAUDE.md                          # shared-lib rules
│       └── src/
└── infra/
    └── terraform/
```

## 7.3 File contents

### Root `CLAUDE.md`

```markdown
# Acme Shop

pnpm monorepo: `apps/web` (React + Vite), `apps/api` (Express), `packages/shared`, `infra/terraform`.

## Commands
- Install: `pnpm install`
- Build all: `pnpm -r build`
- Typecheck and lint: `pnpm typecheck && pnpm lint`
- Test everything: `pnpm -r test`

## Repo-wide conventions
- Conventional Commits; never commit to `main`
- Before reporting a task done: `pnpm typecheck && pnpm lint` must pass

## Standards
@docs/standards/typescript.md

## Layout notes
Area-specific guidance lives in `apps/web/CLAUDE.md`, `apps/api/CLAUDE.md`, `packages/shared/CLAUDE.md`, and `.claude/rules/`.
```

### `docs/standards/typescript.md` (the reusable import)

```markdown
# TypeScript Standards
- `strict: true`; no `any` (use `unknown` + narrowing)
- Named exports only
- `import type` for type-only imports
- No non-null assertions (`!`) outside tests
```

### `docs/standards/error-handling.md` (second reusable import)

```markdown
# Error Handling
- Domain errors extend `AppError` from `@acme/shared`
- Never throw strings; never swallow errors silently
- Convert errors to HTTP responses only at the API boundary
```

### `apps/api/CLAUDE.md`

```markdown
# API (Express)
- Dev: `pnpm --filter api dev`
- Test: `pnpm --filter api test`
- Entry: `src/server.ts`; routes in `src/routes/`; business logic in `src/services/`
@../../docs/standards/error-handling.md
```

### `apps/web/CLAUDE.md`

```markdown
# Web (React + Vite)
- Dev: `pnpm --filter web dev`
- Test: `pnpm --filter web test`
- Components: `src/components/`; hooks: `src/hooks/`; routes: `src/routes/`
- Use design tokens from `src/tokens.css`; do not hard-code colors
```

### `packages/shared/CLAUDE.md`

```markdown
# Shared library (`@acme/shared`)
- No dependency on React, Express, or any app code
- Every exported function needs a unit test and a TSDoc comment
@../../docs/standards/error-handling.md
```

### `.claude/rules/testing.md` *(path-scoped)*

```markdown
---
paths:
  - "**/*.test.{ts,tsx}"
  - "**/tests/**/*"
---

# Testing Rules
- Runner: Vitest. Single file: `pnpm vitest run <path>`
- Colocate tests: `foo.ts` → `foo.test.ts`
- Mock only network and time; never the unit under test
- Frontend: React Testing Library; query by role or label
- Bug fixes need a regression test that fails first
```

### `.claude/rules/security.md` *(unscoped, deliberately tiny)*

```markdown
# Security Basics
- Never print, log, or commit secrets or tokens
- Never edit `.env*` files; ask the user to
- Treat all request input as untrusted
```

### `.claude/rules/frontend/react-components.md`

```markdown
---
paths:
  - "apps/web/src/**/*.{ts,tsx}"
---

# React Components
- Function components; one per file; filename equals component name
- Props typed with a named `type`
- Data fetching in hooks, not in presentational components
- Accessible by default: labels, roles, keyboard support
```

### `.claude/rules/backend/api-conventions.md`

```markdown
---
paths:
  - "apps/api/src/**/*.ts"
---

# API Conventions
- Plural noun routes; validate input with zod
- Success `{ data }`; errors `{ error: { code, message } }`
- Handlers are thin; logic in `src/services/`
- New endpoint → update `apps/api/openapi.yaml`
```

### `.claude/rules/deployment.md`

```markdown
---
paths:
  - "infra/**/*"
  - ".github/workflows/**/*"
  - "**/Dockerfile"
---

# Deployment
- Terraform lives in `infra/terraform/`; run `fmt`, `validate`, `plan`
- Never run `terraform apply`; the pipeline applies after review
- Pin GitHub Actions to commit SHAs; do not inline secrets
```

### User-level guidance (`~/.claude/CLAUDE.md`; **one developer's file**)

```markdown
# Personal preferences
- Be concise; lead with the diff
- Explain unfamiliar shell commands before running them
- I use zsh with Homebrew paths; keep commands copy-pasteable
```

### Local file (`CLAUDE.local.md`; **gitignored, this repo only**)

```markdown
# My sandbox
- Local API: http://localhost:4010; test user: dev@example.com
- I run the web app on port 5180 to avoid a clash with another project
```

### `.gitignore` excerpt

```gitignore
CLAUDE.local.md
```

### `.github/CODEOWNERS` *(🛠 how reviews map to ownership)*

```text
/CLAUDE.md                          @acme/platform
/docs/standards/                    @acme/platform
/.claude/rules/testing.md           @acme/platform
/.claude/rules/security.md          @acme/security
/.claude/rules/deployment.md        @acme/devops
/.claude/rules/frontend/            @acme/frontend
/.claude/rules/backend/             @acme/backend
/apps/web/CLAUDE.md                 @acme/frontend
/apps/api/CLAUDE.md                 @acme/backend
/packages/shared/CLAUDE.md          @acme/platform
```

## 7.4 Who maintains each file

| File | Maintainer | Audience | Why |
|---|---|---|---|
| Root `CLAUDE.md` | Platform / tech leads | Everyone | Changes affect all work; needs broad review |
| `docs/standards/*.md` | Platform | Everyone who imports them | One source of truth |
| `apps/web/CLAUDE.md`, frontend rules | Frontend team | Frontend work | Domain expertise |
| `apps/api/CLAUDE.md`, backend rules | Backend team | Backend work | Domain expertise |
| `packages/shared/CLAUDE.md` | Platform | Shared lib work | Cross-cutting API stability |
| `.claude/rules/security.md` | Security | Everyone | Policy |
| `.claude/rules/deployment.md` | DevOps | Infra and pipeline work | Risk |
| `~/.claude/CLAUDE.md` | **Each developer** | Only that developer | Personal |
| `CLAUDE.local.md` | **Each developer** | Only that developer, this repo | Personal and gitignored |
| Auto memory | **Claude, per machine** | That developer | Machine-local; not a team asset |
| Org-wide policy (managed CLAUDE.md) | IT / security | Whole organization | Not excludable `[S1]` |

## 7.5 Walking five requests through the architecture

Assume the developer launches `claude` from the repo root (`acme-shop/`) unless noted.

### Request 1: *"Add a new React component, `OrderCard`."*

| Loaded | Trigger | Why it applies |
|---|---|---|
| Root `CLAUDE.md` + `typescript.md` | Launch | Commands, strict TS, named exports |
| `security.md` | Launch (unscoped) | Always-on basics |
| `apps/web/CLAUDE.md` | Claude reads/edits under `apps/web/` | Layout, design tokens |
| `react-components.md` | Claude touches `apps/web/src/**/*.tsx` | Component conventions |
| *Not loaded:* API rules, deployment, testing (until a test file is touched) | | Irrelevant here |

**Stays user-specific:** your explanation style and shell preferences (`~/.claude/CLAUDE.md`), your dev port (`CLAUDE.local.md`).

### Request 2: *"Implement `GET /orders/:id`."*

| Loaded | Trigger | Why |
|---|---|---|
| Root + TS standards + `security.md` | Launch | Baseline |
| `apps/api/CLAUDE.md` + `error-handling.md` import | Claude reads under `apps/api/` | Structure, error rules |
| `backend/api-conventions.md` | Claude touches `apps/api/src/**/*.ts` | REST conventions, zod, response envelope |
| *Not loaded:* any frontend rule | | Correctly absent |

🛠 If you always do backend work, **launching from `apps/api/`** puts `apps/api/CLAUDE.md` and its import in context from message one.

### Request 3: *"Write unit tests for `calculateTotal`."*

| Loaded | Trigger | Why |
|---|---|---|
| Baseline (root, TS, security) | Launch | Always |
| `packages/shared/CLAUDE.md` + `error-handling.md` | Claude reads a file under `packages/shared/` | Shared-lib rules |
| `testing.md` | Claude reads or edits a `*.test.ts` file | Vitest, colocation, mocking policy |

Note that `testing.md` joins **after** the first test file is touched. That is *expected*, not a failure.

### Request 4: *"Modify deployment infrastructure: add a staging environment."*

| Loaded | Trigger | Why |
|---|---|---|
| Baseline | Launch | Always |
| `deployment.md` | Claude touches `infra/**` or workflows | Terraform and pipeline rules |
| Guardrail | `.claude/settings.json` (permissions or hook) | 🛠 **Enforce** "never `terraform apply`" here, since CLAUDE.md alone is guidance `[S1]` |

### Request 5: *"Onboard a new developer."*

| Step | Result |
|---|---|
| `git clone` and `pnpm install` | They receive root CLAUDE.md, all directory CLAUDE.md files, `.claude/rules/`, `docs/standards/`, `.claude/settings.json` |
| First `claude` session | `/context` shows the root CLAUDE.md and unscoped rules; nested files load as work progresses |
| They create their own `~/.claude/CLAUDE.md` and `CLAUDE.local.md` | Personal preferences, never committed |
| They do **not** receive: Alice's `~/.claude/CLAUDE.md`, anyone's auto memory, anyone's `CLAUDE.local.md` | 📘 Personal by design `[S1]` |

The onboarding test: *"If we deleted everyone's home directory, would the new hire's Claude still behave like the team's?"* If yes, the team's rules are in Git where they belong.

## 7.6 What should remain user-specific?

| Keep personal | Reason |
|---|---|
| Communication style, verbosity | Taste |
| Shell, editor, OS quirks | Machine-specific |
| Local URLs, ports, test accounts | Environment-specific (`CLAUDE.local.md`) |
| "Remember I prefer X" notes | Auto memory |
| Anything that would surprise or constrain a teammate | Doesn't belong in shared files |

## 7.7 Why this design works (and what it trades off)

| Strength | Trade-off |
|---|---|
| Idle context stays small; rules appear when relevant | Rules arrive *during* a task, so a human reading `/context` at launch sees few files |
| Clear ownership per file | More files to keep consistent; needs periodic `/doctor prompt-audit` |
| Reuse via two imports | Imports still load at launch, so keep imported files short |
| Guarantees live in settings and hooks | You maintain two systems (instructions and enforcement) |

---

# Module 8 — Hands-On Labs

**Safety rules for every lab.**
- Work in a throwaway directory such as `~/labs/ccar-lab-N`. Never use a real repository.
- Run `git init` in each lab so `git status` and `git check-ignore` behave realistically.
- Don't touch your real `~/.claude/CLAUDE.md`. Where a lab needs user-level behavior, use the **clean config directory** technique: `CLAUDE_CONFIG_DIR=$HOME/labs/fake-claude-home claude`. 📘 This points Claude Code at a different configuration directory, so your real user-level files are untouched `[S2]`. (The first launch shows first-run setup screens and asks you to log in again `[S2]`.)
- Nested CLAUDE.md files load on demand. Create them **from your shell**, then ask Claude to **read** a file in that folder `[S1]`.

---

## Lab 1 (Beginner): Create a minimal CLAUDE.md

**Objective.** Create a project CLAUDE.md and prove Claude Code loaded it.

**Starting structure.**
```text
~/labs/ccar-lab-1/
└── package.json
```

**Tasks.**
1. `mkdir -p ~/labs/ccar-lab-1 && cd ~/labs/ccar-lab-1 && git init`
2. Create `package.json` containing `{ "name": "lab1", "scripts": { "test": "echo ok" } }`.
3. Create `CLAUDE.md` with a title, a Commands section (`npm test`), and two concrete conventions.
4. Launch `claude`. Run `/context`.
5. Ask: "What test command should you use here?"

**Hints.**
- Keep instructions concrete (📘 "Run `npm test` before committing", not "test your changes" `[S1]`).
- Look under **Memory files** in `/context`.

**Expected structure.**
```text
ccar-lab-1/
├── CLAUDE.md
└── package.json
```
```markdown
# Lab 1
## Commands
- Test: `npm test`
## Conventions
- Use 2-space indentation
- Name files in kebab-case
```

**Verification.** `/context` lists `CLAUDE.md` under Memory files; Claude's answer mentions `npm test`.

**Solution and explanation.** The file sits in the working directory, which is discovered and loaded **at launch** `[S1]`. If it doesn't appear, check you launched from `ccar-lab-1/` and that the filename is exactly `CLAUDE.md`.

---

## Lab 2 (Beginner–Intermediate): Separate personal from team guidance

**Objective.** Place each instruction at the correct scope: project, local, or user.

**Starting structure.** A single file mixing everything:
```text
~/labs/ccar-lab-2/
└── CLAUDE.md
```
```markdown
# Lab 2
- Use pnpm; run tests with `pnpm test`
- No `any` in TypeScript
- I like very short answers
- My local API is http://localhost:4010
- I use fish shell
```

**Tasks.**
1. Classify each line: **team**, **personal-this-project**, or **personal-everywhere**.
2. Keep team lines in `CLAUDE.md`.
3. Move personal-this-project lines into `CLAUDE.local.md` and add it to `.gitignore`.
4. Put personal-everywhere lines into a **fake** user-level file at `~/labs/fake-claude-home/CLAUDE.md`.
5. Launch with `CLAUDE_CONFIG_DIR=$HOME/labs/fake-claude-home claude` and run `/context`.

**Hints.**
- Re-read the Section 2.8 decision list.
- `git status` should show `CLAUDE.md` and `.gitignore` as new, but **not** `CLAUDE.local.md`.

**Expected structure.**
```text
ccar-lab-2/
├── .gitignore            # contains: CLAUDE.local.md
├── CLAUDE.md             # pnpm + no any
└── CLAUDE.local.md       # local API URL
~/labs/fake-claude-home/
└── CLAUDE.md             # short answers, fish shell
```

**Verification.**
```bash
git check-ignore -v CLAUDE.local.md   # prints the .gitignore rule that matches
git status --short                    # CLAUDE.local.md must not appear
```
`/context` should show all three memory files for this session.

**Solution and explanation.** "Short answers" and "fish shell" are about *you* in *every* project, so user-level. The sandbox URL is about *you* in *this* project, so `CLAUDE.local.md`. 📘 Local files load alongside CLAUDE.md and are appended after it at that level `[S1]`. A teammate cloning this repo gets only `CLAUDE.md`.

---

## Lab 3 (Intermediate): Refactor a monolithic file into `.claude/rules/`

**Objective.** Split a long CLAUDE.md into topic rules, with path scoping.

**Starting structure.**
```text
~/labs/ccar-lab-3/
├── CLAUDE.md
├── apps/api/src/orders.ts
└── apps/web/src/OrderCard.tsx
```
```markdown
# Lab 3
## Commands
- Test: `pnpm test`
## General
- TypeScript strict; named exports only
## API
- Validate input with zod
- Errors: { error: { code, message } }
## React
- Function components only
- One component per file
## Testing
- Vitest; colocate tests as *.test.ts(x)
## Deployment
- Never run terraform apply
```

**Tasks.**
1. Keep **Commands** and **General** in `CLAUDE.md`.
2. Create `.claude/rules/api.md` with `paths: ["apps/api/src/**/*.ts"]`.
3. Create `.claude/rules/react.md` with `paths: ["apps/web/src/**/*.tsx"]`.
4. Create `.claude/rules/testing.md` scoped to test files.
5. Leave **Deployment** in `CLAUDE.md` as context, and write down (no need to implement) how you would enforce it with a hook or a permission rule.
6. Launch Claude, run `/context`, then ask Claude to **read** `apps/web/src/OrderCard.tsx`.

**Hints.**
- Frontmatter goes at the very top of the file between `---` markers `[S1]`.
- Quote glob strings.
- Only `paths` is read from frontmatter `[S1]`.

**Expected structure.**
```text
ccar-lab-3/
├── CLAUDE.md                     (commands, general, deployment note)
├── .claude/rules/
│   ├── api.md                    (paths: apps/api/src/**/*.ts)
│   ├── react.md                  (paths: apps/web/src/**/*.tsx)
│   └── testing.md                (paths: **/*.test.{ts,tsx})
└── apps/...
```

**Verification.**
1. At launch, `/context` lists only `CLAUDE.md` (all three rules have `paths`).
2. After Claude reads `OrderCard.tsx`, `react.md` should be in effect. Ask Claude "what rules apply to this file?" ❓ Whether `/context` reflects on-demand rules mid-session isn't spelled out in what I read, so confirm using Claude's answer and the `Loaded` indication, or an `InstructionsLoaded` hook `[S1]`.
3. Ask Claude to read `apps/api/src/orders.ts`; now `api.md` should apply too.

**Solution and explanation.** Path-scoped rules enter context only on matching file access `[S1]`, so a clean launch list is correct. If a rule never applies, check glob vs real path, YAML validity (`claude --debug` shows parse errors `[S1]`), and `.md` extension.

---

## Lab 4 (Intermediate–Advanced): Add `@import` references for package-specific standards

**Objective.** Build Example C from Module 3 and prove which imports resolve.

**Starting structure.**
```text
~/labs/ccar-lab-4/
├── CLAUDE.md
├── docs/standards/{typescript.md, testing.md, api-conventions.md}
└── apps/{api,web}/src/
```

**Tasks.**
1. Write three short standards files (3–5 bullets each).
2. Root `CLAUDE.md`: import only `typescript.md`.
3. Create `apps/api/CLAUDE.md` importing `api-conventions.md` and `testing.md` using paths **relative to that file**.
4. Create `apps/web/CLAUDE.md` importing only `testing.md`.
5. Launch **from `apps/api/`**. Run `/context`.
6. Relaunch **from the repo root**, ask Claude to read `apps/api/src/<some file>`, and watch for a `Loaded` line.
7. **Break it deliberately**: change one import to `@docs/standards/api-conventions.md` (wrong base), restart, and observe.

**Hints.**
- From `apps/api/`, the shared docs are `../../docs/standards/...`.
- Verify with `ls -l ../../docs/standards/api-conventions.md` from `apps/api/`.

**Expected structure.** As the Module 3 Example C tree.

**Verification.**
- Launch from `apps/api/`: Memory files include root and `apps/api/CLAUDE.md` `[S1][S2]`.
- Launch from root: only root at launch; API file appears after a read.
- Broken import: Claude no longer reflects API conventions; `/doctor prompt-audit` should flag the dangling reference (📘 it checks "references to files or commands that don't exist"; requires v2.1.283+ `[S1]`).

**Solution and explanation.** Relative imports resolve from the importing file `[S1]`. Because both launches differ only in *which files are in cwd or ancestors*, you see launch-time vs on-demand loading side by side.

---

## Lab 5 (Advanced): Diagnose a deliberately misconfigured repository

**Objective.** Find and fix six planted defects using only inspection commands.

**Starting structure** *(create exactly this)*:
```text
~/labs/ccar-lab-5/
├── CLAUDE.md
├── .gitignore                      (empty)
├── CLAUDE.local.md
├── docs/standards/
│   └── api-conventions.md
├── .claude/rules/
│   ├── testing.txt
│   └── frontend.md
└── apps/
    ├── api/
    │   ├── CLAUDE.md
    │   └── src/orders.ts
    └── web/
        └── src/OrderCard.tsx
```

**Planted defects.**

| # | File | Defect |
|---|---|---|
| D1 | `CLAUDE.md` | Contains "Use default exports", and `apps/web/...` guidance says "named exports only" |
| D2 | `apps/api/CLAUDE.md` | `` `@docs/standards/api-conventions.md` `` (in backticks, wrong base) |
| D3 | `.claude/rules/testing.txt` | Correct rules, wrong extension |
| D4 | `.claude/rules/frontend.md` | `paths: ["apps/web/**/*.vue"]` in a React project |
| D5 | `CLAUDE.local.md` | Not in `.gitignore` |
| D6 | `CLAUDE.md` | Says "Never run `rm -rf`", and you want a guarantee |

**Tasks.**
1. For each defect, state *symptom*, *investigation command*, *fix*, *verification*.
2. Apply the fixes.
3. Run `/doctor prompt-audit` before and after.

**Hints.**
- Use the 8-step investigation ladder (5.2).
- `git check-ignore -v CLAUDE.local.md` for D5.
- D6 is not solved inside CLAUDE.md.

**Expected end state.**
```text
ccar-lab-5/
├── CLAUDE.md                 (conflict removed; rm -rf note kept as context)
├── .gitignore                (CLAUDE.local.md)
├── CLAUDE.local.md
├── docs/standards/api-conventions.md
├── .claude/rules/
│   ├── testing.md            (renamed)
│   └── frontend.md           (paths: apps/web/**/*.{ts,tsx})
└── apps/api/CLAUDE.md        (@../../docs/standards/api-conventions.md, no backticks)
```

**Verification procedure.**
```bash
ls .claude/rules                       # testing.md present, no .txt
git check-ignore -v CLAUDE.local.md    # prints the matching ignore rule
grep -rn -i "default export" CLAUDE.md apps .claude   # no contradictions
cd apps/api && ls -l ../../docs/standards/api-conventions.md
```
Then in Claude: read `apps/api/src/orders.ts` and `apps/web/src/OrderCard.tsx`; confirm the API conventions and the frontend rule apply; run `/doctor prompt-audit` again to see fewer findings.

**Solution and explanation.**

| # | Fix | Why |
|---|---|---|
| D1 | Remove one side of the contradiction; add an explicit exception if one is real | 📘 Conflicts are resolved "arbitrarily" `[S1]` |
| D2 | `@../../docs/standards/api-conventions.md`, no backticks | Code spans skip imports; relative-to-file base `[S1]` |
| D3 | Rename to `testing.md`, optionally add `paths` | 📘 Only `.md` files are discovered `[S1]` |
| D4 | Match real files: `apps/web/**/*.{ts,tsx}` | A glob that matches nothing means the rule never loads |
| D5 | Add `CLAUDE.local.md` to `.gitignore` | 📘 Docs say to gitignore it `[S1]` |
| D6 | Add a permission `deny` rule or a PreToolUse hook; keep the note | 📘 CLAUDE.md is not enforcement `[S1][S2]` |

---

# Module 9 — Certification Exam Preparation

> No question in this guide is an actual CCAR-F / CCA-F exam question. They are original practice items. Community sources report the *themes* the exam tests; I could not verify them against the official exam guide 🎓.

## 9.1 Most important concepts to remember

1. **CLAUDE.md is context, not enforcement.** Guarantees need permissions or hooks `[S1][S2]`.
2. **Four documented scopes**, broad to specific: managed policy → user (`~/.claude/CLAUDE.md`) → project (`./CLAUDE.md` or `./.claude/CLAUDE.md`) → local (`./CLAUDE.local.md`) `[S1]`.
3. **User-level is personal and never in Git.** Team standards belong in the project file `[S1]`.
4. **Upward = launch; downward = on demand.** The cwd and ancestors load at launch; subdirectory files load after Claude reads a file there `[S1]`.
5. **Concatenation, not override.** Contradictions are resolved arbitrarily; remove them `[S1]`.
6. **`@path` imports** resolve relative to the importing file, nest four hops, skip code spans and fenced blocks, load at launch, and **don't reduce context** `[S1]`.
7. **`.claude/rules/`**: recursive `.md` discovery; no `paths` → launch; `paths` → loads when a matching file is read or edited; `paths` is the only frontmatter field read `[S1]`.
8. **`/memory`** lists and opens memory files and toggles auto memory. **`/context`** shows what is actually loaded `[S1][S2]`.
9. **Auto memory is Claude's, machine-local, and per repo.** First 200 lines or 25 KB of `MEMORY.md` load at start `[S1]`.
10. **Size matters.** Target under 200 lines per file `[S1]`.

## 9.2 Easily confused concepts

| Pair | The distinction |
|---|---|
| CLAUDE.md vs `settings.json` | Prose guidance Claude reads vs machine-read switches (permissions, hooks, env) |
| CLAUDE.md vs auto memory | You write vs Claude writes; team-shared vs machine-local |
| `~/.claude/CLAUDE.md` vs `CLAUDE.local.md` | Personal across all projects vs personal in one project |
| `./CLAUDE.md` vs `./.claude/CLAUDE.md` | Same documented role; location convention only |
| Directory CLAUDE.md vs path-scoped rule | Trigger is *location* vs trigger is *file pattern* |
| Unscoped rule vs `paths` rule | Always at launch vs on matching file access |
| `@import` vs `.claude/rules/` | Reuse and organization (no context saving) vs topic split and conditional loading |
| `/memory` vs `/context` | Locations and editing vs what's in the window |
| Discovery vs loading | Is it found vs when it enters context |
| Scope vs precedence | Intended audience vs conflict resolution (which isn't a simple override) |
| CLAUDE.md vs skills | Always-needed facts vs procedures loaded when relevant |
| Settings precedence vs CLAUDE.md ordering | Settings have a defined override order; CLAUDE.md files are concatenated |

## 9.3 Common distractors in multiple-choice questions

| Distractor pattern | Why it's wrong |
|---|---|
| "Update Claude Code; the teammate's version is outdated" | Missing instructions are a scope issue, not a version issue, in the typical scenario |
| "CLAUDE.md must be in `.claude/` or it's ignored" | Root `./CLAUDE.md` is explicitly valid `[S1]` |
| "Project file must `@import` the user-level file" | Wrong direction and wrong purpose; also external-import approval rules apply `[S1]` |
| "Use `/memory` to tell Claude which section to prioritize" | `/memory` doesn't do that `[S1]` |
| "Later/deeper file always overrides" | Documented as concatenation `[S1]` |
| "Imports reduce context" | Documented as not reducing it `[S1]` |
| "Add more emphasis (ALL CAPS, 'NEVER') to guarantee compliance" | Doesn't change CLAUDE.md's non-enforced nature |
| "Put everything in the root file so it's always loaded" | Raises context cost; lowers adherence |
| "Subdirectory CLAUDE.md files all load at launch" | They load on demand `[S1]` |
| "Put team standards in `~/.claude/CLAUDE.md` for consistency" | Not shared via Git |
| "Auto memory is how teams share conventions" | Machine-local, per developer `[S1]` |

## 9.4 Scenario decision rules

| If the scenario says… | Think… |
|---|---|
| "New teammate doesn't get X" | User-level vs project-level; move to project file |
| "Only when working in package P" | Directory CLAUDE.md, or path-scoped rule |
| "For all test files across the repo" | Path-scoped rule with a glob |
| "Same standard used by several packages" | One file, `@import` it |
| "File is too long / adherence dropping" | Path-scoped rules or trim; **not** imports |
| "Backend rule affects frontend" | Scope too broad: move down or add `paths` |
| "Rule isn't taking effect" | `/context` first; then location, glob, path, wording, conflict |
| "Different behavior between sessions" | cwd, on-demand loading, auto memory, `CLAUDE.local.md`, compaction |
| "Must never / must always happen" | Permissions or hooks |
| "Personal preference for this repo only" | `CLAUDE.local.md` + `.gitignore` |
| "Organization-wide, can't be skipped" | Managed policy CLAUDE.md |

## 9.5 Quick-reference comparison table

| Mechanism | Loaded | Shared? | Narrowed by | Saves idle context? | Enforces? |
|---|---|---|---|---|---|
| `~/.claude/CLAUDE.md` | Launch | No | Nothing (all your projects) | No | No |
| `./CLAUDE.md` / `.claude/CLAUDE.md` | Launch | Git | Where cwd is | No | No |
| `./CLAUDE.local.md` | Launch | No (gitignore) | Project | No | No |
| Ancestor CLAUDE.md | Launch | Git | Directory tree | No | No |
| Subdirectory CLAUDE.md | On demand | Git | Location | **Yes** | No |
| `.claude/rules/*.md` (no `paths`) | Launch | Git | Topic only | No | No |
| `.claude/rules/*.md` (`paths`) | On matching file access | Git | File pattern | **Yes** | No |
| `@import` | With parent | Git | Parent's scope | **No** | No |
| Auto memory | Launch (first 200 lines or 25 KB) | No | Per repo, per machine | No | No |
| Permissions / hooks | Client-side | Settings file | Config scope | n/a | **Yes** |

## 9.6 Where does this instruction belong? (checklist)

☐ Organization-wide and non-negotiable? → **Managed policy**
☐ Only me, all projects? → **`~/.claude/CLAUDE.md`**
☐ Only me, this repo? → **`CLAUDE.local.md`** (gitignored)
☐ Whole team, whole repo? → **Root or `.claude/CLAUDE.md`**
☐ One package or folder? → **Directory CLAUDE.md** (or path-scoped rule)
☐ One file type across folders? → **`.claude/rules/` with `paths`**
☐ Same text needed in several files? → **`@import`**
☐ Always-on topic split for readability? → **`.claude/rules/` without `paths`**
☐ Multi-step, occasional procedure? → **Skill**
☐ Must be guaranteed? → **Permissions or hook**
☐ Concrete, short, non-conflicting? → If not, fix before filing

---

# Module 10 — Assessment and Answer Key

Answer all 25 first. Check the key afterward.

## Part A: Multiple choice (Q1–Q10)

**Q1.** Which of these is **not** delivered to a new teammate when they clone the repository?
- A) `./CLAUDE.md`
- B) `./.claude/CLAUDE.md`
- C) `~/.claude/CLAUDE.md` on the original author's laptop
- D) `.claude/rules/testing.md`

**Q2.** A developer launches `claude` in `acme/apps/api/`. The repository has `acme/CLAUDE.md`, `acme/apps/api/CLAUDE.md`, and `acme/apps/api/src/handlers/CLAUDE.md`. Which statement is correct?
- A) The first two load at launch; the third loads after Claude reads a file in `handlers/`.
- B) Only `acme/apps/api/CLAUDE.md` loads.
- C) All three load at launch.
- D) Only `acme/CLAUDE.md` loads; the others load only if imported.

**Q3.** `apps/api/CLAUDE.md` contains `@../../docs/standards/api.md`. That relative path is resolved from:
- A) The directory where `claude` was launched
- B) The repository root
- C) The user's home directory
- D) The directory containing `apps/api/CLAUDE.md`

**Q4.** A team splits a 600-line CLAUDE.md into five files and imports them all with `@`. What is the effect on context size at launch?
- A) Only relevant files are loaded
- B) No reduction: imported files still load at launch
- C) Imported files load on demand
- D) Imports are ignored if the total exceeds 200 lines

**Q5.** `.claude/rules/security.md` has no frontmatter. When does it load?
- A) Only when Claude edits a file with "security" in its name
- B) Only when requested with `/memory`
- C) At launch, with the same priority as `.claude/CLAUDE.md`
- D) It never loads without `paths`

**Q6.** Which frontmatter field does Claude Code read from a rule file?
- A) `paths`
- B) `scope`
- C) `applyTo`
- D) `globs`

**Q7.** What does `/memory` do?
- A) Tells Claude which CLAUDE.md section to prioritize
- B) Erases all saved memory
- C) Forces every CLAUDE.md to reload
- D) Lists memory file locations, opens files in your editor, and toggles auto memory

**Q8.** Two loaded files give contradictory instructions. According to the docs:
- A) The deeper file always wins
- B) Claude may pick one arbitrarily, so remove the conflict
- C) The user-level file always wins
- D) The project-level file always wins

**Q9.** A team requires that `terraform apply` **never** runs from a Claude session. Best mechanism?
- A) A strongly worded line in CLAUDE.md
- B) A line in `~/.claude/CLAUDE.md`
- C) A permission deny rule or a PreToolUse hook
- D) An `@import` of a policy file

**Q10.** Which are valid locations for project-level CLAUDE.md?
- A) `./CLAUDE.md` or `./.claude/CLAUDE.md`
- B) Only `./CLAUDE.md`
- C) Only `./.claude/CLAUDE.md`
- D) `~/.claude/CLAUDE.md`

## Part B: Scenario-based (Q11–Q20)

**Q11.** A new hire's Claude doesn't follow the naming and testing conventions the rest of the team gets. The conventions exist only in a senior developer's `~/.claude/CLAUDE.md`. What should the team do?
- A) Ask the new hire to upgrade Claude Code
- B) Move the conventions into the project CLAUDE.md (or `.claude/CLAUDE.md` or a rule file) and commit
- C) Add `@~/.claude/CLAUDE.md` to the project CLAUDE.md
- D) Rename the senior's file to `CLAUDE.local.md`

**Q12.** The API team wants conventions applied only to work in `apps/api/`. The QA lead wants test conventions applied to every `*.test.ts(x)` file everywhere. Which pairing is best?
- A) Both in the root CLAUDE.md
- B) Both as imports in the root file
- C) `apps/api/CLAUDE.md` for the API; a path-scoped rule with a test-file glob for tests
- D) Both in `~/.claude/CLAUDE.md`

**Q13.** Four packages need the same error-handling standard, and the four copies have drifted. Best fix?
- A) Keep four copies, add a reminder to sync
- B) Put one `docs/standards/error-handling.md` and `@import` it from each package's CLAUDE.md
- C) Put it in `~/.claude/CLAUDE.md`
- D) Put it only in the root file and delete package files

**Q14.** An organization wants a security policy applied in every Claude Code session on company laptops that individual developers cannot exclude. Best location?
- A) Each developer's `~/.claude/CLAUDE.md`
- B) A project CLAUDE.md in every repo
- C) `claudeMdExcludes` in project settings
- D) The managed policy CLAUDE.md deployed by IT

**Q15.** A developer wants a local sandbox URL applied in one repository, never committed. Best choice?
- A) Root CLAUDE.md
- B) `~/.claude/CLAUDE.md`
- C) `CLAUDE.local.md`, listed in `.gitignore`
- D) `.claude/rules/sandbox.md`

**Q16.** Launched from the repo root, Claude's first answer to an API question ignores rules in `apps/api/CLAUDE.md`. What best explains this and what is the lowest-effort remedy?
- A) A bug; reinstall
- B) Subdirectory files load on demand; have Claude read a file under `apps/api/` or launch from `apps/api/`
- C) The file must be renamed to `.claude/CLAUDE.md`
- D) Subdirectory CLAUDE.md files are never loaded

**Q17.** The root CLAUDE.md has grown to 900 lines and adherence is dropping. Which change best reduces the content loaded for most tasks?
- A) Split it into five files and import all five from the root
- B) Add "IMPORTANT" in front of the key lines
- C) Move area- and file-type-specific content into path-scoped rules and keep the root short
- D) Move everything into `~/.claude/CLAUDE.md`

**Q18.** A repo has an `AGENTS.md` (used by another tool) and a `CLAUDE.md` in the root. Claude isn't using the guidance in `AGENTS.md`. Best fix?
- A) Delete `CLAUDE.md`
- B) Add `@AGENTS.md` to `CLAUDE.md`, with Claude-specific notes below
- C) Rename `AGENTS.md` to `.claude/rules/agents.txt`
- D) Nothing; Claude always reads both

**Q19.** "Run lint before every commit" must happen every time, not just usually. Where should it live?
- A) A bullet in CLAUDE.md
- B) A PreToolUse hook (with the guidance in CLAUDE.md for context)
- C) A path-scoped rule
- D) Auto memory

**Q20.** In a monorepo launched from the root, you're working only on `packages/shared`. Other teams' CLAUDE.md files above you are noisy. Which setting skips specific ones locally?
- A) `claudeMdExcludes` in `.claude/settings.local.json`
- B) `paths` frontmatter
- C) `/memory` toggle
- D) `CLAUDE_CONFIG_DIR`

## Part C: Troubleshooting (Q21–Q25)

**Q21.** CLAUDE.md contains `@"docs/standards.md"`. The standards never apply. Most likely cause?
- A) The file is too short
- B) Quoted paths aren't imported
- C) Imports only work in `~/.claude/CLAUDE.md`
- D) The import should be in `settings.json`

**Q22.** `.claude/rules/testing.md` has `paths: ["**/*.spec.ts"]`, but the repo's tests are named `*.test.ts`. Claude ignores the rule when editing tests. First fix?
- A) Add `@testing.md` to root
- B) Remove all frontmatter fields except `scope`
- C) Fix the glob to match real files, such as `**/*.test.{ts,tsx}`
- D) Move the file to `~/.claude/rules/`

**Q23.** Claude suggested pnpm yesterday and npm today in the same repo. CLAUDE.md doesn't mention package managers. What's the most useful first diagnostic action and fix?
- A) Re-run `/init` and hope
- B) Run `/memory`, inspect auto memory for stale notes, and add an explicit "Package manager: pnpm" line to the project CLAUDE.md
- C) Switch to `~/.claude/CLAUDE.md`
- D) Add three more imports

**Q24.** `/context` confirms the project CLAUDE.md is loaded, which says "write clean code." Claude's style varies. Best action?
- A) Reload memory
- B) Replace vague text with concrete, verifiable instructions (e.g. "No `any`; named exports; max function length 40 lines")
- C) Move it to a user file
- D) Convert it to an import

**Q25.** After launching from the repo root, an engineer sees only the root CLAUDE.md under **Memory files** in `/context` and concludes `apps/web/CLAUDE.md` is broken. What's the best response?
- A) Rename the file
- B) This is expected: subdirectory files load on demand; ask Claude to read a file under `apps/web/` and look for the `Loaded` indication
- C) Add the file path to `.gitignore`
- D) Disable auto memory

---

# Answer Key

### Q1: **C**
- **Why:** User-level files live in the author's home directory; Git never carries them. 📘 `[S1]`
- **Wrong:** A, B are the two project locations (committed). D is a project rule (committed).
- **Concept:** user vs project scope.

### Q2: **A**
- **Why:** Files in the cwd and ancestors load at launch; subdirectory files load once Claude reads a file there. 📘 `[S1]`
- **Wrong:** B ignores ancestors. C ignores on-demand loading. D invents an import requirement.
- **Concept:** discovery direction and loading timing.

### Q3: **D**
- **Why:** Relative imports resolve relative to the file containing the import. 📘 `[S1]`
- **Wrong:** A is the common mistake. B and C are never the base.
- **Concept:** `@import` path resolution.

### Q4: **B**
- **Why:** Imports organize a file but don't reduce context, since imported files load at launch. 📘 `[S1]`
- **Wrong:** A and C describe path-scoped or directory loading, not imports. D invents a rule.
- **Concept:** imports vs conditional loading.

### Q5: **C**
- **Why:** Rules without `paths` load at launch, with the same priority as `.claude/CLAUDE.md`. 📘 `[S1]`
- **Wrong:** A describes a path-scoped rule. B misuses `/memory`. D is false.
- **Concept:** unscoped vs scoped rules.

### Q6: **A**
- **Why:** "`paths` is the only field Claude Code reads from a rule." 📘 `[S1]`
- **Wrong:** `scope`, `applyTo`, and `globs` aren't read; other tools use similar names, which is the lure.
- **Concept:** rule frontmatter.

### Q7: **D**
- **Why:** It lists memory file locations across scopes, opens them in your editor, toggles auto memory, and opens the auto-memory folder. 📘 `[S1]`
- **Wrong:** A, B, C describe functions it doesn't document.
- **Concept:** purpose of `/memory`.

### Q8: **B**
- **Why:** Files are concatenated; "Claude may pick one arbitrarily." 📘 `[S1]`
- **Wrong:** A, C, D claim a universal priority order the docs don't give.
- **Concept:** precedence is not simple override.

### Q9: **C**
- **Why:** CLAUDE.md is context, not enforcement; permissions and hooks guarantee. 📘 `[S1][S2]`
- **Wrong:** A is still guidance. B is personal and unenforced. D loads text; it doesn't enforce.
- **Concept:** guidance vs guarantee.

### Q10: **A**
- **Why:** Both `./CLAUDE.md` and `./.claude/CLAUDE.md` are documented project locations. 📘 `[S1]`
- **Wrong:** B and C wrongly restrict. D is user-level.
- **Concept:** project-level locations.

### Q11: **B**
- **Why:** The cause is scope. Team guidance must live in committed project files.
- **Wrong:** A is a red herring. C imports a personal file into shared config, and external imports trigger approval prompts `[S1]`. D keeps it personal.
- **Concept:** where an instruction belongs; user vs team.

### Q12: **C**
- **Why:** Area-specific content fits a directory file (or a path-scoped rule). A cross-directory file pattern fits a `paths` glob. 📘 `[S1]`
- **Wrong:** A overloads the root. B doesn't narrow anything. D isn't shared.
- **Concept:** directory vs path-scoped; choosing the right trigger.

### Q13: **B**
- **Why:** One source of truth, referenced by `@import`. 📘 `[S1]`
- **Wrong:** A keeps drift. C is personal. D loses package autonomy and loads it everywhere.
- **Concept:** reuse via import.

### Q14: **D**
- **Why:** 📘 Managed policy CLAUDE.md applies organization-wide and "cannot be excluded by individual settings." `[S1]`
- **Wrong:** A is personal. B is per repo. C can't exclude managed files.
- **Concept:** managed policy scope.

### Q15: **C**
- **Why:** Personal and project-specific is `CLAUDE.local.md`; add it to `.gitignore`. 📘 `[S1]`
- **Wrong:** A and D are committed. B applies to all projects.
- **Concept:** local scope.

### Q16: **B**
- **Why:** On-demand loading for subdirectory files. Reading a file under that folder triggers it; launching from `apps/api/` loads it at launch. 📘 `[S1]`
- **Wrong:** A is unfounded. C is unnecessary. D is false.
- **Concept:** discovery vs loading.

### Q17: **C**
- **Why:** Path-scoped rules reduce loaded content; keeping the root short reduces launch cost and improves adherence. 📘 `[S1]`
- **Wrong:** A reshuffles but doesn't reduce launch context. B doesn't change size or enforcement. D removes it from the team.
- **Concept:** trade-offs; imports vs rules.

### Q18: **B**
- **Why:** By default Claude reads `AGENTS.md` only when no CLAUDE.md exists in the cwd or above; an `@AGENTS.md` import includes it. 📘 `[S1]`
- **Wrong:** A may work but drops Claude-specific content; C: `.txt` isn't discovered and AGENTS.md isn't a rule; D contradicts the default.
- **Concept:** import for cross-tool sharing; default behavior.

### Q19: **B**
- **Why:** A must-always step needs a hook. 📘 `[S1][S2]`
- **Wrong:** A, C, D are all non-enforcing context.
- **Concept:** guidance vs guarantee.

### Q20: **A**
- **Why:** 📘 `claudeMdExcludes` skips specific CLAUDE.md files by path or glob; putting it in `.claude/settings.local.json` keeps it local `[S1]`.
- **Wrong:** B scopes rules. C toggles auto memory. D relocates the whole config directory.
- **Concept:** monorepo noise management.

### Q21: **B**
- **Why:** 📘 "A path wrapped in quotes isn't imported at all." `[S1]`
- **Wrong:** A, C, D are not documented causes.
- **Concept:** import syntax pitfalls.

### Q22: **C**
- **Why:** The glob doesn't match real files, so the rule never loads. Brace expansion is documented. 📘 `[S1]`
- **Wrong:** A: you can't import a rule to force scoping; B: `scope` isn't a field; D: moving to user level makes it personal.
- **Concept:** path-matching behavior.

### Q23: **B**
- **Why:** `/memory` leads to the auto-memory folder; stale or missing auto-memory notes explain cross-session drift; the durable fix is an explicit shared instruction. 📘 `[S1]`
- **Wrong:** A is a gamble. C makes it personal. D adds no information.
- **Concept:** memory vs configuration; cross-session inconsistency.

### Q24: **B**
- **Why:** The file is loaded, so the issue is wording. 📘 Concrete, verifiable instructions improve adherence `[S1][S2]`.
- **Wrong:** A, C, D don't address vagueness.
- **Concept:** loaded vs followed.

### Q25: **B**
- **Why:** 📘 Nested files don't show under **Memory files** at launch; they load after a read, with a `Loaded` line `[S1]`.
- **Wrong:** A, C, D don't address the cause.
- **Concept:** on-demand loading is expected behavior.

## Coverage map

| Task area | Questions |
|---|---|
| User / project / directory hierarchy | 1, 2, 10, 11, 14, 15, 16, 25 |
| Placement decisions | 11, 12, 13, 15, 19 |
| `@import` | 3, 4, 13, 18, 21 |
| `.claude/rules/` and path scoping | 5, 6, 12, 17, 22 |
| Diagnosing missing, conflicting, mis-scoped, unexpectedly loaded instructions | 8, 16, 21, 22, 23, 24, 25 |
| `/memory` and memory | 7, 23 |
| Guidance vs enforcement | 9, 19 |
| Realistic repositories | 2, 12, 17, 20 |

## Score interpretation

| Score | Reading | Next step |
|---|---|---|
| **23–25** | Exam-ready on Task 3.1 | Re-skim the revision sheet; test the ❓ items in a scratch repo |
| **19–22** | Solid, with gaps | Review the modules listed below for your misses; redo Labs 4 and 5 |
| **14–18** | Understands the pieces, confuses the boundaries | Re-read Modules 2 and 3; rebuild the Section 9.5 table from memory |
| **Below 14** | Foundation not yet stable | Work through Modules 1–4 in order, then Labs 1–3, then retake |

## Topics to revisit by missed question

| Missed | Revisit |
|---|---|
| 1, 11, 14, 15 | 2.1–2.3, 2.7, 2.8 |
| 2, 16, 25 | 2.4, 2.5 |
| 3, 4, 13, 18, 21 | Module 3 |
| 5, 6, 12, 17, 22 | Module 4 |
| 7, 23 | Module 6 |
| 8, 24 | 2.6, 5 (Scenarios 8–9) |
| 9, 19 | 1.2, Scenario 10 |
| 10 | 2.2 |
| 20 | 2.5 and Module 7 |

---

# Source List

### Official documentation (primary authority)

| Tag | URL | Used for |
|---|---|---|
| **[S1]** | https://code.claude.com/docs/en/memory | CLAUDE.md locations, load order, on-demand loading, imports, `.claude/rules/`, path-specific rules, `/memory`, auto memory, AGENTS.md, `claudeMdExcludes`, size guidance, troubleshooting |
| **[S2]** | https://code.claude.com/docs/en/debug-your-config | `/context`, `/memory`, `/status`, `/doctor`, `claude --safe-mode`, clean-config session, common-cause table, subagent and nested-file loading notes |
| **[S3]** | https://code.claude.com/docs/en/settings | Settings scopes and precedence. **Linked from [S1]/[S2]; not read in full for this guide** |
| **[S4]** | https://code.claude.com/docs/en/hooks-guide | PreToolUse hooks and enforcement. **Linked from [S1]; not read in full for this guide** |

Other official pages referenced by [S1] but **not read** here: skills, large-codebases (monorepos), errors (`Instruction file not loaded`), sub-agents, commands. The index of all pages is at https://code.claude.com/docs/llms.txt.

### Community exam material (unofficial; used only for "what the exam tends to test" 🎓)

| Tag | URL |
|---|---|
| **[S5]** | https://github.com/hamzafarooq/claude-certified-architect |
| **[S6]** | https://github.com/OlivierAlter/Claude-Certified-Architect-Foundations-Certification-Exam |
| **[S7]** | https://claudecertifiedarchitect.substack.com/p/claude-certified-architect-exam-domain-716 |
| **[S8]** | https://github.com/daronyondem/claude-architect-exam-guide/blob/main/exam-preparation-guide.md |

### Items I could not verify (test these yourself)

1. The **official exam guide PDF** and its exact Task 3.1 bullet wording (not accessible to me).
2. Behavior when **both** `./CLAUDE.md` and `./.claude/CLAUDE.md` exist.
3. Whether **writes** (not just reads) trigger nested-file loading: the two official pages differ.
4. Whether **imports inside on-demand nested files** expand at that moment (reasonable inference only).
5. The **anchor** for `paths` globs (root-relative is implied by examples, not stated).
6. Whether `/context` displays **on-demand rules** after they load mid-session.

---

# One-Page Revision Sheet

**Golden rule.** CLAUDE.md = *context*, not enforcement. Guarantees → permissions / hooks.

**Four scopes (broad → specific; concatenated, not overriding).**
`Managed policy` → `~/.claude/CLAUDE.md` (you, all projects, **not in Git**) → `./CLAUDE.md` or `./.claude/CLAUDE.md` (team, **in Git**) → `./CLAUDE.local.md` (you, this repo, **gitignore it**).

**Loading.**
- cwd + every **ancestor** → at **launch**.
- **Subdirectory** CLAUDE.md → **on demand**, after Claude **reads** a file there (the memory page also lists write/edit; the debug page says Read only).
- `.claude/rules/*.md` **without** `paths` → launch (same priority as `.claude/CLAUDE.md`).
- `.claude/rules/*.md` **with** `paths` → when a matching file is read/edited.
- `--add-dir` folders: CLAUDE.md **not** loaded unless `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`.
- Managed policy CLAUDE.md **cannot be excluded**; others can via `claudeMdExcludes`.

**Conflicts.** No simple override. "Claude may pick one arbitrarily." → **Delete the conflict.**

**@import.**
- `@path/to/file`, relative to the **importing file** (not cwd). Absolute and `~` allowed.
- Max **4 hops**. Skipped inside `` `code spans` `` and fenced blocks. **Quotes break it.** Spaces need `\ `.
- Loads **at launch**. **Does NOT reduce context.**
- External (outside working dir) project imports → one-time approval dialog.
- `@AGENTS.md` in CLAUDE.md shares one file with other tools.

**Rules.**
- Recursive `.md` discovery; subfolders OK; **one topic per file**.
- Frontmatter: only `paths` (YAML list **or** comma string). Invalid YAML → rule loads **unscoped**.
- Globs: `**/*.ts`, `src/**/*`, brace expansion `src/**/*.{ts,tsx}`.
- Only `.md`. Symlink targets outside the project → treated as external imports.

**Size.** Under ~200 lines per file. Over → move to path-scoped rules, skills, or trim. (Imports don't help.)

**Memory.**
- **Auto memory**: Claude writes it; `~/.claude/projects/<project>/memory/`; machine-local; per repo; first **200 lines / 25 KB** of `MEMORY.md` at start.
- **`/memory`**: lists and opens memory files, toggles auto memory, opens the auto-memory folder. It does **not** tell Claude what to prioritize.
- **`/context`**: shows what's **actually loaded** (Memory files).
- "Remember X" → auto memory. "Add this to CLAUDE.md" → CLAUDE.md.

**Diagnosis ladder.**
1. `/context` loaded? → 2. Right location? → 3. Right scope? → 4. Import path (from importing file)? → 5. Conflict (`grep`, `/doctor prompt-audit`)? → 6. Wording concrete and short? → 7. Needs a guarantee? → 8. `claude --safe-mode`, then clean `CLAUDE_CONFIG_DIR`.

**Where does it go?**
Org-wide → managed · Me, everywhere → `~/.claude` · Me, this repo → `CLAUDE.local.md` · Team, repo-wide → project file · One folder → directory CLAUDE.md · File pattern → path-scoped rule · Reused text → `@import` · Must-never → hook/permission · Multi-step procedure → skill.

**Trap answers.**
✗ "teammate's Claude is outdated" · ✗ "root CLAUDE.md is ignored" · ✗ "import the user file into the project file" · ✗ "`/memory` prioritizes sections" · ✗ "imports reduce context" · ✗ "deeper file always wins" · ✗ "all nested files load at launch" · ✗ "team conventions in `~/.claude`" · ✗ "auto memory is shared with the team".

**Symptom → cause.**
Teammate lacks rule → **user-level scope** · Backend rule in frontend → **too broad / no `paths`** · Nested file ignored → **on-demand, not read yet** · Import dead → **path base, backticks, quotes, spaces, depth** · Rule never fires → **glob mismatch, YAML, `.txt`** · Differs by session → **cwd, auto memory, local file, compaction** · Contradiction → **remove one** · "Never" ignored → **needs hook**.

*End of document.*
