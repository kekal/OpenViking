# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Claude Code CLI VLM Provider — uses the local `claude` binary instead of API calls."""

import asyncio
import ctypes
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

from ..base import VLMBase

logger = logging.getLogger(__name__)

# --- Windows Job Object helpers to enforce low priority on entire process tree ---

_job_handle = None

if sys.platform == "win32":
    import ctypes.wintypes

    _kernel32 = ctypes.windll.kernel32

    # Job Object constants
    _JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
    _IDLE_PRIORITY_CLASS = 0x00000040
    _JobObjectExtendedLimitInformation = 9

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.wintypes.DWORD),
            ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
            ("PriorityClass", ctypes.wintypes.DWORD),
            ("SchedulingClass", ctypes.wintypes.DWORD),
        ]

    class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    def _create_low_priority_job():
        """Create a Windows Job Object that forces all processes in it to IDLE priority."""
        global _job_handle
        if _job_handle is not None:
            return _job_handle

        try:
            handle = _kernel32.CreateJobObjectW(None, None)
            if not handle:
                logger.warning("[ClaudeCodeVLM] Failed to create Job Object")
                return None

            info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_PRIORITY_CLASS
            info.BasicLimitInformation.PriorityClass = _IDLE_PRIORITY_CLASS

            success = _kernel32.SetInformationJobObject(
                handle,
                _JobObjectExtendedLimitInformation,
                ctypes.byref(info),
                ctypes.sizeof(info),
            )
            if not success:
                logger.warning("[ClaudeCodeVLM] Failed to set Job Object priority")
                _kernel32.CloseHandle(handle)
                return None

            _job_handle = handle
            return handle
        except Exception as e:
            logger.warning(f"[ClaudeCodeVLM] Job Object creation failed: {e}")
            return None

    def _assign_process_to_job(pid: int):
        """Assign a process (by PID) to the low-priority Job Object."""
        job = _create_low_priority_job()
        if not job:
            return
        try:
            PROCESS_ALL_ACCESS = 0x1FFFFF
            proc_handle = _kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if proc_handle:
                _kernel32.AssignProcessToJobObject(job, proc_handle)
                _kernel32.CloseHandle(proc_handle)
        except Exception as e:
            logger.warning(f"[ClaudeCodeVLM] Failed to assign PID {pid} to job: {e}")

else:
    def _assign_process_to_job(pid: int):
        """No-op on non-Windows."""
        pass


_IDLE_FLAGS = subprocess.IDLE_PRIORITY_CLASS if sys.platform == "win32" else 0


class ClaudeCodeVLM(VLMBase):
    """
    VLM implementation that shells out to the local `claude` CLI.

    Uses the user's existing Claude Code subscription (OAuth) —
    no API key required.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get("model", "claude-sonnet-4-6")
        self._timeout = config.get("timeout", 120)
        # Resolve claude path once
        self._claude_path = shutil.which("claude") or "claude"

    def _build_cmd(self) -> list[str]:
        """Build the command line for claude CLI."""
        cmd = [
            self._claude_path,
            "-p",
            "--bare",
            "--no-session-persistence",
            "--output-format", "json",
            "--model", self.model,
            "--tools", "",
        ]
        return cmd

    def _parse_response(self, raw: str) -> str:
        """Parse JSON response from claude CLI."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"[ClaudeCodeVLM] Failed to parse JSON, returning raw output")
            return raw.strip()

        if data.get("is_error"):
            error_msg = data.get("result", "Unknown error from claude CLI")
            raise RuntimeError(f"Claude CLI error: {error_msg}")

        result = data.get("result", "")

        # Update token usage if available
        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_create = usage.get("cache_creation_input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        self.update_token_usage(
            model_name=self.model,
            provider="claude-code",
            prompt_tokens=prompt_tokens + cache_read + cache_create,
            completion_tokens=completion_tokens,
        )

        return self._clean_response(result)

    def _run_claude(self, prompt: str) -> str:
        """Run claude CLI synchronously with low priority on entire process tree."""
        cmd = self._build_cmd()
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=_IDLE_FLAGS,
            )
            # Assign to Job Object so ALL child processes get low priority
            _assign_process_to_job(proc.pid)

            try:
                stdout, stderr = proc.communicate(input=prompt, timeout=self._timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise RuntimeError(f"Claude CLI timed out after {self._timeout}s")

        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Make sure 'claude' is in your PATH."
            )

        output = stdout.strip()
        if not output and stderr:
            raise RuntimeError(f"Claude CLI error: {stderr.strip()}")
        if not output:
            raise RuntimeError(f"Claude CLI returned no output (exit code {proc.returncode})")

        return output

    async def _run_claude_async(self, prompt: str) -> str:
        """Run claude CLI asynchronously with low priority on entire process tree."""
        cmd = self._build_cmd()
        try:
            kwargs = dict(
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            if sys.platform == "win32":
                kwargs["creationflags"] = _IDLE_FLAGS

            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(*cmd, **kwargs),
                timeout=self._timeout,
            )
            # Assign to Job Object so ALL child processes get low priority
            _assign_process_to_job(proc.pid)

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Claude CLI timed out after {self._timeout}s")

        output = stdout.decode().strip()
        if not output and stderr:
            raise RuntimeError(f"Claude CLI error: {stderr.decode().strip()}")
        if not output:
            raise RuntimeError(f"Claude CLI returned no output (exit code {proc.returncode})")

        return output

    def get_completion(self, prompt: str, thinking: bool = False) -> str:
        """Get text completion via claude CLI."""
        raw = self._run_claude(prompt)
        return self._parse_response(raw)

    async def get_completion_async(
        self, prompt: str, thinking: bool = False, max_retries: int = 0
    ) -> str:
        """Get text completion asynchronously via claude CLI."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                raw = await self._run_claude_async(prompt)
                return self._parse_response(raw)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)

        if last_error:
            raise last_error
        raise RuntimeError("Unknown error in async completion")

    def get_vision_completion(
        self,
        prompt: str,
        images: List[Union[str, Path, bytes]],
        thinking: bool = False,
    ) -> str:
        """Get vision completion — delegates to text completion (images not supported via CLI)."""
        logger.warning(
            "[ClaudeCodeVLM] Vision not supported via CLI, falling back to text-only"
        )
        return self.get_completion(prompt, thinking)

    async def get_vision_completion_async(
        self,
        prompt: str,
        images: List[Union[str, Path, bytes]],
        thinking: bool = False,
    ) -> str:
        """Async vision completion — delegates to text completion."""
        logger.warning(
            "[ClaudeCodeVLM] Vision not supported via CLI, falling back to text-only"
        )
        return await self.get_completion_async(prompt, thinking)

    def is_available(self) -> bool:
        """Check if claude CLI is available."""
        try:
            proc = subprocess.run(
                [self._claude_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return proc.returncode == 0
        except Exception:
            return False
