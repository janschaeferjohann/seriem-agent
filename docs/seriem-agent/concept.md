# seriem-agent Concept

## Current Snapshot

- Purpose: autonomous AI agent for creating Serie M/ resources.
- Focus areas: to be enumerated separately (capture at high level only for now).
- Status: early concept; gather requirements and constraints before design.
- Next steps: refine this concept file and expand the rationale/README in the `seriem-agent` folder.

## Resource Automation Approach

- Resource surface: Template, Model, Datamodel, Datamapping, FormIO, StyleCollection, Testdata, Testcases.
- Each resource type gets its own subagent with CRUD capabilities; cross-resource dependencies mean subagents may read other files before acting.
- Files live under multiple project roots (Eclipse workspace style).
- Special handling: the systemic `Configuration` project gets a dedicated Configuration Sub Agent (with potential nested subagents).
- Special handling: the shared `Framework` project needs its own Framework Sub Agent for framework-specific resources.
- Default project layout: `Templates/`, `Models/`, `Data/`, `Testdata/`, `Images/`, `Framework/`.
- Content format is primarily XML (FormIO = JSON); subagents edit partial structures and entire files.
- Interaction challenge: before full orchestration exists, a human can manually invoke individual subagents to perform focused edits.
- Validation strategy: prefer schema checks (XSDs) where available; add bespoke validation or linting when schemas are missing.
- Tooling baseline: standard file read/write helpers; terminal access not required beyond file operations.

## Integration and Experience Ideas

- Expose seriem-agent as an MCP tool so it can plug into other IDEs or API-driven workflows.
- Provide a Docubot-oriented MCP tool for structured documentation queries and answers.
- Generate template previews as PNGs for quick visual validation before committing changes.

## Subagent Specification Template (WIP)

- **Purpose & scope**: clarify the resource type, default directories, file formats, and CRUD coverage.
- **System prompt skeleton**: intent statement, guardrails, interaction style, and dependency-reading expectations.
- **Inputs & triggers**: what requests or cues invoke the subagent; include required metadata (project, resource path, linked artefacts).
- **Outputs & deliverables**: files touched, summaries reported back, validation artefacts produced.
- **Toolbox**: list tools by capability—(a) file operations (read/list/edit), (b) validation utilities (XSD checkers, linters), (c) generation/analysis helpers (LLM calls, template expanders). Note whether tools are shared with other subagents or bespoke.
- **Agent↔subagent communication**: define the JSON schema used for hand-offs (common envelope shared across subagents plus resource-specific payload) and how JSON validation enables retries on parsing/validation failures.
- **Cross-subagent dependencies**: enumerate which other artefacts must be read or referenced before CRUD actions.
- **Permissions & access**: default to inheriting main agent rights, but state directory/file restrictions (e.g., Configuration-only paths); note if elevated rights are disallowed.
- **Validation & testing**: schema checks, consistency rules, human review hooks; describe what constitutes success/failure.
- **Interaction mode**: autonomous workflow vs. human-in-the-loop usage; include escalation/clarification guidance.
- **Edge cases & risks**: known tricky patterns (partial XML merges, schema drift) and mitigation steps.


## Main Agent/Orchstrator


## Subagents

### Datamodel

- Generate
- Edit
- Reference Datamodel

### Datamapping

- Generate
- Edit

### Testdata

- Generate
- Edit

### Testcase

tbd

### Model

- Datadef -> Call Sub Datadef
- Containerpart (Pars, Spans, Texts)
- TablePart (Header,Rows, Columns, Cells)
- Styles -> Read Sub StyleCollection
- Visible If -> Call Sub JavaScript
- Data -> Read .datamodel files
- Validate XSD

### Template

- Datadef -> Call Sub Datadef
- Modification Rights
- Document
- DocumentPartRef -> Call Sub References
- Extensions
- ContainerPart (Sub shared with Model?)
- TablePart (Sub shared with Model?)
- ParamDef -> Call Sub References
- Model Ref -> Call Sub References
- Validate XSD

### StyleCollection

- Generate
- Read properties
- Multiple File Handling
- Validate

### Form.IO

- Generate
- Action Script
- Modify with Datamodel
- Validate possible?

### UI Contribution

- Generate
- Include Conditions -> Call Sub Javascript
- Validate

### DataDefinitions

- Generate
- Read -> Response is datamodel Path for data inclusion

### References

- doc refs
- model refs
- Paramdefs

### JavaScript

- 1 Line conditions
- Scripts
- Load/Read .js files


### Metadata
- Generate
- Edit