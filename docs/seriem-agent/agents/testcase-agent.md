# Testcase Subagent

## Purpose

Work with testcase `.xml` files in two modes:

1. **Generate** a new testcase XML instance from an existing `.datamodel`
2. **Modify** an existing testcase XML by changing values only while preserving structure

The subagent always returns **XML only**; the main agent is responsible for writing/overwriting files.

## Implementation

- Subagent: `backend/app/agents/subagents/testcase_agent.py`
- Main-agent tool wrappers (exposed to the supervisor agent):
  - `backend/app/agents/main_agent.py` → `generate_testcase_from_datamodel(datamodel_path, description)`
  - `backend/app/agents/main_agent.py` → `modify_testcase_xml(source_testcase_path, description)`

## Tool access / permissions

Read-only filesystem tools:

- `ls(path)`: list directories under storage root
- `read_file(path)`: read `.datamodel` / `.xml` inputs from storage

No write access. Persisting changes is the main agent’s job.

## Mode 1: generate testcase from datamodel

### Inputs

- `datamodel_path`: path to the `.datamodel` file (relative to storage root)
- `description`: requirements/constraints for values and structure

### Output

- One well-formed XML document that follows the datamodel semantics.
- Uses realistic placeholder values when requirements are underspecified.

## Mode 2: modify existing testcase XML (structure preserved)

### Inputs

- `source_testcase_path`: path to the source testcase `.xml` (relative to storage root)
- `description`: instructions for value changes

### Output

- One well-formed XML document with **the same structure** (element/attribute names and overall layout preserved).
- Only text nodes / attribute values are changed.

## Example user prompts (to the main agent)

- Generate:\n  “Create a minimal testcase from `Test_Agent/bank_client_signup.datamodel` with realistic values and save it as `Test_Agent/bank_client_signup_testcase.xml`.”\n\n- Modify:\n  “Modify `TerminationArrears/TestCases/<file>.xml`: change policy IDs and dates to new realistic values but keep structure. Save as a new testcase file.”


