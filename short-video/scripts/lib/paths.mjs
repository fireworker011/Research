import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
export const PUBLIC_DIR = path.join(ROOT, 'public');
export const AUDIO_DIR = path.join(PUBLIC_DIR, 'audio');
export const MEDIA_DIR = path.join(PUBLIC_DIR, 'media');
export const BGM_DIR = path.join(PUBLIC_DIR, 'bgm');
export const FONT_DIR = path.join(PUBLIC_DIR, 'fonts');
export const OUT_DIR = path.join(ROOT, 'out');
export const SCRIPT_PATH = path.join(ROOT, 'script.json');

export const ensureDir = (dir) => fs.mkdirSync(dir, { recursive: true });
export const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));
export const writeJson = (p, data) => fs.writeFileSync(p, JSON.stringify(data, null, 2) + '\n');
export const loadScript = () => readJson(SCRIPT_PATH);

export const sceneId = (index) => String(index).padStart(2, '0');
