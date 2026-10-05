# JavaScript and TypeScript

ESLint carries the whole family of complexity and size rules. oxlint implements the
same family at much higher speed. SonarJS supplies the readability metric neither
core linter has.

## Contents

- [The rules](#the-rules)
- [ESLint complexity](#eslint-complexity)
- [The `variant` option](#the-variant-option)
- [What ESLint counts that other languages don't](#what-eslint-counts-that-other-languages-dont)
- [Cognitive complexity via SonarJS](#cognitive-complexity-via-sonarjs)
- [oxlint](#oxlint)
- [Recommended config](#recommended-config)
- [Exemptions](#exemptions)

## The rules

| Rule | Measures | Default |
| ---- | -------- | ------- |
| [`complexity`](https://eslint.org/docs/latest/rules/complexity) | Cyclomatic | `max: 20` |
| [`max-depth`](https://eslint.org/docs/latest/rules/max-depth) | Block nesting depth | `4` |
| [`max-nested-callbacks`](https://eslint.org/docs/latest/rules/max-nested-callbacks) | Callback nesting | `10` |
| [`max-lines-per-function`](https://eslint.org/docs/latest/rules/max-lines-per-function) | Function length | `50` |
| [`max-statements`](https://eslint.org/docs/latest/rules/max-statements) | Statements per function | `10` |
| [`max-params`](https://eslint.org/docs/latest/rules/max-params) | Parameter count | `3` |
| `sonarjs/cognitive-complexity` | Cognitive | `15` |

None of the core rules are on in `eslint:recommended`. They all have to be enabled
deliberately.

`max-lines-per-function` also takes `skipBlankLines`, `skipComments` and `IIFEs`, all
defaulting to `false`. `max-statements` takes `ignoreTopLevelFunctions`.

## ESLint complexity

```js
// eslint.config.js
export default [
  {
    rules: {
      complexity: ["error", { max: 15 }],
      // shorthand form, same thing:
      // complexity: ["error", 15],
    },
  },
];
```

**The default is `max: 20`** — double McCabe's recommendation. A project that writes
`complexity: "error"` and stops has set a gate at twice the number they almost
certainly had in mind. Always pass an explicit `max`.

Class field initializers and static blocks are scored independently rather than
folding into the enclosing scope, so a class with many initialized fields will not
inflate the constructor's score.

## The `variant` option

Underused, and directly relevant to the dispatch-table problem.

```js
complexity: ["error", { max: 15, variant: "modified" }]
```

| Variant | Behaviour |
| ------- | --------- |
| `"classic"` (default) | Standard McCabe. Each `case` in a `switch` adds 1 individually |
| `"modified"` | A whole `switch` adds **1**, regardless of case count. Everything else is unchanged |

`"modified"` is the multiway-decision exemption expressed as configuration. If a
codebase leans on dispatch tables — reducers, action handlers, protocol decoders,
discriminated-union switches in TypeScript — this is almost certainly the variant you
want, and it avoids a stream of per-function `eslint-disable` comments.

It is not a way to lower scores generally: it changes exactly one construct, the one
where cyclomatic complexity is known to mislead.

## What ESLint counts that other languages don't

ESLint's `complexity` increments for:

- `if`, `else if`
- Logical operators `||`, `&&`, and the assignment forms `||=`, `&&=`
- Ternaries `?:`
- `switch`, and each `case` under `classic`
- **Optional chaining `?.`**
- **Default parameter values**
- **Destructuring with defaults**

The last three have no counterpart in Go or Python tooling, and they appear
constantly in idiomatic modern TypeScript. A function full of `opts?.retries ?? 3`
and destructured defaults scores materially higher than the equivalent Go, with no
difference in difficulty.

The practical consequence: **do not carry a threshold across languages.** A shared
"complexity must be under 10" policy across a polyglot repo penalises the TypeScript
and lets the Go through.

## Cognitive complexity via SonarJS

The core linter has no readability metric. `eslint-plugin-sonarjs` supplies one, and
it is the rule that separates a readable dispatch table from a nested tangle.

```bash
npm i -D eslint-plugin-sonarjs
```

```js
import sonarjs from "eslint-plugin-sonarjs";

export default [
  sonarjs.configs.recommended,
  {
    rules: {
      // positional argument, not an object
      "sonarjs/cognitive-complexity": ["error", 15],
    },
  },
];
```

The threshold defaults to **15** and the rule is part of the plugin's recommended
config. Note the option is positional — `["error", 15]`, not `["error", { max: 15 }]`.

The standalone `eslint-plugin-sonarjs` repository was archived in October 2024; from
v2.0.0 the rules live in the SonarJS analyzer repository. The npm package name is
unchanged. Check the version in use before quoting rule behaviour.

## oxlint

[oxlint](https://oxc.rs) implements the same rules as ESLint's `complexity` and its
companions, orders of magnitude faster, which makes it viable as a pre-commit gate
where ESLint is not.

```json
{
  "rules": {
    "complexity": ["error", { "max": 15, "variant": "modified" }]
  }
}
```

Same `max` default of **20** and the same `classic` / `modified` variants.

Two things to know:

- None of these rules is on by default; `complexity` sits in the **Restriction**
  category. Each has to be turned on explicitly, like the ESLint originals.
- oxlint implements the companion rules too: `max-depth`, `max-params`,
  `max-lines-per-function`, `max-nested-callbacks` and `max-statements`, with the
  same options (checked against oxlint 1.86). What it lacks is **cognitive
  complexity**. There is no SonarJS equivalent.

So the split is by metric, not by speed. oxlint can carry every rule except cognitive
complexity; add ESLint with SonarJS only for that one rule. If a project runs both,
keep shared rules in one of them, or keep their `max` values identical, so the two
gates do not disagree about the same code.

## Recommended config

```js
// eslint.config.js
import sonarjs from "eslint-plugin-sonarjs";

export default [
  sonarjs.configs.recommended,
  {
    rules: {
      complexity: ["error", { max: 15, variant: "modified" }],
      "sonarjs/cognitive-complexity": ["error", 15],
      "max-depth": ["warn", 4],
      "max-lines-per-function": ["warn", { max: 80, skipBlankLines: true, skipComments: true }],
      "max-params": ["warn", 4],
      "max-nested-callbacks": ["warn", 4],
    },
  },
  {
    // Test files legitimately nest describe/it and run long.
    files: ["**/*.test.ts", "**/*.spec.ts"],
    rules: {
      "max-lines-per-function": "off",
      "max-nested-callbacks": "off",
      "sonarjs/cognitive-complexity": "off",
    },
  },
];
```

Two deliberate choices worth copying: cognitive complexity is an **error** while the
size rules are **warnings**, because the former is the readability signal and the
latter are prompts; and `max-nested-callbacks` is tightened from 10 to 4, since the
default effectively never fires in code that uses `async`/`await`.

For a project on oxlint, the same gate minus cognitive complexity goes in
`.oxlintrc.json`. Nesting depth becomes the readability signal there, so say in the
reply that cognitive complexity is missing and that adding it means ESLint with
SonarJS for that one rule.

```json
{
  "rules": {
    "complexity": ["error", { "max": 15, "variant": "modified" }],
    "max-depth": ["error", 4],
    "max-lines-per-function": ["warn", { "max": 80, "skipBlankLines": true, "skipComments": true }],
    "max-params": ["warn", 4],
    "max-nested-callbacks": ["warn", 4]
  },
  "overrides": [
    {
      "files": ["**/*.test.ts", "**/*.spec.ts"],
      "rules": {
        "max-lines-per-function": "off",
        "max-nested-callbacks": "off"
      }
    }
  ]
}
```

`max-depth` is an error here rather than a warning because, without cognitive
complexity, it is the only rule pointing at nesting.

## Exemptions

```js
// Dispatch over the discriminated union. One branch per message kind, each a single
// call — the score tracks branch count, not difficulty.
// eslint-disable-next-line complexity -- deliberate dispatch table
function handle(msg: Message) {
  switch (msg.kind) {
    // ...
  }
}
```

ESLint supports `--` followed by a description in disable comments. Use it. A bare
`eslint-disable-next-line complexity` records that someone silenced the rule but not
why, which is the same as having no gate. The
[`eslint-comments/require-description`](https://eslint-community.github.io/eslint-plugin-eslint-comments/)
rule can enforce that a reason is always present.

If dispatch tables are common in the codebase, prefer `variant: "modified"` over
scattering disable comments — one config line beats twenty annotations.
