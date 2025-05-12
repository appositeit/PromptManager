#MCP Feature Server

Prompt Manager is really good. Lets make a complementary standalone piece of software that is an MCP Server that we can integrate with Claude Desktop so that rather than having to copy paste the text, we can simply ask CD to pull the apppropriate prompt from prompt manager. We should be able to use the REST or Websocket APIs.

Do not start writing code. Let's start by discussing the features and the API.

I think we need to be able list the possible prompts, and retrieve a prompt using a fuzzy match. Maybe it would be useful to also be able to push a prompt *into* prompt manager?

I have made a subfolder which is our new project directory for work related to the prompt manager MCP server:
/home/jem/development/prompt_manager/mcp_server

It should reflect the normal project folder structure (doc, doc/progress, src, prompts, tools, bin, etc.).

Again, don't write any code yet. First we dicuss features and the API. Once we've agreed, write a project_overview and an API description.


#MCP Feature Server, part 2

Please read:

/home/jem/ai/prompts/llms-full.md

...which describes the mcp protocol in detail.

We should use the STDIO interface for simplicity. I'd prefer to use python.

Make sure you use the MCP server subfolder as our new project directory:
/home/jem/development/prompt_manager/mcp_server
