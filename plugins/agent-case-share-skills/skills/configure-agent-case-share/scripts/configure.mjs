#!/usr/bin/env node

import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";

const DEFAULT_BASE_URL = "https://agentcaseshare.cn/";
const MCP_SERVER_NAME = "agent-case-share";
const MCP_URL = "https://mcp.agentcaseshare.cn/mcp";
const MCP_BEARER_ENV_VAR = "AGENT_CASE_SHARE_API_KEY";

function usage() {
  console.log(`Usage: node configure.mjs [options]

Options:
  --status                 Show whether configuration exists without revealing the API key.
  --clear                  Delete the saved configuration.
  --api-key <key>          Set the API key non-interactively (for automation only).
  --no-mcp                 Save credentials without registering the Codex MCP server.
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

function parseArgs(args) {
  const options = { status: false, clear: false, apiKey: undefined, noMcp: false };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--status") {
      options.status = true;
    } else if (arg === "--clear") {
      options.clear = true;
    } else if (arg === "--api-key") {
      const value = args[index + 1];
      if (!value || value.startsWith("--")) {
        throw new Error(`${arg} requires a value.`);
      }
      options.apiKey = value;
      index += 1;
    } else if (arg === "--no-mcp") {
      options.noMcp = true;
    } else if (arg === "--help" || arg === "-h") {
      options.help = true;
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }

  if ([options.status, options.clear].filter(Boolean).length > 1 || ((options.status || options.clear) && (options.apiKey || options.noMcp))) {
    throw new Error("--status and --clear cannot be combined with other options.");
  }

  return options;
}

async function readConfig(filePath) {
  try {
    const parsed = JSON.parse(await readFile(filePath, "utf8"));
    return {
      apiKey: typeof parsed.apiKey === "string" ? parsed.apiKey.trim() : "",
      baseUrl: DEFAULT_BASE_URL,
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

function codexHomePath() {
  return process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
}

function codexConfigPath() {
  return path.join(codexHomePath(), "config.toml");
}

function hasCodexConfig() {
  return Boolean(process.env.CODEX_HOME) || existsSync(codexConfigPath());
}

function runCodex(args) {
  if (process.platform === "win32") {
    // Windows exposes the npm-installed Codex launcher as a .cmd file.
    return spawnSync("cmd.exe", ["/d", "/s", "/c", ["codex.cmd", ...args].join(" ")], {
      encoding: "utf8",
      windowsHide: true,
    });
  }

  return spawnSync("codex", args, { encoding: "utf8" });
}

function codexMcpRegistration() {
  if (!hasCodexConfig()) {
    return { status: "skipped", reason: "Codex configuration was not detected." };
  }

  const result = runCodex([
    "mcp",
    "add",
    MCP_SERVER_NAME,
    "--url",
    MCP_URL,
    "--bearer-token-env-var",
    MCP_BEARER_ENV_VAR,
  ]);

  if (result.error?.code === "ENOENT") {
    return { status: "skipped", reason: "Codex CLI was not found." };
  }
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || "").trim();
    return { status: "failed", reason: detail || `Codex exited with status ${result.status}.` };
  }

  return { status: "registered", path: codexConfigPath() };
}

function codexMcpStatus() {
  if (!hasCodexConfig()) {
    return "not detected";
  }

  const result = runCodex(["mcp", "list"]);
  if (result.status !== 0) {
    return "unavailable";
  }

  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  const hasServer = output.includes(MCP_SERVER_NAME) && output.includes(MCP_URL);
  if (!hasServer) {
    return "not configured";
  }

  return output.includes(MCP_BEARER_ENV_VAR) ? "configured" : "missing bearer token configuration";
}

function setWindowsUserEnvironmentVariable(value) {
  if (process.platform !== "win32") {
    return { status: "skipped", reason: "Automatic persistent environment setup is currently supported on Windows only." };
  }

  const command = "$value = [Console]::In.ReadToEnd(); [Environment]::SetEnvironmentVariable('AGENT_CASE_SHARE_API_KEY', $value, 'User')";
  try {
    execFileSync("powershell.exe", ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command], {
      input: value,
      encoding: "utf8",
      windowsHide: true,
      stdio: ["pipe", "ignore", "pipe"],
    });
    process.env[MCP_BEARER_ENV_VAR] = value;
    return { status: "set" };
  } catch (error) {
    const detail = error.stderr?.toString().trim();
    return { status: "failed", reason: detail || error.message };
  }
}

function hasWindowsUserEnvironmentVariable() {
  if (process.platform !== "win32") {
    return Boolean(process.env[MCP_BEARER_ENV_VAR]);
  }

  try {
    const value = execFileSync(
      "powershell.exe",
      ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "[Environment]::GetEnvironmentVariable('AGENT_CASE_SHARE_API_KEY', 'User')"],
      { encoding: "utf8", windowsHide: true },
    ).trim();
    return Boolean(value);
  } catch {
    return false;
  }
}

function clearWindowsUserEnvironmentVariable() {
  if (process.platform !== "win32") {
    return { status: "skipped" };
  }

  try {
    execFileSync(
      "powershell.exe",
      ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "[Environment]::SetEnvironmentVariable('AGENT_CASE_SHARE_API_KEY', $null, 'User')"],
      { encoding: "utf8", windowsHide: true, stdio: ["ignore", "ignore", "pipe"] },
    );
    delete process.env[MCP_BEARER_ENV_VAR];
    return { status: "cleared" };
  } catch (error) {
    const detail = error.stderr?.toString().trim();
    return { status: "failed", reason: detail || error.message };
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
    console.log(`MCP bearer environment: ${hasWindowsUserEnvironmentVariable() ? "configured" : "not configured"}`);
    console.log(`Codex MCP registration: ${codexMcpStatus()}`);
    console.log(`Codex MCP config: ${codexConfigPath()}`);
    return;
  }

  if (options.clear) {
    await rm(filePath, { force: true });
    const environment = clearWindowsUserEnvironmentVariable();
    if (environment.status === "failed") {
      throw new Error(`Could not clear the MCP bearer environment: ${environment.reason}`);
    }
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

  await writeConfig(filePath, { apiKey, baseUrl: DEFAULT_BASE_URL });
  console.log(`Agent Case Share configured. Config file: ${filePath}`);

  if (options.noMcp) {
    console.log("MCP registration skipped (--no-mcp).");
    return;
  }

  const environment = setWindowsUserEnvironmentVariable(apiKey);
  if (environment.status === "failed") {
    throw new Error(`Credentials were saved, but the MCP bearer environment could not be configured: ${environment.reason}`);
  }
  if (environment.status === "skipped") {
    console.log(`MCP bearer environment was not configured: ${environment.reason}`);
  }

  const registration = codexMcpRegistration();
  if (registration.status === "registered") {
    console.log(`Codex MCP server registered in ${registration.path}.`);
    console.log("Restart Codex so it can load the new MCP server and environment variable.");
  } else if (registration.status === "failed") {
    throw new Error(`Credentials were saved, but Codex MCP registration failed: ${registration.reason}`);
  } else {
    console.log(`Codex MCP registration skipped: ${registration.reason}`);
  }
}

main().catch((error) => {
  console.error(`Configuration failed: ${error.message}`);
  process.exitCode = 1;
});
