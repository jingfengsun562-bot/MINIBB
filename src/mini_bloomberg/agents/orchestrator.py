"""
Single-agent tool-use loop with:
  - claude-sonnet-4-6 (dev) / claude-opus-4-7 (set CLAUDE_MODEL in .env)
  - Streaming output via client.messages.stream()
  - Prompt caching on the system prompt (cache_control ephemeral)
  - Parallel tool execution when Claude issues multiple tool_use blocks
"""

import json
import threading
from typing import Any

import anthropic
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from mini_bloomberg.agents.prompts import ANALYST_SYSTEM_PROMPT
from mini_bloomberg.agents.tools import ALL_TOOLS, FUNCTIONS_BY_NAME
from mini_bloomberg.config import get_settings
from mini_bloomberg.render.cli_renderer import console, DIM, ORANGE, HEADER

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
    return _client


# ── Tool execution ─────────────────────────────────────────────────────────────

def _run_tool(tool_use: Any) -> dict:
    """Execute one tool_use block, return a tool_result dict."""
    fn = FUNCTIONS_BY_NAME.get(tool_use.name)
    if fn is None:
        result_content = json.dumps({"status": "error", "message": f"Unknown tool: {tool_use.name}"})
    else:
        try:
            result_content = json.dumps(fn.run(**tool_use.input))
        except Exception as e:
            result_content = json.dumps({"status": "error", "message": str(e)})

    return {
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "content": result_content,
    }


def _run_tools_parallel(tool_uses: list) -> list[dict]:
    """Run all tool_use blocks concurrently via threads."""
    results: list[dict | None] = [None] * len(tool_uses)

    def _worker(i: int, tu: Any) -> None:
        results[i] = _run_tool(tu)

    threads = [threading.Thread(target=_worker, args=(i, tu)) for i, tu in enumerate(tool_uses)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return results  # type: ignore[return-value]


# ── Streaming helpers ──────────────────────────────────────────────────────────

def _stream_response(client: anthropic.Anthropic, model: str, messages: list) -> tuple[str, list]:
    """
    Stream one turn. Returns (full_text, tool_use_blocks).
    Prints streamed text live to the terminal.
    Prompt caching applied to the system prompt.
    """
    full_text = ""
    tool_uses = []

    system = [
        {
            "type": "text",
            "text": ANALYST_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},  # prompt caching
        }
    ]

    with client.messages.stream(
        model=model,
        system=system,
        tools=ALL_TOOLS,
        messages=messages,
        max_tokens=4096,
    ) as stream:
        # Stream text tokens live
        with Live(console=console, refresh_per_second=15, transient=False) as live:
            for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_start":
                        if hasattr(event, "content_block") and event.content_block.type == "tool_use":
                            tool_uses.append(event.content_block)
                    elif event.type == "content_block_delta":
                        if hasattr(event, "delta"):
                            if hasattr(event.delta, "text"):
                                full_text += event.delta.text
                                live.update(
                                    Panel(
                                        Markdown(full_text),
                                        title=f"[{ORANGE}]AI Analyst[/{ORANGE}]",
                                        border_style="blue",
                                        padding=(1, 2),
                                    )
                                )
                            elif hasattr(event.delta, "partial_json") and tool_uses:
                                # Accumulate tool input JSON
                                last = tool_uses[-1]
                                if not hasattr(last, "_partial"):
                                    last._partial = ""
                                last._partial += event.delta.partial_json

        # Finalise tool_use inputs from streamed partial JSON
        final_message = stream.get_final_message()

    # Extract complete tool_use blocks from the final message
    tool_use_blocks = [
        b for b in final_message.content if b.type == "tool_use"
    ]

    return full_text, tool_use_blocks, final_message


# ── Main agent loop ────────────────────────────────────────────────────────────

def run_agent(query: str) -> None:
    """
    Run the tool-use loop for a user query. Prints streaming output to terminal.
    Exits when Claude returns end_turn with no more tool calls.
    """
    settings = get_settings()
    model = settings.claude_model
    client = _get_client()

    messages: list[dict] = [{"role": "user", "content": query}]

    console.print()
    console.print(
        f"[{DIM}]AI Analyst thinking… (model: {model})[/{DIM}]"
    )

    max_rounds = 8  # guard against infinite loops
    for round_num in range(max_rounds):

        # Show spinner while tools run (not during streaming)
        full_text, tool_use_blocks, final_message = _stream_response(client, model, messages)

        # Append assistant turn
        messages.append({"role": "assistant", "content": final_message.content})

        if final_message.stop_reason == "end_turn" or not tool_use_blocks:
            # Done — final answer already printed via streaming
            if not full_text.strip():
                console.print(f"[{DIM}](No text response)[/{DIM}]")
            break

        # Execute tools in parallel, show which ones are running
        tool_names = ", ".join(f"[{ORANGE}]{tu.name}({tu.input})[/{ORANGE}]" for tu in tool_use_blocks)
        console.print(f"\n[{DIM}]Running tools: {tool_names}[/{DIM}]")

        tool_results = _run_tools_parallel(tool_use_blocks)
        messages.append({"role": "user", "content": tool_results})

    else:
        console.print(f"[dim]Agent reached max rounds ({max_rounds}) — stopping.[/dim]")

    console.print()
