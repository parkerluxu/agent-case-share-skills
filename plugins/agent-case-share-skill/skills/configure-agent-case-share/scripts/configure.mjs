#!/usr/bin/env node

import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import readline from "node:readline/promises";

const DEFAULT_BASE_URL = "https://agentcaseshare.cn/";

function usage() {
  console.log(`Usage: node configure.mjs [options]

Options:
  --status                 Show whether configuration exists without revealing the API key.
  --clear                  Delete the saved configuration.
  --api-key <key>          Set the API key non-interactively (for automation only).
  --base-url <url>         Set a custom Agent Case Share base URL.
  --help                   Show this help message.`);
}

function configPath() {
  if (process.platform === "win32") {
    return path.join(process.env.APPDATA || path.join(os.homedir(), "AppData", "Roaming"), "agent-case-share", "config.json");
  }

  if (process.platform === "darwin") {
    return path.join(os.homedir(), "Library", "Application Support", "agent-case-share", "config.json");
  }

  return path.join(process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config"), "agent-case-share", "config.json");
}

function normalizeBaseUrl(value) {
  const candidate = (value || DEFAULT_BASE_URL).trim();
  let url;

  try {
    url = new URL(candidate);
  } catch {
    throw new Error("Base URL must be a valid http or https URL.");
  }

  if (url.protocol !== "https:" && url.protocol !== "http:") {
    throw new Error("Base URL must use http or https.");
  }

  return url.toString();
}

function parseArgs(args) {
  const options = { status: false, clear: false, apiKey: undefined, baseUrl: undefined };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--status") {
      options.status = true;
    } else if (arg === "--clear") {
      options.clear = true;
    } else if (arg === "--api-key" || arg === "--base-url") {
      const value = args[index + 1];
      if (!value || value.startsWith("--")) {
        throw new Error(`${arg} requires a value.`);
      }
      options[arg === "--api-key" ? "apiKey" : "baseUrl"] = value;
      index += 1;
    } else if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }

  if ([options.status, options.clear].filter(Boolean).length > 1 || ((options.status || options.clear) && (options.apiKey || options.baseUrl))) {
    throw new Error("--status and --clear cannot be combined with other options.");
  }

  return options;
}

async function readConfig(filePath) {
  try {
    const parsed = JSON.parse(await readFile(filePath, "utf8"));
    return {
      apiKey: typeof parsed.apiKey === "string" ? parsed.apiKey.trim() : "",
      baseUrl: typeof parsed.baseUrl === "string" ? normalizeBaseUrl(parsed.baseUrl) : DEFAULT_BASE_URL,
    };
  } catch (error) {
    if (error.code === "ENOENT") {
      return null;
    }
    if (error instanceof SyntaxError) {
      throw new Error(`Saved configuration is not valid JSON: ${filePath}`);
    }
    throw error;
  }
}

async function promptSecret(message) {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    throw new Error("An interactive terminal is required. Use --api-key only in trusted automation.");
  }

  return new Promise((resolve, reject) => {
    let value = "";
    const input = process.stdin;
    input.setEncoding("utf8");
    input.setRawMode(true);
    input.resume();
    process.stdout.write(message);

    const finish = (error) => {
      input.setRawMode(false);
      input.pause();
      input.removeListener("data", onData);
      process.stdout.write("\n");
      if (error) {
        reject(error);
      } else {
        resolve(value);
      }
    };

    const onData = (chunk) => {
      for (const character of chunk) {
        if (character === "\u0003") {
          finish(new Error("Configuration cancelled."));
          return;
        }
        if (character === "\r" || character === "\n") {
          finish();
          return;
        }
        if (character === "\u0008" || character === "\u007f") {
          value = value.slice(0, -1);
          continue;
        }
        if (character >= " ") {
          value += character;
        }
      }
    };

    input.on("data", onData);
  });
}

async function promptBaseUrl(defaultValue) {
  const terminal = readline.createInterface({ input: process.stdin, output: process.stdout });
  try {
    const answer = await terminal.question(`Base URL [${defaultValue}]: `);
    return answer.trim() || defaultValue;
  } finally {
    terminal.close();
  }
}

async function writeConfig(filePath, config) {
  const directory = path.dirname(filePath);
  await mkdir(directory, { recursive: true, mode: 0o700 });
  const temporaryPath = path.join(directory, `.config-${process.pid}-${Date.now()}.tmp`);
  const payload = `${JSON.stringify(config, null, 2)}\n`;

  try {
    await writeFile(temporaryPath, payload, { encoding: "utf8", mode: 0o600 });
    await rename(temporaryPath, filePath);
  } finally {
    await rm(temporaryPath, { force: true });
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    usage();
    return;
  }

  const filePath = configPath();
  if (options.status) {
    const config = await readConfig(filePath);
    if (!config?.apiKey) {
      console.log("Agent Case Share is not configured.");
      return;
    }
    console.log("Agent Case Share is configured.");
    console.log(`Config file: ${filePath}`);
    console.log(`Base URL: ${config.baseUrl}`);
    return;
  }

  if (options.clear) {
    await rm(filePath, { force: true });
    console.log("Agent Case Share configuration cleared.");
    return;
  }

  const existing = await readConfig(filePath);
  let apiKey = options.apiKey?.trim();
  if (!apiKey) {
    const prompt = existing?.apiKey ? "API key (leave blank to keep the saved key): " : "API key: ";
    apiKey = (await promptSecret(prompt)).trim() || existing?.apiKey;
  }
  if (!apiKey) {
    throw new Error("An API key is required.");
  }

  const defaultBaseUrl = existing?.baseUrl || DEFAULT_BASE_URL;
  const baseUrlInput = options.baseUrl || (process.stdin.isTTY && process.stdout.isTTY
    ? await promptBaseUrl(defaultBaseUrl)
    : defaultBaseUrl);
  const baseUrl = normalizeBaseUrl(baseUrlInput);
  await writeConfig(filePath, { apiKey, baseUrl });
  console.log(`Agent Case Share configured. Config file: ${filePath}`);
}

main().catch((error) => {
  console.error(`Configuration failed: ${error.message}`);
  process.exitCode = 1;
});
