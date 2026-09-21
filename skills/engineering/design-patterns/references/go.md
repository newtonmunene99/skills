# Go: idiomatic patterns

This file is the source of truth for what each pattern looks like in Go. The catalog
files ([creational.md](creational.md), [structural.md](structural.md),
[behavioral.md](behavioral.md)) cover when a pattern is worth it and what it costs.
Read one of those for the decision, then this file for the code. Examples target Go
1.23+ and omit the package clause and imports.

## Contents

- [What changes the catalog in Go](#what-changes-the-catalog-in-go)
- [SOLID in Go](#solid-in-go)
- [Creational](#creational)
- [Structural](#structural)
- [Behavioral](#behavioral)
- [Java in Go: smells to catch in review](#java-in-go-smells-to-catch-in-review)

## What changes the catalog in Go

- **Implicit interfaces.** A type satisfies an interface by having its methods; there
  is no `implements`. So the consumer declares the interface it needs, small and after
  the fact. Many Adapters disappear because the foreign type already fits the interface
  you declare, and Interface Segregation comes for free.
- **No inheritance, only embedding.** Embedding promotes the inner type's methods to
  the outer type. It is not subclassing and there is **no virtual dispatch**: when an
  embedded type's method calls another of its methods, it calls its own version, never
  the outer type's "override". This rules out the textbook Template Method and any
  "abstract base struct".
- **Functions are values, and function types can have methods.** `http.HandlerFunc`
  turns a plain function into an `http.Handler`. Strategy, Command, and single-method
  Adapters usually collapse into a function or a function type.
- **Closures.** A function literal captures state without a struct. Command,
  Decorator, Observer callbacks and simple Mementos often need nothing more.
- **Functional options.** A variadic `...Option` parameter, where `Option` is
  `func(*T)`, replaces Builder for constructors with many optional settings.
- **Generics.** Type-safe containers, event buses and helpers without `any` and type
  assertions. Do not use them to fake inheritance.
- **Range-over-func (1.23+).** `iter.Seq[V]` and `iter.Seq2[K, V]` make Iterator a
  function that callers consume with `for v := range seq`. `slices.Values`,
  `maps.Keys` and `ast.Preorder` already return them.
- **Goroutines and channels.** Observer, Mediator, pipelines and Command queues can be
  channel-based. That adds lifecycle questions every time: who closes the channel, who
  cancels, what happens when a reader is slow.
- **Packages are the unit of encapsulation.** Unexported names are hidden from other
  packages, and `internal/` directories are enforced by the compiler. A Facade is often
  just a package with a small exported API.
- **`sync.Once`, `sync.OnceValue`, `sync.OnceValues` (1.21+).** Safe lazy one-time
  initialization. They replace hand-rolled double-checked locking.
- **Useful zero values.** `var mu sync.Mutex` and `var buf bytes.Buffer` work with no
  constructor. Many "factories" exist only to initialize what a well-designed zero
  value gets right on its own.

## SOLID in Go

The examples are the running examples from [solid.md](solid.md), written in Go.

- **Single Responsibility.** `User` holds the data, `UserStore` persists it,
  `WelcomeNotifier` sends the email. Three actors ask for changes, so three types,
  usually in different packages. The same test applies to packages: `util` or
  `common` changes for as many reasons as it has callers.
- **Open/Closed.** A `ShippingCalculator` that switches over `Ground`, `Air` and `Sea`
  must be edited to add `Drone`. That is fine while carriers rarely change and the
  switch lives in one place. A `Carrier` interface, or a `map[string]RateFunc`, is
  earned only when carriers keep getting added or the same switch repeats elsewhere.
- **Liskov Substitution.** A `Bird` interface with `Fly()` forces `Penguin` to return
  an error or panic. Declare a narrower `Flier` interface and let only flying birds
  satisfy it. The compiler checks method sets, not contracts: an `io.Reader` must also
  return `n > 0` bytes alongside an error when it has them, and a typed nil pointer
  returned as an `error` makes `err != nil` true.
- **Interface Segregation.** `Worker` with `Work`, `Eat` and `Sleep` forces
  `RobotWorker` to stub out two methods. Split it into `Worker`, `Eater` and
  `Sleeper`, and let each consumer declare the one it uses. No `I` prefix.
- **Dependency Inversion.** A `Store.Checkout` that builds a Stripe client ties
  checkout to one vendor. The store package declares `PaymentProcessor` in its own
  terms, and `main` injects a Stripe or PayPal adapter. Accept interfaces, return
  concrete types.

```go
// ISP: one small interface per capability.
type Worker interface{ Work() error }
type Eater interface{ Eat() }
type Sleeper interface{ Sleep() }

// DIP: package store owns this interface, in its own terms.
// main injects a Stripe or PayPal adapter that satisfies it.
type PaymentProcessor interface {
	Charge(ctx context.Context, amountCents int64, source string) (chargeID string, err error)
}

type Store struct {
	payments PaymentProcessor
}

func NewStore(p PaymentProcessor) *Store { return &Store{payments: p} }

func (s *Store) Checkout(ctx context.Context, cart Cart) error {
	_, err := s.payments.Charge(ctx, cart.TotalCents, cart.PaymentSource)
	return err
}
```

## Creational

### Factory Method

**Idiomatic form:** a `NewX` constructor function. It returns a concrete type, unless
the implementation is chosen at runtime, in which case it returns an interface.

```go
type Notifier interface {
	Notify(ctx context.Context, userID, msg string) error
}

// NewNotifier is the one place that knows the concrete types.
func NewNotifier(cfg Config) (Notifier, error) {
	switch cfg.Channel {
	case "email":
		return &EmailNotifier{from: cfg.From}, nil
	case "sms":
		return &SMSNotifier{apiKey: cfg.SMSKey}, nil
	default:
		return nil, fmt.Errorf("unknown notification channel %q", cfg.Channel)
	}
}
```

**Avoid:** a `NotifierFactory` interface with a `Create()` method and one factory type
per product. Also avoid returning an interface when there is only one implementation:
it hides the type's other methods and forces callers into type assertions.

**Gotcha:** return a literal `nil` on the error path. A nil `*EmailNotifier` stored in
a `Notifier` is a non-nil interface, and the caller's `n != nil` check passes.

### Abstract Factory

**Idiomatic form:** build the family once, at startup, as a struct of interfaces.
One constructor per family keeps the members matched.

```go
// Storage groups clients that must come from the same backend.
// Mixing a GCS blob store with an in-memory queue is the bug this prevents.
type Storage struct {
	Blobs  BlobStore
	Queue  Queue
	Locker Locker
}

// NewMemoryStorage is the test family. NewGCPStorage builds the real one
// the same way.
func NewMemoryStorage() *Storage {
	return &Storage{
		Blobs:  newMemBlobs(),
		Queue:  newMemQueue(),
		Locker: newMemLocker(),
	}
}
```

**Avoid:** a `StorageFactory` interface with `CreateBlobStore()`, `CreateQueue()` and
parallel families of factory types. Go code rarely needs to create family members
lazily and repeatedly, which is the only thing that design adds.

### Builder

**Idiomatic form:** functional options for optional settings, with required values as
plain parameters. A `Config` struct is just as good, and often more discoverable, when
every field is plain data.

```go
type Server struct {
	addr    string
	timeout time.Duration
	logger  *slog.Logger
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }

func WithLogger(l *slog.Logger) Option { return func(s *Server) { s.logger = l } }

func NewServer(addr string, opts ...Option) *Server {
	s := &Server{addr: addr, timeout: 30 * time.Second, logger: slog.Default()}
	for _, opt := range opts {
		opt(s)
	}
	return s
}

// srv := NewServer(":8080", WithTimeout(5*time.Second))
```

**Avoid:** `NewServerBuilder().SetAddr(a).SetTimeout(t).Build()`, a second type that
mirrors every field as a setter.

**Gotcha:** if an option can be invalid, make it `func(*Server) error` and return the
first error from the constructor, rather than panicking or silently ignoring it.

### Prototype

**Idiomatic form:** assignment copies a struct. For structs holding slices, maps or
pointers, add a `Clone` method that copies whatever must not be shared.

```go
type Template struct {
	Name    string
	Headers map[string]string
	Tags    []string
}

// Clone returns a copy that shares no mutable state with t.
func (t Template) Clone() Template {
	c := t // Name is copied; Headers and Tags still point at t's data
	c.Headers = maps.Clone(t.Headers)
	c.Tags = slices.Clone(t.Tags)
	return c
}
```

**Avoid:** a `Prototype` interface with `Clone() Prototype` and type assertions on the
result.

**Gotcha:** `slices.Clone` and `maps.Clone` are shallow. Elements that are themselves
pointers, slices or maps stay shared. Copying a struct that contains a `sync.Mutex` is
a bug; `go vet`'s copylocks check catches it.

### Singleton

**Idiomatic form:** do not make one. Build the shared resource once where the program
starts and pass it to whatever needs it. For a lazily built, immutable process-wide
value, use a package-level variable or `sync.OnceValue(s)`.

```go
// Preferred: one instance, created at startup and passed down.
// Tests build their own and never touch a global.
func run(ctx context.Context, dsn string) error {
	db, err := sql.Open("pgx", dsn)
	if err != nil {
		return err
	}
	defer db.Close()
	return NewOrderService(db).Serve(ctx)
}

// When lazy, process-wide init is truly needed, e.g. an immutable table:
var loadRates = sync.OnceValues(func() (map[string]float64, error) {
	return parseRates(embeddedRates)
})
```

**Avoid:** `var instance *DB` set in `init()` behind a `GetInstance()` function, and
hand-rolled double-checked locking with a mutex and a nil check.

**Gotcha:** `OnceValue` and `OnceValues` cache the result forever, errors included, so a
failed load is never retried. If the function panics, every later call panics with the
same value. Use a mutex if a failed init must be retried.

## Structural

### Adapter

**Idiomatic form:** often nothing. Declare the interface you need and check whether the
foreign type already satisfies it. Otherwise, a small wrapper struct, or a function
type with a method to adapt plain functions.

```go
// Publisher is what the domain code needs.
type Publisher interface {
	Publish(ctx context.Context, topic string, data []byte) error
}

// sdkPublisher is the only code that knows the vendor's types.
type sdkPublisher struct {
	client *vendorsdk.Client
}

func (p sdkPublisher) Publish(ctx context.Context, topic string, data []byte) error {
	_, err := p.client.Send(ctx, &vendorsdk.Message{Topic: topic, Body: data})
	return err
}

// PublisherFunc adapts a plain function, the same trick as http.HandlerFunc.
type PublisherFunc func(ctx context.Context, topic string, data []byte) error

func (f PublisherFunc) Publish(ctx context.Context, topic string, data []byte) error {
	return f(ctx, topic, data)
}
```

**Avoid:** an adapter for a type that already satisfies the interface, and an interface
that mirrors the whole vendor API. Include only the methods you call.

### Bridge

**Idiomatic form:** a struct with an interface-typed field for the dimension that varies
on its own. This is ordinary composition, and Go code gets it without naming it.

```go
// Two dimensions: what a report contains, and where it is delivered.
type Sink interface {
	Write(ctx context.Context, name string, body []byte) error
}

type SalesReport struct {
	sink Sink // S3, local disk or email, chosen independently of the report
}

func (r SalesReport) Publish(ctx context.Context, rows []Sale) error {
	body, err := renderCSV(rows)
	if err != nil {
		return err
	}
	return r.sink.Write(ctx, "sales.csv", body)
}
```

**Avoid:** an abstraction hierarchy (`Report`, `SalesReport`, `InventoryReport`)
crossed with an implementor hierarchy. The class explosion Bridge prevents cannot
happen without inheritance, so there is nothing to bridge.

### Composite

**Idiomatic form:** an interface with one method, implemented by both single items and
a group type that holds a slice of the interface. The standard library does this with
`io.MultiReader`, `io.MultiWriter` and `errors.Join`.

```go
type Rule interface {
	Check(o Order) error
}

// AllOf is a Rule made of Rules; callers cannot tell it from a single one.
type AllOf []Rule

func (rs AllOf) Check(o Order) error {
	var errs []error
	for _, r := range rs {
		if err := r.Check(o); err != nil {
			errs = append(errs, err)
		}
	}
	return errors.Join(errs...) // nil when every rule passed
}

type MaxTotal int64

func (m MaxTotal) Check(o Order) error {
	if o.TotalCents > int64(m) {
		return fmt.Errorf("total %d exceeds limit %d", o.TotalCents, m)
	}
	return nil
}

// rules := AllOf{MaxTotal(500_00), AllOf{requireAddress, requireEmail}}
```

**Avoid:** `Add`, `Remove` and `Child` methods on the shared interface, the GoF
"transparent" composite. Every leaf then carries methods that can only panic. Keep
child management on the group type.

### Decorator

**Idiomatic form:** middleware. A function takes an interface (or a function) and
returns the same interface with behavior wrapped around it. `func(http.Handler)
http.Handler` is the canonical shape.

```go
func Logging(logger *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
			next.ServeHTTP(rec, r)
			logger.Info("request", "path", r.URL.Path, "status", rec.status, "took", time.Since(start))
		})
	}
}

type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (r *statusRecorder) WriteHeader(code int) {
	r.status = code
	r.ResponseWriter.WriteHeader(code)
}

// Unwrap lets http.ResponseController reach Flush and Hijack on the original.
func (r *statusRecorder) Unwrap() http.ResponseWriter { return r.ResponseWriter }
```

**Avoid:** a decorator base type plus one subtype per decoration.

**Gotcha:** embedding an interface promotes only that interface's methods. The wrapper
hides optional interfaces the original had, such as `http.Flusher` and
`http.Hijacker`, so a downstream `w.(http.Flusher)` fails and streaming silently stops.
Add `Unwrap` and have handlers use `http.NewResponseController(w).Flush()`. The same
trap hides `io.WriterTo` and `io.ReaderFrom` behind `io.Reader` wrappers.

### Facade

**Idiomatic form:** a package with a small exported API, with the subsystems unexported
or under `internal/`. Often one struct with a few methods.

```go
// Service is the checkout facade: one call for callers, while tax, stock
// and payments stay unexported.
type Service struct {
	tax      taxCalculator
	stock    stockReserver
	payments paymentGateway
}

func (s *Service) PlaceOrder(ctx context.Context, cart Cart) (OrderID, error) {
	total := s.tax.Apply(cart.Subtotal(), cart.ShipTo)
	hold, err := s.stock.Reserve(ctx, cart.Items)
	if err != nil {
		return "", fmt.Errorf("reserve stock: %w", err)
	}
	id, err := s.payments.Charge(ctx, cart.CustomerID, total)
	if err != nil {
		hold.Release(ctx)
		return "", fmt.Errorf("charge: %w", err)
	}
	hold.Commit(ctx)
	return id, nil
}
```

**Avoid:** a facade that re-exports every subsystem method one to one. That is a
pass-through layer, not a simplification.

**Gotcha:** put the subsystems under `internal/` if callers must not bypass the facade.
The compiler enforces it; a comment does not.

### Flyweight

**Idiomatic form:** intern repeated immutable values with `unique.Make` (Go 1.23+).
Each distinct value is stored once, and a `unique.Handle` is one pointer that compares
in constant time.

```go
// Millions of log records share a few hundred distinct host names.
type Record struct {
	Host unique.Handle[string] // one pointer; == is a pointer compare
	Msg  string
}

func parse(line []byte) Record {
	host, msg, _ := bytes.Cut(line, []byte(" "))
	return Record{
		Host: unique.Make(string(host)),
		Msg:  string(msg),
	}
}

// r.Host.Value() returns the string when you need it.
```

**Avoid:** a hand-rolled global `map[string]*T` behind a mutex. It serializes callers
and grows forever unless you add eviction.

**Gotcha:** only worth it when a heap profile shows the duplication. Every `Make` is a
lookup, so interning values that are rarely repeated costs more than it saves.

### Proxy

**Idiomatic form:** a struct that implements the same interface as the real thing and
controls access to it: lazy setup, caching, auth, rate limiting, or a remote call.

```go
type PriceSource interface {
	Price(ctx context.Context, sku string) (int64, error)
}

// cachedPrices is a caching proxy in front of a slow PriceSource.
type cachedPrices struct {
	next PriceSource
	mu   sync.Mutex
	seen map[string]int64
}

func (c *cachedPrices) Price(ctx context.Context, sku string) (int64, error) {
	c.mu.Lock()
	p, ok := c.seen[sku]
	c.mu.Unlock()
	if ok {
		return p, nil
	}
	p, err := c.next.Price(ctx, sku)
	if err != nil {
		return 0, err
	}
	c.mu.Lock()
	c.seen[sku] = p
	c.mu.Unlock()
	return p, nil
}
```

**Avoid:** `Subject` and `RealSubject` naming, and a proxy that changes the method set.
A wrapper that changes the interface is an Adapter.

**Gotcha:** this cache never expires, so it grows without bound and serves stale prices.
Concurrent misses for the same key all hit the slow source at once; use
`golang.org/x/sync/singleflight` to collapse them.

## Behavioral

### Chain of Responsibility

**Idiomatic form:** a slice of middleware composed into one handler. Each link can
handle the request, pass it on, or stop the chain.

```go
type Middleware func(http.Handler) http.Handler

// Chain applies middleware so the first in the list runs first.
func Chain(h http.Handler, mws ...Middleware) http.Handler {
	for i := len(mws) - 1; i >= 0; i-- {
		h = mws[i](h)
	}
	return h
}

func RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return // stop the chain
		}
		next.ServeHTTP(w, r)
	})
}

// h := Chain(api, Recover, RequestID, RequireAuth)
```

**Avoid:** handler structs wired into a linked list with `SetNext(h Handler)`.

**Gotcha:** order is easy to get backwards. Recovery and logging belong outermost so
they see everything, including requests that auth rejects. Test the order.

### Command

**Idiomatic form:** a closure for queues, retries and deferred work. A struct with `Do`
and `Undo` only when undo, logging or sending the command elsewhere needs its data.

```go
// For a job queue, a command is just a function.
type Job func(ctx context.Context) error

// For undo, a command has to remember what it changed.
type Command interface {
	Do(doc *Document) error
	Undo(doc *Document)
}

type InsertText struct {
	At   int
	Text string
}

func (c InsertText) Do(doc *Document) error {
	return doc.Insert(c.At, c.Text)
}

func (c InsertText) Undo(doc *Document) {
	doc.Delete(c.At, len(c.Text))
}
```

**Avoid:** `Invoker`, `Receiver` and `ConcreteCommand` types around what is one function
call.

**Gotcha:** a closure cannot be persisted or sent over the network. Commands that must
survive a restart or cross a process boundary need to be data.

### Interpreter

**Idiomatic form:** rarely hand-built. For real grammars use `text/template`,
`go/parser`, or an expression library such as CEL or expr. For a tiny rule language, an
AST of small types, each with an `Eval` method.

```go
type Expr interface {
	Eval(vars map[string]float64) float64
}

type Num float64
type Var string
type Add struct{ L, R Expr }
type Mul struct{ L, R Expr }

func (n Num) Eval(map[string]float64) float64   { return float64(n) }
func (v Var) Eval(m map[string]float64) float64 { return m[string(v)] }
func (a Add) Eval(m map[string]float64) float64 { return a.L.Eval(m) + a.R.Eval(m) }
func (x Mul) Eval(m map[string]float64) float64 { return x.L.Eval(m) * x.R.Eval(m) }

// price * (1 + tax)
// e := Mul{Var("price"), Add{Num(1), Var("tax")}}
```

**Avoid:** a parser and interpreter for what is really five fixed rules. A map of
functions is enough.

**Gotcha:** the evaluator is the easy part. Parsing, error messages with positions, and
limits on depth and run time for untrusted input are most of the work, which is why a
library usually wins.

### Iterator

**Idiomatic form:** return an `iter.Seq[T]` (or `iter.Seq2[K, V]`) and let callers use
`for v := range seq`. It hides the storage layout and supports early exit.

```go
// Pending walks the queue without exposing its ring-buffer layout.
func (q *Queue) Pending() iter.Seq[Task] {
	return func(yield func(Task) bool) {
		for i := range q.n {
			if !yield(q.buf[(q.head+i)%len(q.buf)]) {
				return // the caller broke out of the loop
			}
		}
	}
}

// for t := range q.Pending() {
// 	if t.Urgent {
// 		handle(t)
// 		break
// 	}
// }
```

**Avoid:** Java-style `HasNext()` and `Next()` iterator structs for in-memory
collections. Also avoid channels as iterators: when the caller breaks early, the
producing goroutine blocks forever and leaks.

**Gotcha:** always check what `yield` returns. Calling `yield` again after it returned
`false` panics at run time. Put cleanup in a `defer` inside the iterator function; it
runs when the caller's loop ends, including on `break`. For iteration that can fail,
yield `iter.Seq2[T, error]`, or keep the `bufio.Scanner` shape of `Next`, `Value` and
`Err`.

### Mediator

**Idiomatic form:** one coordinator that owns the interactions, often a single goroutine
looping over channels. Components talk to the coordinator, never to each other.

```go
// Room owns all member-to-member traffic; members never hold each other.
type Room struct {
	join  chan *Member
	leave chan *Member
	say   chan Message
}

func (r *Room) Run(ctx context.Context) {
	members := map[*Member]bool{}
	for {
		select {
		case m := <-r.join:
			members[m] = true
		case m := <-r.leave:
			delete(members, m)
		case msg := <-r.say:
			for m := range members {
				if m != msg.From {
					m.Deliver(msg) // must not block, or the whole room stalls
				}
			}
		case <-ctx.Done():
			return
		}
	}
}
```

**Avoid:** a mediator that slowly absorbs all the business logic and becomes the god
object it was meant to prevent.

**Gotcha:** the state lives in one goroutine, so it needs no mutex. The price is that
one slow `Deliver` stalls every member. Give each member a buffered channel and a
drop or disconnect policy.

### Memento

**Idiomatic form:** keep the old value. When the state is a plain value with no shared
slices or maps, assignment is the snapshot. Keep a stack of them.

```go
type Editor struct {
	state   docState
	history []docState
}

type docState struct {
	text   string // strings are immutable, so sharing them is safe
	cursor int
}

func (e *Editor) Apply(edit func(docState) docState) {
	e.history = append(e.history, e.state)
	e.state = edit(e.state)
}

func (e *Editor) Undo() {
	if len(e.history) == 0 {
		return
	}
	e.state = e.history[len(e.history)-1]
	e.history = e.history[:len(e.history)-1]
}
```

**Avoid:** `Originator`, `Caretaker` and an opaque `Memento` interface. Unexported
fields already keep a snapshot opaque to other packages.

**Gotcha:** if the state holds slices or maps, every snapshot shares them. Clone on save
(see Prototype) or only ever replace them. Cap the history, or it grows for the life of
the process.

### Observer

**Idiomatic form:** callbacks, where subscribing returns the function that
unsubscribes. Use channels only when subscribers run in their own goroutines, and tie
their lifetime to a `context.Context`.

```go
type Bus[E any] struct {
	mu   sync.Mutex
	next int
	subs map[int]func(E)
}

// Subscribe returns the function that removes the subscription.
func (b *Bus[E]) Subscribe(fn func(E)) (unsubscribe func()) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.subs == nil {
		b.subs = map[int]func(E){}
	}
	id := b.next
	b.next++
	b.subs[id] = fn
	return func() {
		b.mu.Lock()
		defer b.mu.Unlock()
		delete(b.subs, id)
	}
}

func (b *Bus[E]) Publish(e E) {
	b.mu.Lock()
	fns := slices.Collect(maps.Values(b.subs))
	b.mu.Unlock()
	for _, fn := range fns {
		fn(e) // outside the lock, so a handler may unsubscribe
	}
}
```

**Avoid:** `Subject` and `Observer` interfaces with `Attach`, `Detach` and
`Update(subject)`, where every observer pulls state back out of the subject.

**Gotcha:** a forgotten unsubscribe leaks the subscriber and everything its closure
captured. Handlers run on the publisher's goroutine, so one slow handler slows every
publish. With channels, choose a slow-subscriber policy on purpose: **block** (one
slow reader stalls everyone), **drop** (`select` with a `default` case, plus a counter),
or **buffer** (delays the same problem). Only the publisher closes a channel.

### State

**Idiomatic form:** a named type with constants and the transitions in one table or one
`switch`. Use a state interface only when each state carries real behavior of its own.

```go
type OrderStatus int

const (
	Pending OrderStatus = iota
	Paid
	Shipped
	Cancelled
)

// allowed is the whole state machine, in one place.
var allowed = map[OrderStatus][]OrderStatus{
	Pending: {Paid, Cancelled},
	Paid:    {Shipped, Cancelled},
}

func (o *Order) Transition(to OrderStatus) error {
	if !slices.Contains(allowed[o.Status], to) {
		return fmt.Errorf("order %s: cannot go from %v to %v", o.ID, o.Status, to)
	}
	o.Status = to
	return nil
}
```

**Avoid:** one struct per state implementing every method, most of them returning
"not allowed in this state".

**Gotcha:** run `stringer` on the status type so errors read `Paid`, not `1`. The
`exhaustive` linter checks that every `switch` over the constants covers all of them.
When states are steps in a loop, as in a lexer, the state-function form `type stateFn
func(*lexer) stateFn` is a neat alternative.

### Strategy

**Idiomatic form:** pass a function. Use an interface only when a strategy needs several
methods or naturally carries configuration.

```go
type PricingFunc func(base int64, c Customer) int64

func Standard(base int64, _ Customer) int64 { return base }

func Loyalty(pct int64) PricingFunc {
	return func(base int64, c Customer) int64 {
		if c.Years >= 2 {
			return base - base*pct/100
		}
		return base
	}
}

func Checkout(items []Item, c Customer, price PricingFunc) int64 {
	var total int64
	for _, it := range items {
		total += price(it.PriceCents, c)
	}
	return total
}

// The standard library works the same way:
// slices.SortFunc(orders, func(a, b Order) int { return cmp.Compare(b.Total, a.Total) })
```

**Avoid:** a `PricingStrategy` interface, one struct per strategy, and a context struct
holding the current one, all to pass a single function. Also avoid a strategy parameter
with only one strategy ever passed.

### Template Method

**Idiomatic form:** a function that runs the fixed steps and takes the varying steps as
function arguments or a small interface.

```go
// Source supplies only the steps that vary between importers.
type Source interface {
	Fetch(ctx context.Context) (io.ReadCloser, error)
	Parse(r io.Reader) ([]Record, error)
}

// Import is the fixed skeleton.
func Import(ctx context.Context, src Source, store Store) error {
	rc, err := src.Fetch(ctx)
	if err != nil {
		return fmt.Errorf("fetch: %w", err)
	}
	defer rc.Close()
	recs, err := src.Parse(rc)
	if err != nil {
		return fmt.Errorf("parse: %w", err)
	}
	return store.SaveAll(ctx, recs)
}
```

**Avoid:** a `BaseImporter` struct with a `Run` method, embedded in each importer that
"overrides" `Parse`.

**Gotcha:** that embedded version compiles and runs, and it is wrong. `BaseImporter.Run`
calls `BaseImporter.Parse`, never the outer type's `Parse`, because embedding has no
virtual dispatch. The default step runs silently.

### Visitor

**Idiomatic form:** a type switch over a closed set of types. For trees, a walk function
that takes a callback, like `ast.Inspect`, or an iterator, like `ast.Preorder`.

```go
// Shape is a closed set: only this package can add cases.
//
//sumtype:decl
type Shape interface{ isShape() }

type Circle struct{ R float64 }
type Rect struct{ W, H float64 }

func (Circle) isShape() {}
func (Rect) isShape()   {}

// A new operation is a new function. No Accept methods needed.
func Area(s Shape) float64 {
	switch s := s.(type) {
	case Circle:
		return math.Pi * s.R * s.R
	case Rect:
		return s.W * s.H
	default:
		panic(fmt.Sprintf("unhandled shape %T", s))
	}
}
```

**Avoid:** `Accept(v Visitor)` on every node plus a `Visitor` interface with a method
per node type. It pays off only when code in other packages adds many operations and
you want the compiler, not a linter, to flag every visitor when a node type is added.

**Gotcha:** the compiler does not check a type switch for missing cases. The
`gochecksumtype` linter does, for interfaces marked `//sumtype:decl` as above; until it
runs in CI, the `default` panic is the only guard.

## Java in Go: smells to catch in review

- **Interfaces declared next to their only implementation,** especially when the
  constructor returns them. Declare interfaces where they are consumed.
- **`IUserService`, `UserServiceImpl`, `AbstractX`, `BaseX` names.** Name the concrete
  type after what it is (`postgres.Store`), and the interface after what it does
  (`Store`, `Notifier`).
- **Getters named `GetName()`.** Go uses `Name()` and `SetName()`. Generated protobuf
  code is the exception.
- **A "base struct" embedded to fake inheritance,** with the outer type expected to
  override methods the base calls. It will not; see Template Method.
- **A Singleton as a package-level variable set in `init()`** with a `GetInstance()`
  accessor. Pass the value in.
- **Factories of factories,** and any `XFactory` interface with a single `Create` method.
  A function does the same job.
- **Builders with chained setters** for what is a plain config struct.
- **`any` parameters plus type assertions to simulate overloading.** Write two functions
  with two names, or use generics.
- **Packages named after pattern roles or layers:** `factories`, `strategies`,
  `interfaces`, `models`, `utils`. Name packages after what they provide.
