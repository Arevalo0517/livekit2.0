"""
Voice pipeline assembly for LiveKit Agents v1.3.x.

Uses the new Agent + AgentSession API:
- Agent: carries system instructions
- AgentSession: wires together STT, LLM, TTS, VAD

Each call gets a fresh Agent instance with the client's system_prompt.
"""
import logging

from livekit.agents import Agent, AgentSession
from livekit.plugins import deepgram, openai, rime, silero

logger = logging.getLogger(__name__)


class VoiceAgent(Agent):
    """
    A voice AI agent configured with a specific system prompt.
    One instance is created per call.
    """

    def __init__(self, system_prompt: str) -> None:
        super().__init__(instructions=system_prompt)


def build_session(agent_config: dict) -> AgentSession:
    """
    Build and return a configured AgentSession for a call.

    Args:
        agent_config: dict with keys:
            - system_prompt: str — the agent's persona/instructions
            - voice_id: str — Rime speaker name (e.g. "celeste", "ava")
            - language: str — language code (e.g. "es", "en")

    Returns:
        Configured AgentSession ready to be started in a LiveKit room.
    """
    voice_id = agent_config["voice_id"]
    language = agent_config.get("language", "es")
    system_prompt = agent_config["system_prompt"]

    logger.info(
        f"Building pipeline: voice={voice_id}, language={language}, "
        f"prompt_len={len(system_prompt)}"
    )

    vad = silero.VAD.load()

    stt = deepgram.STT(language=language)

    llm = openai.LLM(model="gpt-4o-mini")

    tts = rime.TTS(
        model="arcana",
        speaker=voice_id,
    )

    return AgentSession(
        vad=vad,
        stt=stt,
        llm=llm,
        tts=tts,
    )


def build_agent(agent_config: dict) -> VoiceAgent:
    """
    Build and return a VoiceAgent with the given system prompt.

    Args:
        agent_config: dict with 'system_prompt' key

    Returns:
        VoiceAgent instance with the client's instructions.
    """
    return VoiceAgent(system_prompt=agent_config["system_prompt"])
