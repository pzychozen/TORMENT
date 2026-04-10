"""
Voice Pipeline — STT (Whisper) → TORMENT memory → Qwen generation → TTS.

Runs a live loop: listens for speech, retrieves memory context,
generates a response with the base model, and speaks it back.

TTS backends:
  - voicebox (default): local Voicebox server at http://127.0.0.1:17493
  - edge: edge-tts (free Microsoft TTS, fallback)

Dependencies:
  pip install openai-whisper sounddevice numpy requests soundfile
  Optional: pip install edge-tts pydub  (for edge-tts fallback)
"""

import io
import os
import sys
import time
import asyncio
import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd

log = logging.getLogger(__name__)

# ── audio config ────────────────────────────────────────────────────
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 0.02       # RMS below this = silence
SILENCE_DURATION = 1.5         # seconds of silence to trigger end-of-speech
MIN_SPEECH_DURATION = 0.5      # ignore very short bursts
MAX_RECORDING_DURATION = 30.0  # hard cap per utterance


# ════════════════════════════════════════════════════════════════════
#  STT
# ════════════════════════════════════════════════════════════════════

class WhisperSTT:
    """Speech-to-text using OpenAI Whisper (local)."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None

    def load(self) -> None:
        import warnings
        import whisper
        log.info("Loading Whisper '%s' model ...", self.model_size)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning, message=".*weights_only.*")
            self.model = whisper.load_model(self.model_size)
        log.info("Whisper loaded")

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a numpy audio array (float32, 16kHz mono)."""
        if self.model is None:
            raise RuntimeError("Whisper not loaded — call .load() first")
        audio_f32 = audio.astype(np.float32)
        result = self.model.transcribe(audio_f32, language="en")
        return result.get("text", "").strip()


# ════════════════════════════════════════════════════════════════════
#  TTS — Voicebox (primary)
# ════════════════════════════════════════════════════════════════════

VOICEBOX_DEFAULT_URL = os.environ.get("VOICEBOX_URL", "http://127.0.0.1:17493")

class VoiceboxTTS:
    """TTS via local Voicebox server.

    Speed tips (from API spec):
      - model_size "0.6B" is ~3x faster than "1.7B"
      - engine "luxtts" is 150x realtime on CPU (english only)
      - /generate/stream returns WAV without disk I/O
      - lower max_chunk_chars = faster first-chunk latency
      - normalize=False and no effects_chain skips post-processing
    """

    def __init__(
        self,
        base_url: str = VOICEBOX_DEFAULT_URL,
        profile_id: Optional[str] = None,
        engine: str = "qwen",          # qwen | luxtts | chatterbox | chatterbox_turbo
        model_size: str = "0.6B",       # 0.6B | 1.7B  (qwen engine only)
        language: str = "en",
        max_chunk_chars: int = 300,     # lower = faster first chunk
        normalize: bool = False,        # skip for speed
        use_streaming: bool = True,     # use /generate/stream
        instruct: Optional[str] = None, # qwen delivery instruction e.g. "speak calmly"
    ):
        self.base_url = base_url.rstrip("/")
        self.profile_id = profile_id
        self.engine = engine
        self.model_size = model_size
        self.language = language
        self.max_chunk_chars = max_chunk_chars
        self.normalize = normalize
        self.use_streaming = use_streaming
        self.instruct = instruct
        self._session = None

    def _get_session(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session

    def ping(self) -> bool:
        """Check if Voicebox server is reachable."""
        try:
            r = self._get_session().get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def list_profiles(self) -> list[dict]:
        """List available voice profiles."""
        try:
            r = self._get_session().get(f"{self.base_url}/profiles", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            log.warning("Failed to list profiles: %s", exc)
            return []

    def _resolve_profile(self) -> str:
        """Resolve profile_id: use explicit, or fetch the first available."""
        if self.profile_id:
            return self.profile_id
        if not hasattr(self, '_cached_profile'):
            profiles = self.list_profiles()
            if profiles:
                pid = profiles[0].get("id") or profiles[0].get("profile_id") or "default"
                log.info("Auto-selected Voicebox profile: %s", pid)
                self._cached_profile = pid
            else:
                self._cached_profile = "default"
        return self._cached_profile

    def _build_payload(self, text: str) -> dict:
        payload = {
            "text": text,
            "language": self.language,
            "engine": self.engine,
            "max_chunk_chars": self.max_chunk_chars,
            "normalize": self.normalize,
            "crossfade_ms": 0,
            "profile_id": self._resolve_profile(),
        }
        if self.engine == "qwen":
            payload["model_size"] = self.model_size
        if self.instruct:
            payload["instruct"] = self.instruct
        return payload

    @staticmethod
    def _clean_for_tts(text: str) -> str:
        """Strip emotes, markdown, and other non-speakable content."""
        import re
        # Remove *emotes* and _emphasis_
        text = re.sub(r'\*[^*]+\*', '', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        # Remove markdown bold/headers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # Collapse whitespace
        text = re.sub(r'\n{2,}', '\n', text)
        text = re.sub(r'  +', ' ', text)
        return text.strip()

    def speak(self, text: str) -> None:
        """Generate speech and play it."""
        if not text:
            return

        text = self._clean_for_tts(text)
        if not text:
            return

        t0 = time.time()

        if self.use_streaming:
            self._speak_stream(text)
        else:
            self._speak_file(text)

        elapsed = time.time() - t0
        log.info("TTS took %.2fs for %d chars", elapsed, len(text))

    def _speak_stream(self, text: str) -> None:
        """Use /generate/stream — returns WAV directly, no disk I/O."""
        import soundfile as sf

        payload = self._build_payload(text)
        try:
            r = self._get_session().post(
                f"{self.base_url}/generate/stream",
                json=payload,
                timeout=120,
                stream=True,
            )
            r.raise_for_status()

            # Read the full streamed WAV into memory
            audio_bytes = io.BytesIO(r.content)
            data, sr = sf.read(audio_bytes)
            sd.play(data, sr)
            sd.wait()

        except Exception as exc:
            # Log the response body if available
            resp_body = getattr(getattr(exc, 'response', None), 'text', '')
            if resp_body:
                log.warning("Voicebox stream failed: %s — body: %s", exc, resp_body[:500])
            else:
                log.warning("Voicebox stream failed: %s", exc)
            log.warning("Falling back to file mode")
            self._speak_file(text)

    def _speak_file(self, text: str) -> None:
        """Use /generate — saves to disk on server, returns metadata."""
        payload = self._build_payload(text)
        try:
            r = self._get_session().post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=120,
            )
            r.raise_for_status()
            result = r.json()

            audio_path = result.get("audio_path")
            if audio_path and os.path.exists(audio_path):
                import soundfile as sf
                data, sr = sf.read(audio_path)
                sd.play(data, sr)
                sd.wait()
            else:
                log.warning("Voicebox returned no audio_path or file missing")

        except Exception as exc:
            resp_body = getattr(getattr(exc, 'response', None), 'text', '')
            if resp_body:
                log.error("Voicebox generate failed: %s — body: %s", exc, resp_body[:500])
            else:
                log.error("Voicebox generate failed: %s", exc)


# ════════════════════════════════════════════════════════════════════
#  TTS — edge-tts (fallback)
# ════════════════════════════════════════════════════════════════════

class EdgeTTS:
    """Text-to-speech using edge-tts (free, no API key needed)."""

    def __init__(self, voice: str = "en-US-AriaNeural"):
        self.voice = voice

    async def _synthesize(self, text: str, output_path: str) -> None:
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def speak(self, text: str) -> None:
        if not text:
            return
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
        try:
            asyncio.run(self._synthesize(text, tmp_path))
            self._play_audio(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _play_audio(self, path: str) -> None:
        try:
            import soundfile as sf
            data, sr = sf.read(path)
            sd.play(data, sr)
            sd.wait()
        except Exception:
            try:
                from pydub import AudioSegment
                from pydub.playback import play
                audio = AudioSegment.from_file(path)
                play(audio)
            except Exception as exc:
                log.warning("Could not play audio: %s", exc)


# ════════════════════════════════════════════════════════════════════
#  Audio recorder
# ════════════════════════════════════════════════════════════════════

class AudioRecorder:
    """Records audio from microphone with silence detection."""

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        silence_threshold: float = SILENCE_THRESHOLD,
        silence_duration: float = SILENCE_DURATION,
        min_speech: float = MIN_SPEECH_DURATION,
        max_duration: float = MAX_RECORDING_DURATION,
    ):
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.min_speech = min_speech
        self.max_duration = max_duration

    def record_utterance(self) -> Optional[np.ndarray]:
        """Block until the user speaks and then stops."""
        frames = []
        silence_start = None
        speech_detected = False
        start_time = time.time()

        def callback(indata, frame_count, time_info, status):
            nonlocal silence_start, speech_detected
            if status:
                log.debug("Audio status: %s", status)
            rms = np.sqrt(np.mean(indata ** 2))
            frames.append(indata.copy())
            if rms > self.silence_threshold:
                speech_detected = True
                silence_start = None
            elif speech_detected and silence_start is None:
                silence_start = time.time()

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=CHANNELS,
            dtype="float32",
            callback=callback,
            blocksize=int(self.sample_rate * 0.1),
        ):
            while True:
                time.sleep(0.05)
                elapsed = time.time() - start_time
                if elapsed > self.max_duration:
                    break
                if (
                    speech_detected
                    and silence_start is not None
                    and (time.time() - silence_start) > self.silence_duration
                ):
                    break

        if not frames or not speech_detected:
            return None

        audio = np.concatenate(frames, axis=0).flatten()
        duration = len(audio) / self.sample_rate
        if duration < self.min_speech:
            return None
        return audio


# ════════════════════════════════════════════════════════════════════
#  TTS factory
# ════════════════════════════════════════════════════════════════════

def make_tts(args):
    """Create TTS backend from CLI args."""
    if args.tts == "voicebox":
        vb = VoiceboxTTS(
            base_url=args.voicebox_url,
            profile_id=args.voicebox_profile,
            engine=args.voicebox_engine,
            model_size=args.voicebox_model_size,
            max_chunk_chars=args.voicebox_chunk,
            normalize=False,
            use_streaming=not args.voicebox_no_stream,
            instruct=args.voicebox_instruct,
        )
        if vb.ping():
            log.info("Voicebox connected at %s (engine=%s, model=%s)",
                     args.voicebox_url, args.voicebox_engine, args.voicebox_model_size)
            return vb
        else:
            log.warning("Voicebox not reachable at %s — falling back to edge-tts",
                        args.voicebox_url)
            return EdgeTTS(voice=args.edge_voice)
    else:
        return EdgeTTS(voice=args.edge_voice)


# ════════════════════════════════════════════════════════════════════
#  Pipelines
# ════════════════════════════════════════════════════════════════════

class VoicePipeline:
    """Full loop: listen → retrieve memory → generate → speak."""

    def __init__(
        self,
        inference_engine,
        memory_bridge,
        tts,
        whisper_model: str = "base",
        ingest_conversations: bool = True,
    ):
        self.engine = inference_engine
        self.bridge = memory_bridge
        self.tts = tts
        self.stt = WhisperSTT(model_size=whisper_model)
        self.recorder = AudioRecorder()
        self.ingest_conversations = ingest_conversations
        self.step = 0

    def load(self) -> None:
        self.engine.load()
        self.stt.load()
        log.info("Voice pipeline ready")

    def run_once(self) -> Optional[str]:
        """Run a single listen → respond cycle."""
        print("\n[Listening...] ", end="", flush=True)
        audio = self.recorder.record_utterance()
        if audio is None:
            print("(no speech detected)")
            return None

        print("[Transcribing...] ", end="", flush=True)
        user_text = self.stt.transcribe(audio)
        if not user_text:
            print("(empty transcription)")
            return None
        print(f"\nYou: {user_text}")

        preamble, memory_ctx = self.bridge.get_prompt_context(user_text)
        prompt = self.engine.format_prompt(
            user_input=user_text,
            memory_context=memory_ctx,
            character_preamble=preamble,
        )

        print("[Thinking...] ", end="", flush=True)
        response = self.engine.generate(
            prompt,
            stop_strings=["Human:", "\n\nHuman", "[Conversation]", "[Memory]"],
        )
        print(f"\nAgent: {response}")

        self.tts.speak(response)

        if self.ingest_conversations and self.bridge.ping():
            exchange = f"Human said: {user_text}\nAgent responded: {response}"
            self.bridge.ingest(exchange, step=self.step)
            self.step += 1

        return response

    def run_loop(self) -> None:
        print("=" * 60)
        print("TORMENT Live Agent — Voice Pipeline")
        print("Speak to interact. Press Ctrl+C to stop.")
        print("=" * 60)

        if self.bridge.ping():
            print(f"TORMENT memory: connected ({self.bridge.base_url})")
        else:
            print("TORMENT memory: offline (running without memory)")

        tts_name = type(self.tts).__name__
        print(f"TTS backend: {tts_name}")

        try:
            while True:
                self.run_once()
        except KeyboardInterrupt:
            print("\n\nStopping voice pipeline.")


class TextPipeline:
    """Text-only version for testing without a microphone."""

    def __init__(self, inference_engine, memory_bridge, tts=None, ingest: bool = True):
        self.engine = inference_engine
        self.bridge = memory_bridge
        self.tts = tts  # optional — if set, speaks responses too
        self.ingest = ingest
        self.step = 0

    def load(self) -> None:
        self.engine.load()

    def run_loop(self) -> None:
        print("=" * 60)
        print("TORMENT Live Agent — Text Mode")
        print("Type to interact. Type 'quit' to stop.")
        if self.tts:
            print(f"TTS: {type(self.tts).__name__} (responses will be spoken)")
        print("=" * 60)

        if self.bridge.ping():
            print(f"TORMENT memory: connected ({self.bridge.base_url})")
        else:
            print("TORMENT memory: offline (running without memory)")

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                break

            if user_input.lower() in ("quit", "exit", "q"):
                break
            if not user_input:
                continue

            preamble, memory_ctx = self.bridge.get_prompt_context(user_input)
            prompt = self.engine.format_prompt(
                user_input=user_input,
                memory_context=memory_ctx,
                character_preamble=preamble,
            )

            response = self.engine.generate(
                prompt,
                stop_strings=["Human:", "\n\nHuman", "[Conversation]", "[Memory]"],
            )
            print(f"Agent: {response}")

            if self.tts:
                self.tts.speak(response)

            if self.ingest and self.bridge.ping():
                exchange = f"Human said: {user_input}\nAgent responded: {response}"
                self.bridge.ingest(exchange, step=self.step)
                self.step += 1


# ════════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    parser = argparse.ArgumentParser(description="TORMENT Live Agent")

    # Mode
    parser.add_argument(
        "--mode", choices=["voice", "text"], default="text",
        help="Pipeline mode (default: text)"
    )

    # Inference engine
    parser.add_argument("--engine", choices=["claude", "qwen"], default="claude",
                        help="LLM engine: claude (API) or qwen (local). Default: claude")
    parser.add_argument("--model", default=None,
                        help="Model name/path (Claude model ID or Qwen model dir)")
    parser.add_argument("--device", default=None, help="Device for Qwen (cuda/cpu/auto)")
    parser.add_argument("--character-name", default=None,
                        help="Character name for Claude system prompt")

    # STT
    parser.add_argument("--whisper", default="base", help="Whisper model size")

    # TTS backend selection
    parser.add_argument(
        "--tts", choices=["voicebox", "edge"], default="voicebox",
        help="TTS backend (default: voicebox)"
    )

    # Voicebox options
    parser.add_argument("--voicebox-url", default=VOICEBOX_DEFAULT_URL,
                        help="Voicebox server URL")
    parser.add_argument("--voicebox-profile", default=None,
                        help="Voicebox voice profile ID")
    parser.add_argument("--voicebox-engine", default="qwen",
                        choices=["qwen", "luxtts", "chatterbox", "chatterbox_turbo"],
                        help="Voicebox TTS engine (default: qwen)")
    parser.add_argument("--voicebox-model-size", default="0.6B",
                        choices=["0.6B", "1.7B"],
                        help="Qwen TTS model size (default: 0.6B)")
    parser.add_argument("--voicebox-chunk", type=int, default=300,
                        help="Max chars per chunk (lower=faster, default: 300)")
    parser.add_argument("--voicebox-no-stream", action="store_true",
                        help="Use /generate instead of /generate/stream")
    parser.add_argument("--voicebox-instruct", default=None,
                        help="Qwen delivery instruction (e.g. 'speak calmly')")

    # Edge-tts options (fallback)
    parser.add_argument("--edge-voice", default="en-US-AriaNeural",
                        help="edge-tts voice name")

    # TORMENT
    parser.add_argument("--torment-url", default=None, help="TORMENT server URL")
    parser.add_argument("--workspace", default=None, help="TORMENT workspace ID")
    parser.add_argument("--agent", default=None, help="TORMENT agent ID")
    parser.add_argument("--no-ingest", action="store_true",
                        help="Don't write exchanges to memory")

    # Speak in text mode too
    parser.add_argument("--speak", action="store_true",
                        help="Also speak responses in text mode")

    args = parser.parse_args()

    from memory_bridge import MemoryBridge

    if args.engine == "claude":
        from inference import ClaudeInference
        char_name = args.character_name or args.agent or "Agent"
        engine = ClaudeInference(
            model=args.model,
            character_name=char_name,
        )
    else:
        from inference import QwenInference
        engine = QwenInference(model_path=args.model, device=args.device)
    bridge = MemoryBridge(
        base_url=args.torment_url,
        workspace_id=args.workspace,
        agent_id=args.agent,
    )
    tts = make_tts(args)

    if args.mode == "voice":
        pipeline = VoicePipeline(
            engine, bridge, tts,
            whisper_model=args.whisper,
            ingest_conversations=not args.no_ingest,
        )
    else:
        pipeline = TextPipeline(
            engine, bridge,
            tts=tts if args.speak else None,
            ingest=not args.no_ingest,
        )

    pipeline.load()
    pipeline.run_loop()
