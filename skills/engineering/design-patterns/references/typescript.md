# TypeScript: idiomatic patterns

This file is the source of truth for what each pattern looks like in TypeScript and
modern JavaScript. The catalog files ([creational.md](creational.md),
[structural.md](structural.md), [behavioral.md](behavioral.md)) hold the when, the why
and the cost. Every example targets TypeScript 5+ under `strict`. Plain JavaScript
gets the same shapes with the types removed.

## Contents

- [What changes the catalog in TypeScript](#what-changes-the-catalog-in-typescript)
- [SOLID in TypeScript](#solid-in-typescript)
- [Creational](#creational): [Factory Method](#factory-method),
  [Abstract Factory](#abstract-factory), [Builder](#builder),
  [Prototype](#prototype), [Singleton](#singleton)
- [Structural](#structural): [Adapter](#adapter), [Bridge](#bridge),
  [Composite](#composite), [Decorator](#decorator), [Facade](#facade),
  [Flyweight](#flyweight), [Proxy](#proxy)
- [Behavioral](#behavioral): [Chain of Responsibility](#chain-of-responsibility),
  [Command](#command), [Interpreter](#interpreter), [Iterator](#iterator),
  [Mediator](#mediator), [Memento](#memento), [Observer](#observer),
  [State](#state), [Strategy](#strategy), [Template Method](#template-method),
  [Visitor](#visitor)
- [Java in TypeScript: smells to catch in review](#java-in-typescript-smells-to-catch-in-review)

## What changes the catalog in TypeScript

- **Structural typing.** Any value with the right shape satisfies an interface. No
  `implements` is needed, so adapters, strategies and test fakes are object literals.
  `implements` on a class is only an extra check, never a requirement.
- **First-class functions and closures.** Strategy, Command, Template Method,
  Decorator and Chain of Responsibility become functions. A closure gives private
  state without a class.
- **ES modules.** A module is evaluated once per module instance, so an exported value
  is already a Singleton and a module's exports are already a Facade. The gotcha:
  "once per module instance" is not "once per process". Two copies of a package in
  `node_modules`, a server bundle and a client bundle, hot module reload, or a test
  runner that resets modules per file each give you another instance.
- **Object literals, optional properties, destructuring defaults.** Named options
  replace most Builders.
- **Discriminated unions and narrowing.** A `kind` or `type` field plus an exhaustive
  `switch` turns Visitor, State, Command, Interpreter and Composite into plain data
  and functions. The compiler checks every case.
- **Generators, `Symbol.iterator`, `Symbol.asyncIterator`.** Iterator is built into
  the language, including `for...of`, `for await...of` and early `break`. ES2025
  iterator helpers (`.map`, `.filter`, `.take` on iterators) work on Node 22+.
- **The built-in `Proxy` object.** Metaprogramming traps on any property access. It is
  a different tool from the Proxy pattern, which is usually a plain wrapper.
- **`EventTarget` and `AbortSignal`.** Observer ships in browsers and Node, and one
  `AbortController` can remove a whole group of listeners at once.
- **Spread and `structuredClone`.** Prototype is a copy expression, not a `clone()`
  method.
- **`using` and `Symbol.dispose` (TS 5.2+).** Scope-bound cleanup without
  `try/finally`. TypeScript downlevels the syntax; the runtime needs `Symbol.dispose`
  (Node 20+, current browsers, or a polyfill). Running `using` natively, without
  downleveling, needs Node 24+.

  ```ts
  function openLock(name: string): Disposable {
    console.log(`lock ${name}`);
    return { [Symbol.dispose]: () => console.log(`unlock ${name}`) };
  }

  function migrate() {
    using lock = openLock("migrations");
    // ... work; the lock is released on return or throw
  }
  ```

- **`satisfies` (TS 4.9+).** Checks a registry object against a type while keeping
  its literal keys, which is exactly what a map of strategies or handlers needs.
- **`readonly`, `as const`, `Object.freeze`.** Immutable values make Memento and
  Flyweight safe to share. `readonly` is compile-time only and shallow; `freeze` is
  runtime and also shallow.
- **Private `#fields`.** Real runtime privacy. The `private` keyword is compile-time
  only and disappears in the emitted JavaScript.

## SOLID in TypeScript

- **Single Responsibility.** Keep the `User` data type, the user store and the
  welcome-email notifier in separate modules. Profile rules, persistence and
  marketing copy change for different people.
- **Open/Closed.** A `ShippingCalculator` switch over `ground`, `air` and `sea`
  gets a `drone` case. The fix is earned only if carriers keep being added or the
  same switch repeats elsewhere. Then either a `Record<Carrier, CostFn>` or a union
  with an exhaustive `switch` works; the compiler lists every place a new carrier
  must be handled.
- **Liskov Substitution.** `Penguin extends Bird` with a `fly()` that throws breaks
  every caller of `Bird`. Give callers a narrower `Flier` type instead. TypeScript
  also lets a subtype narrow a *method* parameter: methods are checked bivariantly
  even under `strict`, and `strictFunctionTypes` only covers function-typed
  properties. Declare callbacks as properties, or turn on the typescript-eslint rule
  `method-signature-style: property`.

  ```ts
  class Bird { fly() {} }
  class Penguin extends Bird { swim() {} }

  interface Aviary { admit(b: Bird): void }           // method syntax
  class PenguinPool implements Aviary {
    admit(p: Penguin) { p.swim(); }                   // compiles, crashes on a Sparrow
  }

  interface StrictAviary { admit: (b: Bird) => void } // property syntax
  // @ts-expect-error: parameters of function-typed properties are contravariant
  const pool: StrictAviary = { admit: (p: Penguin) => p.swim() };
  ```

- **Interface Segregation.** A `Worker` with `work`, `eat` and `sleep` forces
  `RobotWorker` to stub two methods. Let each consumer declare the small structural
  type it uses (`{ work(): void }`, or `Pick<Worker, "work">`); no `I` prefix needed.
- **Dependency Inversion.** `Store.checkout` constructing a Stripe client ties the
  business rule to one vendor. The store module declares what it needs in its own
  terms, and the entry point injects a Stripe or PayPal adapter. A handful of
  services never needs a DI container.

  ```ts
  // store.ts owns this type; payment code plugs into it.
  export interface PaymentProcessor {
    charge(amountCents: number, source: string): Promise<{ ok: boolean }>;
  }

  export function createStore(payments: PaymentProcessor) {
    return {
      checkout: (cart: { totalCents: number }, source: string) =>
        payments.charge(cart.totalCents, source),
    };
  }
  // main.ts: const store = createStore(stripeProcessor(process.env.STRIPE_KEY ?? ""));
  ```

## Creational

### Factory Method

**Idiomatic form:** a function that picks the implementation and returns a structural
type, usually switching on a config union.

```ts
interface BlobStore {
  put(key: string, body: Uint8Array): Promise<void>;
  get(key: string): Promise<Uint8Array | undefined>;
}

type StoreConfig = { kind: "memory" } | { kind: "s3"; bucket: string; region: string };

export function createBlobStore(config: StoreConfig): BlobStore {
  switch (config.kind) {
    case "memory":
      return memoryStore();
    case "s3":
      return s3Store(config.bucket, config.region);
  }
}

function memoryStore(): BlobStore {
  const data = new Map<string, Uint8Array>();
  return {
    async put(key, body) { data.set(key, body); },
    async get(key) { return data.get(key); },
  };
}
```

**Avoid:** an abstract `StoreFactory` class with a subclass per backend. The function
is the factory.

### Abstract Factory

**Idiomatic form:** one object whose properties are constructor functions for a whole
family, chosen once.

```ts
interface Queue { publish(topic: string, message: string): Promise<void> }
interface Store { put(key: string, body: Uint8Array): Promise<void> }

// Chosen once at startup, so a queue and a store from different clouds can't mix.
interface CloudKit {
  queue(name: string): Queue;
  store(bucket: string): Store;
}

const localKit: CloudKit = {
  queue: () => ({ publish: async (topic, message) => console.log(topic, message) }),
  store: () => {
    const data = new Map<string, Uint8Array>();
    return { put: async (key, body) => void data.set(key, body) };
  },
};

declare const gcpKit: CloudKit; // defined in gcp.ts

export const kitFor = (env: "local" | "gcp"): CloudKit => (env === "local" ? localKit : gcpKit);
```

**Avoid:** abstract factory and abstract product class hierarchies. With one family in
use, skip the pattern and call the constructors directly.

### Builder

**Idiomatic form:** an options object with defaults, validated once. Keep a fluent
builder for construction that really happens in stages, like a query built across
several functions.

```ts
interface ClientOptions {
  baseUrl: string;
  timeoutMs?: number;
  retries?: number;
  headers?: Record<string, string>;
}

export function createClient({
  baseUrl,
  timeoutMs = 5_000,
  retries = 2,
  headers = {},
}: ClientOptions) {
  if (retries < 0) throw new RangeError("retries must be >= 0");
  return {
    retries,
    get: (path: string) =>
      fetch(new URL(path, baseUrl), { headers, signal: AbortSignal.timeout(timeoutMs) }),
  };
}

const client = createClient({ baseUrl: "https://api.example.com", retries: 5 });
```

**Avoid:** `new ClientBuilder().setBaseUrl(...).setTimeout(...).build()` with one
setter per field. That is Java's workaround for having no named arguments.

**Gotcha:** destructuring defaults apply to `undefined`, but `{ ...defaults, ...options }`
copies an explicit `undefined` over the default. Prefer destructuring defaults, or
turn on `exactOptionalPropertyTypes`.

### Prototype

**Idiomatic form:** copy a plain object with spread, or with `structuredClone` when
the nested data must not be shared.

```ts
interface Invoice {
  customer: string;
  currency: string;
  lines: { sku: string; qty: number }[];
  issuedAt: Date;
}

const template: Invoice = { customer: "", currency: "EUR", lines: [], issuedAt: new Date(0) };

// Spread is shallow: without the second copy, `lines` would be shared with the template.
const draft: Invoice = { ...template, customer: "acme", lines: [...template.lines] };

// A full deep copy, including the Date.
const archived = structuredClone(draft);
```

**Avoid:** a `Cloneable` interface and a hand-written `clone()` on every class.

**Gotcha:** `structuredClone` throws on functions and returns plain objects for class
instances, so methods and `instanceof` are lost. Keep cloned data as plain data.

### Singleton

**Idiomatic form:** build the instance once in the entry file and pass it in. When lazy
creation is truly needed, memoize the promise in a module.

```ts
interface Db { query(sql: string): Promise<unknown[]> }

let db: Promise<Db> | undefined;

// Storing the promise, not the result, means two concurrent first callers
// share one connection instead of racing to open two.
export function getDb(): Promise<Db> {
  db ??= connect(process.env.DATABASE_URL ?? "postgres://localhost/app");
  return db;
}
```

**Avoid:** `private constructor()` plus `static getInstance()`. The module already
runs once, and the static accessor hides the dependency from every caller.

**Gotcha:** module identity is per bundle and per copy of the package, not per
process (see above). Dev servers with hot reload re-run the module, which is why
Next.js apps often keep a database client on `globalThis` in development. A failed connection is
also cached forever here; reset `db` in a `.catch` if a retry should reconnect.

## Structural

### Adapter

**Idiomatic form:** a function that takes the foreign client and returns an object
shaped like the interface you own.

```ts
interface PaymentGateway {
  charge(input: { amountCents: number; currency: string; token: string }):
    Promise<{ id: string; ok: boolean }>;
}

// The vendor's shape, which we don't control.
interface VendorClient {
  paymentIntents: {
    create(p: { amount: number; currency: string; payment_method: string; confirm: true }):
      Promise<{ id: string; status: "succeeded" | "requires_action" | "canceled" }>;
  };
}

export function vendorGateway(client: VendorClient): PaymentGateway {
  return {
    async charge({ amountCents, currency, token }) {
      const intent = await client.paymentIntents.create({
        amount: amountCents, currency, payment_method: token, confirm: true,
      });
      return { id: intent.id, ok: intent.status === "succeeded" };
    },
  };
}
```

**Avoid:** `class Gateway extends VendorClient`. Inheriting leaks every vendor method
to your callers, which is the coupling the adapter exists to stop.

**Gotcha:** keep vendor types out of the adapter's return values, or the vendor leaks
through anyway.

### Bridge

**Idiomatic form:** take the second dimension as an interface-typed parameter, so the
two dimensions combine instead of multiplying.

```ts
interface Channel { deliver(to: string, text: string): Promise<void> }

function createAlerts(channel: Channel) {
  return {
    outage: (team: string, service: string) =>
      channel.deliver(team, `[OUTAGE] ${service} is down`),
    recovered: (team: string, service: string) =>
      channel.deliver(team, `${service} recovered`),
  };
}

const email: Channel = { deliver: (to, text) => sendEmail(to, text) };
const slack: Channel = { deliver: (to, text) => postToSlack(`#${to}`, text) };

// Two kinds of alert times two channels, with no class per combination.
const pager = createAlerts(slack);
```

**Avoid:** `EmailOutageAlert`, `SlackOutageAlert`, `EmailRecoveryAlert`, and so on.

### Composite

**Idiomatic form:** a recursive discriminated union and one function that walks it.

```ts
type FileNode =
  | { kind: "file"; name: string; bytes: number }
  | { kind: "dir"; name: string; children: FileNode[] };

function size(node: FileNode): number {
  switch (node.kind) {
    case "file":
      return node.bytes;
    case "dir":
      return node.children.reduce((sum, child) => sum + size(child), 0);
  }
}
```

When other packages add node types, use an interface with the shared method instead
of a closed union.

**Avoid:** an abstract `Component` class whose `add()` and `remove()` throw on leaves.
That breaks Liskov for every leaf.

### Decorator

**Idiomatic form:** a higher-order function that wraps a function and returns the
same type. Wrapping `fetch` is the everyday case.

```ts
type Fetch = typeof fetch;

function withRetry(inner: Fetch, attempts = 3): Fetch {
  return async (input, init) => {
    for (let i = 1; ; i++) {
      try {
        const res = await inner(input, init);
        if (res.status < 500 || i >= attempts) return res;
      } catch (err) {
        if (i >= attempts) throw err;
      }
    }
  };
}

function withTiming(inner: Fetch): Fetch {
  return async (input, init) => {
    const started = performance.now();
    const res = await inner(input, init);
    console.log(res.url, res.status, `${Math.round(performance.now() - started)}ms`);
    return res;
  };
}

const http = withTiming(withRetry(fetch)); // one log line per call, not per attempt
```

TypeScript's `@decorator` syntax (TC39 stage 3, TS 5.0+ without
`experimentalDecorators`) applies the same idea to class methods, but at class
definition time and for every instance. The pattern wraps chosen objects at runtime.
The legacy `experimentalDecorators` API is a different, incompatible one.

**Avoid:** `class RetryingHttpClient extends HttpClient`, then `LoggingRetryingHttpClient`.

**Gotcha:** wrapper order changes behavior; above, timing outside retry logs once.
Retry only idempotent requests, and note that a `Request` body can only be read once.

### Facade

**Idiomatic form:** a module that exports one or two task-shaped functions and keeps the
subsystem unexported. In a package, that is `index.ts` plus a `package.json`
`"exports"` map that blocks deep imports.

```ts
// billing/index.ts: the only file other packages import.
// Callers want "send the invoice", not PDF rendering, storage and email, in that
// order, with those retries.
export async function sendInvoice(invoiceId: string): Promise<void> {
  const invoice = await invoices.load(invoiceId);
  const pdf = await renderPdf(invoice);
  const url = await storage.upload(`invoices/${invoiceId}.pdf`, pdf);
  await mailer.send(invoice.customerEmail, "Your invoice", url);
}
```

**Avoid:** a `BillingFacade` class of static methods, or a barrel that does
`export * from` every internal file. That is the whole subsystem with a new name.

**Gotcha:** big `export *` barrels also slow down bundlers and test startup, and make
circular imports easy.

### Flyweight

**Idiomatic form:** intern the shared, immutable part in a `Map` and hand out the same
frozen object; keep the per-use part outside it.

```ts
interface Glyph { readonly char: string; readonly font: string; readonly width: number }

const glyphs = new Map<string, Glyph>();

function glyph(char: string, font: string): Glyph {
  const key = `${font}\u0000${char}`;
  let g = glyphs.get(key);
  if (!g) {
    g = Object.freeze({ char, font, width: measure(char, font) });
    glyphs.set(key, g);
  }
  return g;
}

// A million placed characters share a few hundred Glyph objects.
type PlacedGlyph = { glyph: Glyph; x: number; y: number };
```

**Avoid:** applying it without a heap snapshot that shows the duplicates.

**Gotcha:** this `Map` never shrinks. For keys that keep growing, use a bounded LRU
or a `WeakRef` cache.

### Proxy

**Idiomatic form:** an object with the same interface as the real one that adds lazy
loading, caching or access checks.

```ts
type Report = { id: string; body: string };
interface ReportStore { get(id: string): Promise<Report> }

function cachingStore(inner: ReportStore, ttlMs: number): ReportStore {
  const cache = new Map<string, { value: Promise<Report>; expires: number }>();
  return {
    get(id) {
      const hit = cache.get(id);
      if (hit && hit.expires > Date.now()) return hit.value;
      // Caching the promise means concurrent callers share one request.
      const value = inner.get(id);
      value.catch(() => {
        if (cache.get(id)?.value === value) cache.delete(id); // don't cache failures
      });
      cache.set(id, { value, expires: Date.now() + ttlMs });
      return value;
    },
  };
}
```

**Avoid:** the built-in `Proxy` object when the interface is known. It hides behavior
from readers and from the type checker. Keep it for cases where the property names are
not known ahead of time: ORMs, reactive state, test spies.

**Gotcha:** a built-in `Proxy` breaks objects with internal slots or `#private`
fields. `new Proxy(new Map(), {}).get("k")` throws a `TypeError` because `this` is
the proxy, not the `Map`.

## Behavioral

### Chain of Responsibility

**Idiomatic form:** an array of middleware functions, each calling `next()` or
stopping, as in Koa or Express.

```ts
type Ctx = { req: Request; user?: { id: string }; res?: Response };
type Middleware = (ctx: Ctx, next: () => Promise<void>) => Promise<void>;

function compose(stack: Middleware[]): (ctx: Ctx) => Promise<void> {
  const run = (ctx: Ctx, i: number): Promise<void> =>
    i < stack.length ? stack[i](ctx, () => run(ctx, i + 1)) : Promise.resolve();
  return (ctx) => run(ctx, 0);
}

const requireAuth: Middleware = async (ctx, next) => {
  const token = ctx.req.headers.get("authorization");
  if (!token) {
    ctx.res = new Response("unauthorized", { status: 401 });
    return; // stop the chain
  }
  ctx.user = { id: await verify(token) };
  await next();
};

const handle = compose([requireAuth, rateLimit, route]);
```

**Avoid:** an abstract `Handler` class with `setNext()` building a linked list.

**Gotcha:** a middleware that calls `next()` without `await` lets the response go out
before later handlers finish. Calling `next()` twice runs the rest of the chain twice.

### Command

**Idiomatic form:** a closure for fire-and-forget actions. When commands must be
queued, logged, sent over `postMessage`, stored or undone, make them plain data: a
discriminated union.

```ts
interface Doc {
  rename(id: string, name: string): void;
  move(id: string, folder: string): void;
}

type Command =
  | { type: "rename"; id: string; from: string; to: string }
  | { type: "move"; id: string; from: string; to: string };

function apply(doc: Doc, cmd: Command): void {
  if (cmd.type === "rename") doc.rename(cmd.id, cmd.to);
  else doc.move(cmd.id, cmd.to);
}

const invert = (cmd: Command): Command => ({ ...cmd, from: cmd.to, to: cmd.from });

const history: Command[] = [];
export function run(doc: Doc, cmd: Command) {
  apply(doc, cmd);
  history.push(cmd);
}
export function undo(doc: Doc) {
  const last = history.pop();
  if (last) apply(doc, invert(last));
}
```

**Avoid:** an `interface Command { execute(): void }` and a class per action when
`() => void` is enough. Closures cannot be serialized; data commands can.

### Interpreter

**Idiomatic form:** a discriminated-union AST evaluated by one recursive `switch`.
Beyond a toy grammar, use an existing parser or expression library.

```ts
type Expr =
  | { op: "num"; value: number }
  | { op: "var"; name: string }
  | { op: "add" | "mul"; left: Expr; right: Expr };

function evaluate(e: Expr, vars: Record<string, number>): number {
  switch (e.op) {
    case "num":
      return e.value;
    case "var": {
      const v = vars[e.name];
      if (v === undefined) throw new Error(`unknown variable ${e.name}`);
      return v;
    }
    case "add":
      return evaluate(e.left, vars) + evaluate(e.right, vars);
    case "mul":
      return evaluate(e.left, vars) * evaluate(e.right, vars);
  }
}
```

**Avoid:** a class per grammar rule with an `interpret(context)` method.

**Gotcha:** never reach for `eval` or `new Function` on user input as a shortcut.

### Iterator

**Idiomatic form:** a generator function, `*[Symbol.iterator]()` on a class, or an
async generator for paged APIs.

```ts
interface User { id: string; disabled: boolean }

async function* listAll<T>(url: string): AsyncGenerator<T> {
  let next: string | null = url;
  while (next) {
    const res = await fetch(next);
    const page = (await res.json()) as { items: T[]; next: string | null };
    yield* page.items;
    next = page.next;
  }
}

export async function firstDisabled(): Promise<User | undefined> {
  for await (const user of listAll<User>("https://api.example.com/users")) {
    if (user.disabled) return user; // stops early: no more pages are fetched
  }
  return undefined;
}
```

**Avoid:** Java-style iterator classes with `hasNext()` and `next()`.

**Gotcha:** generators are lazy and single-use. Leaving a `for...of` early calls the
generator's `return()`, so cleanup belongs in a `finally` inside it.

### Mediator

**Idiomatic form:** one coordinator that owns how components affect each other. The
components only report to it.

```ts
interface CheckoutUi {
  showShipping(options: string[]): void;
  showTotal(cents: number): void;
}

// Widgets never call each other; they report to the checkout, which decides.
export function createCheckout(ui: CheckoutUi) {
  const state = { country: "KE", coupon: "" };
  const refresh = () => {
    ui.showShipping(shippingOptions(state.country));
    ui.showTotal(totalFor(state.country, state.coupon));
  };
  return {
    countryChanged(country: string) { state.country = country; refresh(); },
    couponApplied(code: string) { state.coupon = code; refresh(); },
  };
}
```

**Avoid:** a generic `Mediator` base class with a stringly typed
`notify(sender, event: string)`.

**Gotcha:** a mediator grows into a god object. Keep one per workflow, not one per app.

### Memento

**Idiomatic form:** immutable state snapshots. When state is never mutated in place,
the previous value *is* the memento.

```ts
type EditorState = Readonly<{ text: string; cursor: number }>;

export function createHistory(initial: EditorState, limit = 100) {
  const past: EditorState[] = [];
  let present = initial;
  return {
    get: () => present,
    set(next: EditorState) {
      past.push(present);
      if (past.length > limit) past.shift();
      present = next;
    },
    undo() {
      present = past.pop() ?? present;
    },
  };
}
```

**Avoid:** `Originator` and `Caretaker` classes with `createMemento()` and
`restore()`.

**Gotcha:** `Readonly` is shallow. A nested array mutated in place changes every
snapshot that shares it. Use `readonly` arrays all the way down, or clone on write.

### Observer

**Idiomatic form:** `EventTarget` for DOM and platform events, or a small typed emitter
whose `subscribe` returns its own unsubscribe function. Where a framework has
signals, use them.

```ts
export function createEmitter<T>() {
  const listeners = new Set<(value: T) => void>();
  return {
    subscribe(fn: (value: T) => void): () => void {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
    emit(value: T) {
      for (const fn of [...listeners]) fn(value); // copy: add/remove during emit is safe
    },
  };
}

const orderShipped = createEmitter<{ orderId: string }>();
const stop = orderShipped.subscribe(({ orderId }) => notifyCustomer(orderId));
stop(); // when the owner goes away

// Platform events: one AbortController removes a whole group of listeners.
const controller = new AbortController();
window.addEventListener("resize", onResize, { signal: controller.signal });
socket.addEventListener("message", onMessage, { signal: controller.signal });
controller.abort();
```

**Avoid:** `Subject` and `Observer` interfaces with `attach`, `detach` and `update`
classes.

**Gotcha:** the leak. Every `subscribe` or `addEventListener` needs a matching removal
tied to the owner's lifetime. In this naive `emit`, one throwing listener also stops
the rest; a browser `EventTarget` reports the error and still calls the others.

### State

**Idiomatic form:** a discriminated union of states and a pure `(state, event) => state`
reducer. Impossible combinations, like `done` with an `error`, cannot be written.

```ts
type Upload =
  | { status: "idle" }
  | { status: "uploading"; progress: number }
  | { status: "done"; url: string }
  | { status: "failed"; error: string };

type UploadEvent =
  | { type: "start" }
  | { type: "progress"; progress: number }
  | { type: "finish"; url: string }
  | { type: "fail"; error: string };

export function next(s: Upload, e: UploadEvent): Upload {
  switch (s.status) {
    case "idle":
    case "failed":
      return e.type === "start" ? { status: "uploading", progress: 0 } : s;
    case "uploading":
      if (e.type === "progress") return { ...s, progress: e.progress };
      if (e.type === "finish") return { status: "done", url: e.url };
      if (e.type === "fail") return { status: "failed", error: e.error };
      return s;
    case "done":
      return s;
  }
}
```

**Avoid:** separate flags and optional fields (`isLoading`, `isError`, `data?`) that
allow eight combinations for four real states. Also avoid a class per state when the states carry
no behavior of their own. For nested or parallel states, use a statechart library
such as XState.

### Strategy

**Idiomatic form:** pass a function. When the choice comes from config, keep a typed
map of them.

```ts
type Cart = { subtotal: number; items: number };
type Pricer = (cart: Cart) => number;

const standard: Pricer = (cart) => cart.subtotal;
const blackFriday: Pricer = (cart) => Math.round(cart.subtotal * 0.8);
const bulk: Pricer = (cart) => (cart.items >= 10 ? cart.subtotal - 500 : cart.subtotal);

export function checkout(cart: Cart, price: Pricer = standard) {
  return { ...cart, total: price(cart) };
}

// satisfies checks every entry but keeps the literal keys for PricingPlan.
const pricers = { standard, blackFriday, bulk } satisfies Record<string, Pricer>;
export type PricingPlan = keyof typeof pricers;
```

**Avoid:** a `PricingStrategy` interface, a class per strategy and a context class
with `setStrategy()`. When a strategy needs several related methods, an object literal
that satisfies an interface is still enough.

### Template Method

**Idiomatic form:** a function that owns the fixed steps and takes the varying steps as
an argument.

```ts
interface ImportSteps<Row> {
  parse(line: string): Row;
  validate(row: Row): string | null; // an error message, or null when valid
  save(rows: Row[]): Promise<void>;
}

// The skeleton is fixed; each format supplies only the steps that vary.
export async function runImport<Row>(lines: string[], steps: ImportSteps<Row>) {
  const rows: Row[] = [];
  const errors: string[] = [];
  lines.forEach((line, i) => {
    const row = steps.parse(line);
    const problem = steps.validate(row);
    if (problem) errors.push(`line ${i + 1}: ${problem}`);
    else rows.push(row);
  });
  if (errors.length === 0) await steps.save(rows);
  return { imported: errors.length === 0 ? rows.length : 0, errors };
}
```

**Avoid:** `abstract class Importer` with `protected abstract parse()` and a subclass
per format. Reading one import then means reading two classes, and the hooks multiply.

### Visitor

**Idiomatic form:** a discriminated union and a `switch` with an `assertNever` default.
Each new operation is just another function.

```ts
type Shape =
  | { kind: "circle"; r: number }
  | { kind: "rect"; w: number; h: number }
  | { kind: "triangle"; base: number; height: number };

function assertNever(x: never): never {
  throw new Error(`unhandled case: ${JSON.stringify(x)}`);
}

export function area(s: Shape): number {
  switch (s.kind) {
    case "circle":
      return Math.PI * s.r ** 2;
    case "rect":
      return s.w * s.h;
    case "triangle":
      return (s.base * s.height) / 2;
    default:
      return assertNever(s); // a new Shape kind breaks the build here
  }
}
```

To pass the handlers around as a value, like a real visitor object, type them with a
mapped type, `{ [K in Shape["kind"]]: (s: Extract<Shape, { kind: K }>) => R }`, which
the compiler also keeps exhaustive.

**Avoid:** `accept(visitor)` on every node class and a `ShapeVisitor` interface with
`visitCircle`, `visitRect` and so on. Keep that for class hierarchies you cannot turn
into a union.

**Gotcha:** the exhaustive check only works if every `switch` has it. The
typescript-eslint rule `switch-exhaustiveness-check` enforces it project-wide.

## Java in TypeScript: smells to catch in review

- **Classes with only static methods.** That is a module. Export functions.
- **`I`-prefixed interfaces** (`IUserService`) and an interface for every class.
  Structural typing makes the pairing unnecessary; declare the interface at the
  consumer when a second implementation or a fake appears.
- **An abstract base class per interface**, and inheritance used to share helpers.
  Compose functions instead.
- **Getters and setters that only read and write a field.** Use a plain property,
  `readonly` if it should not change. Add an accessor later without changing callers.
- **`private constructor()` plus `static getInstance()`.** A module export, or an
  argument, does the job.
- **Factory classes** (`UserFactory.create()`) where a function works.
- **A DI container with `reflect-metadata` decorators** for a handful of services.
  One composition file that calls constructors is easier to read and debug.
- **`instanceof` checks against class hierarchies** to pick behavior. Use a
  discriminant field and a `switch`, which the compiler checks.
- **Builders with a setter per field** where an options object would do.
- **`Subject`, `Visitor`, `Strategy` and `Command` interfaces with one method each.**
  A function type says the same thing in one line.
