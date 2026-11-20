import { Config } from "@remotion/cli/config";

Config.setEntryPoint("src/index.ts");
Config.setOverwriteOutput(true);
Config.setBrowserExecutable("/usr/bin/google-chrome-stable");
