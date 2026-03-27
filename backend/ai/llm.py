from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional
import pathlib

from core.config import settings

# ─── Shared LLM instance ─────────────────────────────────────────────────────
llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    max_tokens=settings.LLM_MAX_TOKENS,
    openai_api_key=settings.OPENAI_API_KEY,
)

PROMPTS_DIR = pathlib.Path(__file__).parent / "prompts"


# ─── Prompt loader ───────────────────────────────────────────────────────────
def load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


# ─── Core invoke helper ──────────────────────────────────────────────────────
async def invoke_llm(
    system_prompt: str,
    user_message: str,
    extra_context: Optional[dict] = None,
) -> str:
    """
    Send a system + user message to the LLM and return the text response.
    Optionally inject extra_context variables into the system prompt via .format().
    """
    if extra_context:
        system_prompt = system_prompt.format(**extra_context)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)
    return response.content.strip()


# ─── Template-based invoke ───────────────────────────────────────────────────
async def invoke_prompt_file(
    prompt_filename: str,
    user_message: str,
    context: Optional[dict] = None,
) -> str:
    """
    Load a prompt from file and invoke the LLM.
    prompt_filename: e.g. 'task_prompt.txt'
    """
    system_prompt = load_prompt(prompt_filename)
    return await invoke_llm(system_prompt, user_message, context)


# ─── Structured JSON response ────────────────────────────────────────────────
async def invoke_llm_json(
    system_prompt: str,
    user_message: str,
    context: Optional[dict] = None,
) -> dict:
    """
    Invoke the LLM and parse the response as JSON.
    The system prompt should instruct the model to respond ONLY in JSON.
    """
    import json

    raw = await invoke_llm(system_prompt, user_message, context)

    # Strip markdown code fences if present
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}\nRaw response:\n{raw}")
