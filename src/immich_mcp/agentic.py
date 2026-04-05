from typing import Any

from fastmcp import Context

from .server import mcp


def register_agentic_tools():
    """Register agentic workflow tools with sampling capabilities."""

    @mcp.tool()
    async def immich_help(ctx: Context, category: str | None = None) -> str:
        """Get comprehensive categorized help for Immich MCP tools with conversational guidance.

        Args:
            category: Optional category to filter help (e.g., 'photos', 'albums', 'system', 'agentic')
        """
        help_data = {
            "photos": "Tools for searching and uploading photos. Use 'search_photos' to find assets and 'upload_photos' to add new ones.",
            "albums": "Tools for managing collections. Use 'list_albums' or 'create_album'.",
            "system": "Tools for checking Immich server stats. Use 'server_stats' or 'server_health'.",
            "agentic": "Tools like 'agentic_immich_workflow' for autonomous orchestration.",
        }

        if category and category.lower() in help_data:
            ctx.info(f"Retrieving help for category: {category}")
            return f"### Immich Help: {category.capitalize()}\n\n{help_data[category.lower()]}\n\nIs there anything specific you'd like to do with these tools?"

        categories_str = ", ".join([f"`{c}`" for c in help_data.keys()])
        return f"### Immich MCP Help System\n\nI can help you with the following categories: {categories_str}.\n\nSpecified a category to get more detailed information, or just ask me a question about your photo library!"

    @mcp.tool()
    async def agentic_immich_workflow(
        ctx: Context,
        workflow_prompt: str,
        available_tools: list[str] | None = None,
    ) -> str:
        """Execute agentic Immich workflows using FastMCP 3.1 sampling.

        Uses SEP-1577 to autonomously orchestrate complex photo management operations.

        Args:
            workflow_prompt: Description of the workflow to execute
            available_tools: Optional list of tool names to restrict the agent to
        """
        ctx.info(f"Starting agentic workflow: {workflow_prompt}")

        # Use sampling to get a plan and execution guidance from the LLM
        sampling_result = await ctx.sample(
            prompt=f"Goal: {workflow_prompt}\n\nPlan and execute this using Immich MCP tools. If helpful, provide a step-by-step summary.",
            max_tokens=600,
        )

        return f"### Agentic Workflow Result\n\n{sampling_result.text}"

    @mcp.tool()
    async def intelligent_photo_processing(
        ctx: Context,
        photos: list[dict[str, Any]],
        processing_goal: str,
        available_operations: list[str],
    ) -> str:
        """Intelligent batch photo processing using FastMCP 3.1 sampling.

        LLM analyzes the batch and intelligently decides optimal operations.

        Args:
            photos: List of photo objects to process
            processing_goal: What you want to achieve
            available_operations: Operations the LLM can choose from
        """
        ctx.info(f"Intelligent processing for {len(photos)} photos: {processing_goal}")

        # Sample for processing strategy
        sampling_result = await ctx.sample(
            prompt=f"Goal: {processing_goal}\nBatch Size: {len(photos)}\nOperations: {available_operations}\n\nSuggest the best processing sequence for these assets.",
            max_tokens=500,
        )

        return f"### Intelligent Processing Analysis\n\n{sampling_result.text}"

    @mcp.tool()
    async def conversational_immich_assistant(
        ctx: Context,
        user_query: str,
    ) -> str:
        """Conversational Immich assistant for natural language interaction.

        Args:
            user_query: Natural language query about Immich operations
        """
        ctx.info(f"Processing conversational query: {user_query}")

        # Sample the LLM for a helpful conversational response
        sampling_result = await ctx.sample(
            prompt=f"User Query: {user_query}\n\nAs an Immich assistant, provide a helpful, conversational response based on your knowledge of the Immich MCP tools. Suggest specific tools if relevant.",
            max_tokens=300,
        )

        return sampling_result.text
