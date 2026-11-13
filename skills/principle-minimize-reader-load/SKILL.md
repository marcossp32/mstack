---
name: principle-minimize-reader-load
description: Keeps code easy to follow by cutting the work a reader must do. Fewer layers between a question and its answer (no one-caller wrappers, pass-through classes or adapters with one implementation) and less hidden or mutable state to keep in mind (globals, shared mutable objects, flags set far away). Use when writing or reviewing code that is hard to trace, adding a wrapper, service, manager or interface, or deciding whether a layer earns its place.
---

# Minimize reader load

Code is maintainable when a reader can understand it with little effort. Two things cost that effort, and they are independent:

- **Layers to trace:** how many jumps between a question ("what does this do?") and its answer.
- **State to hold:** how much hidden or changing context the reader must keep in their head.

Lines of code, complexity metrics and "clean architecture" are only proxies for these two.

## Why

Readers, people and agents alike, have limited working memory. Every extra jump and every hidden variable is a place to lose the thread and a place for bugs to hide. A layer that does nothing still has to be opened, read and understood.

## What good looks like

- **Each layer earns its place.** It hides a real decision or real complexity behind a smaller interface. Wrappers with one caller, adapters with one implementation and classes that forward the same calls are inlined, unless the adapter is the boundary to code you do not control (see `principle-boundary-discipline`).
- **Adjacent layers speak different abstractions.** If a layer repeats the methods and arguments of the one below, it adds reading without saving any.
- **State lives close to its use.** Prefer values passed in and returned over globals, singletons and objects mutated from several places. Keep mutable things in the smallest scope that works.

## Self-check

Pick a question about the code, like "where is the discount applied?". Count the files and functions you must open to answer it, and the variables whose values you must track. If a change raises either count without a clear gain, find a flatter way.

## Traps

- **Layers "for the future".** An interface for a second implementation that does not exist yet is cost today for a guess.
- **Splitting for size.** A long function broken into many tiny ones that only make sense together can be harder to read than the original.
