# Security policy

## Reporting a vulnerability

Please do not open a public issue for a security problem. Report it privately through GitHub:
**Security → Report a vulnerability** on this repository. You will get a reply within seven days, and a
fix or a clear answer as soon as the problem is understood. Credit is given in the release notes unless
you ask otherwise.

## Scope

| Part | Examples of what counts |
|---|---|
| Python package and command line (`src/dairyguard`) | a crafted CSV log that crashes the reader, runs code or reads files it should not |
| Firmware (`firmware/`) | memory errors in the C core, input that drives the monitor into a wrong state |
| Website and browser app (`docs/`, `demo/`) | script injection, unsafe links, anything that runs code a visitor did not expect |
| Repository and CI (`.github/`) | workflow permissions, untrusted input reaching a workflow |

## Not a security issue

DairyGuard is research software. A verdict that turns out wrong for a real carton of milk is a limitation
of the model, documented under *Limits* in the README, not a vulnerability. Please report it as an
ordinary issue. Nothing here is food-safety advice.

## Supported versions

Only the latest release on the `main` branch receives fixes.
