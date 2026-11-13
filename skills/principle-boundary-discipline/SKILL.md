---
name: principle-boundary-discipline
description: Validates and parses outside input once, where it enters the system (CLI args, environment variables, config files, HTTP requests, external APIs, files, database rows), turning it into proper types, and then trusts those types inside. Keeps business logic free of re-validation, type conversion and framework code. Use when reading env vars or config, handling request or API data, fixing a type or parsing error deep in the code, or deciding where a check or conversion belongs.
---

# Boundary discipline

Outside data is untrusted and untyped until it is parsed. Parse and validate it at the boundary, into the types the rest of the code expects. Inside, trust those types.

## Why

When validation is scattered, every function re-checks the same things, some forget to, and nobody knows which checks are the real ones. Conversions done deep inside (`int(port)` in the server code) work for one caller and break for the next. One parse at the boundary gives one place to get right and one place to test.

## What good looks like

- **At the boundary:** each input (args, env, config, request, response from another service) passes through one function that turns it into a domain value or a clear error. Bad input fails there, with a message that names the input.
- **Inside:** functions receive typed values and do not re-check or re-convert them. No defensive `None` checks deep in call chains for things the boundary already guarantees.
- **Logic is plain.** Business rules live in functions that take and return domain values, testable without the framework, the network or the file system.
- **The boundary's own types stay at the boundary.** Raw request objects, ORM rows or wire formats are not passed through the core. Output crosses it too: turn domain values into the response or file format at the boundary, so domain types do not leak out.

## Where the boundary is

Anything the code does not control: user input, environment, files, the network, other services, the database, the clock. A library's public API is a boundary too, for its callers. Internal code calling internal code is not.

## Traps

- **Fixing a type error where it crashed.** If a string arrives where a number should be, the fix is in the parser at the boundary, so every consumer gets the right type.
- **Validating everything everywhere "to be safe".** Redundant checks are noise and give false confidence. Put the real check in one place.
- **Defaults hidden inside.** A default for a missing setting belongs where the setting is read, so it is visible and the same for everyone.
