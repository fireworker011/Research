"""
scene動画を結合してテロップ・音声を合成する

使い方:
  assembler = VideoAssembler()
  output = assembler.assemble(script, scenes_dir="output/videos/scenes/project_xxx")
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class VideoAssembler:
    """FFmpeg で scene動画を結合しテロップを焼き込む"""

    FONT_COLOR = "white"
    BORDER_COLOR = "black"
    FONT_SIZE = 55
    BORDER_WIDTH = 3

    def assemble(
        self,
        script: dict,
        scenes_dir: str,
        bgm_path: str | None = None,
        out_path: str | None = None,
    ) -> Path:
        """
        Args:
            script: ScriptGenerator が返す dict
            scenes_dir: scene01.mp4〜scene07.mp4 が入ったフォルダ
            bgm_path: BGM ファイルパス（省略時は音声なし）
            out_path: 出力先（省略時は output/videos/{project_id}.mp4）

        Returns:
            完成動画のパス
        """
        scenes = script.get("scenes", [])
        project_id = script.get("project_id", "project")
        scenes_dir = Path(scenes_dir)

        # 出力先
        if out_path:
            final_path = Path(out_path)
        else:
            out_dir = Path("output/videos")
            out_dir.mkdir(parents=True, exist_ok=True)
            final_path = out_dir / f"{project_id}_final.mp4"

        # scene動画パスを収集
        scene_paths = self._collect_scene_paths(scenes_dir, len(scenes))

        # 一時ディレクトリで作業
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)

            # Step1: 各sceneを5秒にトリム・リサイズ
            trimmed = []
            for i, sp in enumerate(scene_paths, 1):
                out = tmp / f"trimmed_{i:02d}.mp4"
                self._trim_resize(sp, out)
                trimmed.append(out)

            # Step2: concat
            concat_path = tmp / "concat.mp4"
            self._concat(trimmed, concat_path)

            # Step3: テロップ焼き込み
            telopped_path = tmp / "telopped.mp4"
            self._burn_subtitles(concat_path, scenes, telopped_path)

            # Step4: BGMミックス（省略可）
            if bgm_path and Path(bgm_path).exists():
                mixed_path = tmp / "mixed.mp4"
                self._mix_audio(telopped_path, bgm_path, mixed_path)
                final_src = mixed_path
            else:
                final_src = telopped_path

            # 最終出力
            import shutil
            shutil.copy2(final_src, final_path)

        print(f"✅ 完成: {final_path}")
        return final_path

    # ─────────────────────────────────────────────────────
    # 内部メソッド
    # ─────────────────────────────────────────────────────

    def _collect_scene_paths(self, scenes_dir: Path, n_scenes: int) -> list[Path]:
        paths = []
        for i in range(1, n_scenes + 1):
            p = scenes_dir / f"scene{i:02d}.mp4"
            if not p.exists():
                raise FileNotFoundError(
                    f"{p} が見つかりません。\n"
                    f"Grok で生成した動画を {scenes_dir}/ に scene01.mp4〜scene{n_scenes:02d}.mp4 として保存してください。"
                )
            paths.append(p)
        return paths

    def _trim_resize(self, src: Path, dst: Path):
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-t", "5",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                   "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",  # 音声はあとで処理
            str(dst),
        ]
        _run(cmd)

    def _concat(self, paths: list[Path], dst: Path):
        list_file = dst.parent / "concat_list.txt"
        list_file.write_text(
            "\n".join(f"file '{p}'" for p in paths), encoding="utf-8"
        )
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(dst),
        ]
        _run(cmd)

    def _burn_subtitles(self, src: Path, scenes: list[dict], dst: Path):
        filters = []
        for i, scene in enumerate(scenes):
            text = scene.get("subtitle", scene.get("テロップ", ""))
            if not text:
                continue
            start = i * 5
            end = (i + 1) * 5
            safe_text = text.replace("'", "\\'").replace(":", "\\:")
            filters.append(
                f"drawtext=text='{safe_text}'"
                f":fontcolor={self.FONT_COLOR}"
                f":fontsize={self.FONT_SIZE}"
                f":borderw={self.BORDER_WIDTH}"
                f":bordercolor={self.BORDER_COLOR}"
                f":x=(w-text_w)/2"
                f":y=h-180"
                f":enable='between(t,{start},{end})'"
            )

        if not filters:
            import shutil
            shutil.copy2(src, dst)
            return

        vf = ",".join(filters)
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            str(dst),
        ]
        _run(cmd)

    def _mix_audio(self, video: Path, bgm: Path, dst: Path):
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-i", str(bgm),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=first:weights=1 0.3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac",
            str(dst),
        ]
        _run(cmd)


def _run(cmd: list[str]):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg エラー:\n{result.stderr[-1000:]}")
