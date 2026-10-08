# Notice

This repository is an independent fork of **OMP Desktop**, with a Simplified Chinese interface
added on top.

## Upstream

- **OMP Desktop** — <https://github.com/apoc/omp-desktop>
  MIT License, Copyright (c) 2026 Miroslav Drbal.
  The application source, architecture and documentation in this repository are upstream work;
  this fork changes UI strings and three configuration values (listed in the README).

- **oh-my-pi (`omp`)** — <https://github.com/can1357/oh-my-pi>
  The coding agent the app drives. It is **not** bundled or redistributed here: the app spawns
  whatever `omp` executable is on `PATH`.

## This fork

- `localization/zh.json` — the English → Simplified Chinese dictionary.
- `localization/apply.py`, `localization/patch-config.py` — the applier and the config patch.
- `localization/build-and-install.sh`, `localization/HOWTO.md` — build and maintenance helpers.
- `README.md` — the fork's own documentation.
- The Chinese UI text inserted into `src/` by `localization/apply.py`.

The files listed above are original work of this fork and are released under the same MIT
license as upstream. When rebasing on upstream, upstream's `LICENSE` and copyright remain in
force for everything upstream wrote.
