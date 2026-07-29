import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setPixelFormat('yuv420p'); // SNS 各社のプレイヤー互換
Config.setCodec('h264');
Config.setCrf(20);
Config.setChromiumOpenGlRenderer('swangle'); // GPU なしの環境でも安定して回す
Config.setOverwriteOutput(true);
