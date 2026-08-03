# OffshoreSafe Project Definition

`project.yaml` is the versioned entry point for an OffshoreSafe engineering
workflow. It stores engineering configuration and references; numerical
algorithms remain in UQRA.

## Installation

Install both monorepo distributions in development mode:

``` powershell
python -m pip install -e ".[dev]"
python -m pip install -e packages/offshoresafe
```

The dependency direction is `OffshoreSafe -> UQRA`. Importing UQRA never
imports OffshoreSafe.

## Schema version 1.0

The required root fields are:

| Field | Purpose |
|---|---|
| `schema_version` | Configuration contract; currently exactly `"1.0"` |
| `project` | Stable project ID, name, description, and organization |
| `turbine` | Turbine ID, model, rated power, and definition file |
| `solver` | Solver ID, adapter name, input file, executable, and settings |
| `analyses` | One or more uniquely identified analysis configurations |

Unknown fields are rejected at every level. Identifiers begin with a letter
and contain only letters, digits, `_`, `-`, or `.`. Rated power must be
positive, analysis IDs must be unique, and required referenced files must exist
unless path checking is explicitly disabled.

See `examples/projects/minimal/project.yaml` for a complete copyable example.

## Loading and saving

``` python
from offshoresafe import OffshoreProject

project = OffshoreProject.load("examples/projects/minimal/project.yaml")
print(project.project.project_id)
print(project.solver.input_file)

project.save("build/project-copy.yaml")
```

Relative paths are resolved against the directory containing the loaded YAML.
The in-memory paths are absolute. Saving writes portable paths relative to the
target YAML where possible. Use `check_paths=False` only for authoring or
validation workflows that intentionally reference files not created yet.

Malformed YAML raises `ValueError`; a missing project file raises
`FileNotFoundError`; schema violations raise Pydantic `ValidationError`; and a
missing referenced file reports its full schema field and resolved path.
