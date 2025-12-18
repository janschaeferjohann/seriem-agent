# Ideas
- Agent as MCP tool: expose seriem-agent via MCP to plug into other IDEs / API-driven workflows.
- MCP tool for Docubot: allow documentation querying with structured responses for support agents.
- Preview template generation: render templates to PNG for quick result validation before committing changes.
- check OpenCode Implementation on GitHub (OSS CC Clone)

## Technical Concepts to Consider
- Vercels workflow github repo for agent builder
- Context offloading -> e.g. to filesystem (in built in langchain deep agent i believe)
- summarization for saving tokens -> seems mostly impractical for our usecase for generating xmls?
- make sure to hit kv-cache often -> keep similar things similar
- context reduction via compaction
- 128k tokens without context rot
- summarize first 25 tool calls while leaving latest 25 turns untouched for no compression loss
- for agent subagent communication two patterns are possible: 1) agent creates prompt which is the entire context for subagent -> clearly defined task and result; 2) agent shares full prior context with subagent
- context offloading: dynamic rag on tool descriptions, tool definitions are front of context -> kv cache reset
- contect offloading level 1: function calling, manus uses atomic functions like read, write, search etc
- context offloading level 2: sandbox utilities, each session run in a full vm sandbox, model can shell utlities cli
- take a look at memory

## Technical Components
- Agent Framework: LangChain + LangGraph -> Typescript? Alternative: Claude Agent SDK/ AWS Agent SDK
- Subagents -> See Concept.md
- Models: Claude -> AWS -> Contact Luis Habermayer @AWS? Team Vladi
- Session + Memory Storage
- File / Workspace / Content Hub Access -> Standalone vs Integrated
- Auth -> Customer Auth, User Auth, User Rights
- Observability (Logs, OpenTelemetry)
- Git Connection
- Verifications
- Evaluations
- Initialization: Inspect Workspace, write rules, check project hierarchies, identify framework etc


## Offramp -> If only parts work
- Make Subagents available as single functions via gui in Content Hub e.g. -> Create Datamodel, Insert Paragraph, Create Style etc.
- Make Orchestration deterministic via Workflow Builder -> Datamodel then Testcase then 

## Considerations
- How can we guide the supervisor agent to get an idea of the order of operations? Is it a more or less stable workflow or is too flexible? -> Chain of Thought and ReAct seems to be frameworks addressing this
- What are expected context lengths (input/output)?
- How is project hierarchy handled? Read from .project files?

### Notes from Google on Agents

#### Introduction to Agents

At its core, an agent operates on a continuous, cyclical process to achieve its objectives.
While this loop can become highly complex, it can be broken down into five fundamental
steps as discussed in detail in the book Agentic System Design:6
1. Get the Mission: The process is initiated by a specific, high-level goal. This mission is
provided by a user (e.g., "Organize my team's travel for the upcoming conference") or an
automated trigger (e.g., "A new high-priority customer ticket has arrived").
2. Scan the Scene: The agent perceives its environment to gather context. This involves
the orchestration layer accessing its available resources: "What does the user's request
say?", "What information is in my term memory? Did I already try to do this task? Did the
user give me guidance last week?", "What can I access from my tools, like calendars,
databases, or APIs?"
3. Think It Through: This is the agent's core "think" loop, driven by the reasoning model. The
agent analyzes the Mission (Step 1) against the Scene (Step 2) and devises a plan. This
isn't a single thought, but often a chain of reasoning: "To book travel, I first need to know
who is on the team. I will use the get_team_roster tool. Then I will need to check their
availability via the calendar_api."
4. Take Action: The orchestration layer executes the first concrete step of the plan.
It selects and invokes the appropriate tool—calling an API, running a code function,
or querying a database. This is the agent acting on the world beyond its own
internal reasoning.
5. Observe and Iterate: The agent observes the outcome of its action. The get_
team_roster tool returns a list of five names. This new information is added to the
agent's context or "memory." The loop then repeats, returning to Step 3: "Now that I
have the roster, my next step is to check the calendar for these five people. I will use
the calendar_api."

--> Scene Setting like project references, styles, datamodels, etc come before deciding on the necessary steps to fulfill the task!

#### Debug with OpenTelemetry Traces: Answering "Why?"

When your metrics dip or a user reports a bug, you need to understand "why." An OpenTelemetry trace is a high-fidelity, step-by-step recording of the agent's entire execution path (trajectory), allowing you to debug the agent's steps.

With traces, you can see the exact prompt sent to the model, the model's internal reasoning (if available), the specific tool it chose to call, the precise parameters it generated for that tool, and the raw data that came back as an observation. Traces can be complicated the first time you look at them but they provide the details needed to diagnose and fix the root cause of any issue. Important trace details may be turned into metrics, but reviewing traces is primarily for debugging, not overviews of performance. Trace data can be seamlessly collected in platforms like Google Cloud Trace, which visualize and search across vast quantities of traces, streamlining root cause analysis.

#### Cherish Human Feedback: Guiding Your Automation

Instead of an agent using an interface on behalf of the user, the LM can change the UI to meet the needs of the moment. This can be done with Tools which control UI (MCP UI), or specialized UI messaging systems which can sync client state with an agent (AG UI), and even generation of bespoke interfaces (A2UI).

#### Describe actions, not implementations

Assuming each tool is well-documented, the model's instructions should describe actions, not specific tools. This is important to eliminate any possibility of conflict between instructions on how to use the tool (which can confuse the LLM). Where the available tools can change dynamically, as with MCP, this is even more relevant.

• Describe what, not how: Explain what the model needs to do, not how to do it. For example, say "create a bug to describe the issue", instead of "use the create_bug tool".
• Don't duplicate instructions: Don't repeat or re-state the tool instructions or documentation. This can confuse the model, and creates an additional dependency between the system instructions and the tool implementation.
• Don't dictate workflows: Describe the objective, and allow scope for the model to use tools autonomously, rather than dictating a specific sequence of actions.
• DO explain tool interactions: If one tool has a side-effect that may affect a different tool, document this. For instance, a fetch_web_page tool may store the retrieved web page in a file; document this so the agent knows how to access the data.

```python
def fetchpd(pid):
    """
    Retrieves product data
    Args:
        pid: id
    Returns:
        dict of data
    """
```

#### Publish tasks, not API calls

Tools should encapsulate a task the agent needs to perform, not an external API. It's easy to write tools that are just thin wrappers over the existing API surface, but this is a mistake. Instead, tool developers should define tools that clearly capture specific actions the agent might take on behalf of the user, and document the specific action and the parameters needed. APIs are intended to be used by human developers with full knowledge of the available data and the API parameters; complex Enterprise APIs can have tens or even hundreds of possible parameters that influence the API output. Tools for agents, by contrast, are expected to be used dynamically, by an agent that needs to decide at runtime which parameters to use and what data to pass. If the tool represents a specific task the agent should accomplish, the agent is much more likely to be able to call it correctly.

#### Make tools as granular as possible

Keeping functions concise and limited to a single function is standard coding best practice; follow this guidance when defining tools too. This makes it easier to document the tool and allows the agent to be more consistent in determining when the tool is needed.

• Define clear responsibilities: Make sure each tool has a clear, well-documented purpose. What does it do? When should it be called? Does it have any side effects? What data will it return?
• Don't create multi-tools: In general, don't create tools that take many steps in turn or encapsulate a long workflow. These can be complicated to document and maintain, and can be difficult for LLMs to use consistently. There are scenarios when such a tool may be useful -- for instance, if a commonly performed workflow requires many tool calls in sequence, defining a single tool to encapsulate many operations may be more efficient. In these cases be sure to document very clearly what the tool is doing so the LLM can use the tool effectively.

#### Design for concise output

Poorly designed tools can sometimes return large volumes of data, which can adversely affect performance and cost.

• Don't return large responses: Large data tables or dictionaries, downloaded files, generated images, etc. can all quickly swamp the output context of an LLM. These responses are also frequently stored in an agent's conversation history, so large responses can impact subsequent requests as well.
• Use external systems: Make use of external systems for data storage and access. For instance, instead of returning a large query result directly to the LLM, insert it into a temporary database table and return the table name, so a subsequent tool can retrieve the data directly. Some AI frameworks also provide persistent external storage as part of the framework itself, such as the Artifact Service in Google ADK.

#### Use validation effectively

Most tool calling frameworks include optional schema validation for tool inputs and outputs. Use this validation capability wherever possible. Input and output schemas serve two roles with LLM tool calling. They serve as further documentation of the tool's capabilities and function, giving the LLM a clearer picture of when and how to use the tool; and they provide a run-time check on tool operation, allowing the application itself to validate whether the tool is being called correctly.

#### Provide descriptive error messages

Tool error messages are an overlooked opportunity for refining and documenting tool capabilities. Often, even well-documented tools will simply return an error code, or at best a short, non-descriptive error message. In most tool calling systems, the tool response will also be provided to the calling LLM, so it provides another avenue for giving instructions. The tool's error message should also give some instruction to the LLM about what to do to address the specific error. For example, a tool that retrieves product data could return a response that says "No product data found for product ID XXX. Ask the customer to confirm the product name, and look up the product ID by name to confirm you have the correct ID."


Memory generation is an expensive operation requiring LLM calls and database writes. For agents in production, memory generation should almost always be handled asynchronously as a background process23.

