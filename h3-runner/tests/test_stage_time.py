"""The denoiser timer must keep the forward parameter names. No GPU."""

from __future__ import annotations

import functools
import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from h3_runner.stage_time import attach_forward_timer  # noqa: E402

_LAYOUT = ("token_tags", "position_ids", "video_indices", "audio_indices", "text_indices")


class _Denoiser:
    def forward(
        self,
        hidden_states,
        audio_hidden_states,
        encoder_hidden_states,
        timestep,
        timestep_indices,
        token_tags,
        position_ids,
        video_indices,
        audio_indices,
        text_indices,
        attention_kwargs=None,
        return_dict=True,
    ):
        return token_tags, text_indices


def _layout_kwargs(forward):
    fields = {name: name for name in (*_LAYOUT, "not_a_forward_arg")}
    return {name: value for name, value in fields.items() if name in inspect.signature(forward).parameters}


class StageTimerSignatureTest(unittest.TestCase):
    def test_wrapped_forward_still_lists_the_layout_tensors(self) -> None:
        module = _Denoiser()
        totals = {"denoise": 0.0}
        attach_forward_timer(module, totals, "denoise", lambda: None)
        kept = _layout_kwargs(module.forward)
        self.assertEqual(set(kept), set(_LAYOUT))
        self.assertEqual(module.forward(1, 2, 3, 4, 5, "tags", "pos", "v", "a", "t"), ("tags", "t"))
        self.assertGreaterEqual(totals["denoise"], 0.0)

    def test_wrapper_follows_an_offload_hook_back_to_the_real_names(self) -> None:
        module = _Denoiser()
        real = module.forward

        def hooked(bound, *args, **kwargs):
            return bound._old_forward(*args, **kwargs)

        module._old_forward = real
        module.forward = functools.update_wrapper(functools.partial(hooked, module), real)
        totals = {"denoise": 0.0}
        attach_forward_timer(module, totals, "denoise", lambda: None)
        self.assertEqual(set(_layout_kwargs(module.forward)), set(_LAYOUT))
        self.assertEqual(module.forward(1, 2, 3, 4, 5, "tags", "pos", "v", "a", "t"), ("tags", "t"))


if __name__ == "__main__":
    unittest.main()
