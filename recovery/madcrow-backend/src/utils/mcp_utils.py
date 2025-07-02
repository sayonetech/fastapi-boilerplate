"""MCP utility functions."""

import click
from fastmcp import FastMCP


async def display_mcp_components(mcp_server: FastMCP) -> FastMCP:
    """Display MCP server components with colored logging."""
    # List the components that were created
    tools = await mcp_server.get_tools()
    resources = await mcp_server.get_resources()
    templates = await mcp_server.get_resource_templates()
    prompts = await mcp_server.get_prompts()

    tools_count = len(tools)
    tools_color = "green" if tools_count > 0 else "red"
    click.echo(click.style(f"{tools_count} Tool(s): {', '.join([t.name for t in tools.values()])}", fg=tools_color))

    resources_count = len(resources)
    resources_color = "green" if resources_count > 0 else "red"
    click.echo(
        click.style(
            f"{resources_count} Resource(s): {', '.join([r.name for r in resources.values()])}", fg=resources_color
        )
    )

    templates_count = len(templates)
    templates_color = "green" if templates_count > 0 else "red"
    click.echo(
        click.style(
            f"{templates_count} Resource Template(s): {', '.join([t.name for t in templates.values()])}",
            fg=templates_color,
        )
    )

    prompts_count = len(prompts)
    prompts_color = "green" if prompts_count > 0 else "red"
    click.echo(
        click.style(f"{prompts_count} Prompt(s): {', '.join([p.name for p in prompts.values()])}", fg=prompts_color)
    )

    return mcp_server
