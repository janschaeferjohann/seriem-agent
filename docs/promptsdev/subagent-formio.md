# Description
The next task is to create another subagent for generating formio.

## Main Agent - Subagent Communication

The main agent will handover the task to create a formio json to the subagent. 
The subagent will call the necessary tools to create that json and respond with that content to the main agent. the main agent will carry out the edit or create operation. Formio files end with .formio

## Subagent tools
The subagent will be able to read files, e.g. an existing datamodel. Based on that file and the user instructions it will generate the formio. Most of the time not all datanodes from the datamodel will be used to generate the formio but only some subset. It is the mainagents task to clarif with the user or specify how to identify the correct datanodes to create the formio from.

It can also generate from natural language input from the user

## Supported modes (A/B/C)

The subagent must support all three operations and automatically select the correct one based on inputs provided by the main agent:

- **A: Generate from natural language**
  - Input: only a description/requirements.
  - Output: a new Form.io JSON schema.

- **B: Generate from datamodel**
  - Input: `datamodel_path` + description/requirements.
  - The subagent must call `read_file(datamodel_path)` and generate the Form.io JSON schema based on the actual datamodel XML.
  - Only a subset of datamodel nodes is typically used; the main agent should provide selection guidance.

- **C: Modify existing .formio**
  - Input: `source_formio_path` + description/requirements.
  - The subagent must call `read_file(source_formio_path)` and apply changes while preserving the overall structure.

### Mode selection rule (no special cases)

1. If `source_formio_path` is provided → **Mode C**
2. Else if `datamodel_path` is provided → **Mode B**
3. Else → **Mode A**

## Detailed information

For more information and a previous prompt (can be improved) please refer to:

- /docs/cookbook/formio.ipynb
