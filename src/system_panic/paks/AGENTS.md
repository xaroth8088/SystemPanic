# Pak loader memory

This directory contains immutable definitions and discovery, not game content. See [external authoring](../../../paks/AGENTS.md), [format guide](../../../docs/paks.md) and [public ABCs](../pak_api.py).

API 2 discovers six component folder types and imports their conventional Python entry files. A module must provide a concrete subclass of the matching ABC; COMPONENT or a configured class resolves ambiguity. Validate metadata, relative file paths, abstract methods, init-time asset handles and component configuration before admitting a Pak.

discover(roots) returns an immutable catalog of class/factory definitions, component eligibility pools, complete Pak IDs and isolated issues. Actual instances are constructed per run; never cache mutable component objects in catalog metadata. Preview instances belong only to the renderer and have no world/audio service.

Asset-only inheritance resolves dependencies before class construction and overlays component-local filenames. It does not inspect author-owned handle attribute names. The first validated manifest claims an ID. Missing/cyclic dependencies, malformed/unsupported manifests and import/init failures skip the affected Pak while preserving other content.

Modules and relative helpers use isolated package namespaces and fresh source, including unchanged-timestamp edits. Rescanning replaces the catalog only outside active runs. This is trusted local Python, not a security sandbox or a remote catalog. Avoid launch IDs, content imports, behavior branches and mutable global registries in core code.
