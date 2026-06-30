#!/usr/bin/env node
/**
 * $HEAP token deploy via Clanker SDK (v4).
 *
 * Usage:
 *   node heap_token/deploy-sdk.mjs              # interactive
 *   node heap_token/deploy-sdk.mjs --key <pk>   # deploy with wallet key
 *   node heap_token/deploy-sdk.mjs --admin <addr> # use existing wallet
 *
 * Requires:
 *   - WALLET_PRIVATE_KEY env var or --key flag
 *   - npm packages: clanker-sdk, viem, dotenv
 */

import { execSync } from "child_process";
import { existsSync, readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

// ── Load .env ────────────────────────────────────────────────────────
const envPath = join(root, ".env");
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, "utf-8").split("\n")) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#") && trimmed.includes("=")) {
      const [key, ...rest] = trimmed.split("=");
      if (!process.env[key]) process.env[key] = rest.join("=");
    }
  }
}

// ── Config ───────────────────────────────────────────────────────────
const CONFIG = {
  name: "Agent Heap",
  symbol: "HEAP",
  description:
    "Multi-chain yield optimization AI agent token. Agent profits fuel automated buyback and burn.",
  image: process.env.HEAP_TOKEN_IMAGE || undefined,
  chain: "base",
  social: {
    website: process.env.HEAP_WEBSITE || "https://agentheap.ai",
    twitter: process.env.HEAP_TWITTER || "https://x.com/agentheap",
    telegram: process.env.HEAP_TELEGRAM || "https://t.me/agentheap",
  },
};

// ── Main ─────────────────────────────────────────────────────────────
async function main() {
  const privateKey = process.env.WALLET_PRIVATE_KEY || process.env.PRIVATE_KEY;

  if (!privateKey) {
    console.error("❌ Set WALLET_PRIVATE_KEY or PRIVATE_KEY in .env");
    process.exit(1);
  }

  // Dynamic import of viem + clanker-sdk
  const { createWalletClient, createPublicClient, http } = await import("viem");
  const { privateKeyToAccount } = await import("viem/accounts");
  const { base } = await import("viem/chains");
  const { Clanker } = await import("clanker-sdk/v4");

  const account = privateKeyToAccount(privateKey.startsWith("0x") ? privateKey : `0x${privateKey}`);

  const publicClient = createPublicClient({
    chain: base,
    transport: http(),
  });

  const walletClient = createWalletClient({
    chain: base,
    transport: http(),
    account,
  });

  console.log(`\n  Name:     ${CONFIG.name}`);
  console.log(`  Symbol:   $${CONFIG.symbol}`);
  console.log(`  Chain:    Base mainnet`);
  console.log(`  Deployer: ${account.address}\n`);

  const clanker = new Clanker({ publicClient, walletClient });

  const tokenConfig = {
    name: CONFIG.name,
    symbol: CONFIG.symbol,
    tokenAdmin: account.address,
    ...(CONFIG.image ? { image: CONFIG.image } : {}),
    metadata: {
      description: CONFIG.description,
      socialMediaUrls: [
        { platform: "website", url: CONFIG.social.website },
        { platform: "twitter", url: CONFIG.social.twitter },
        { platform: "telegram", url: CONFIG.social.telegram },
      ],
    },
    vault: {
      percentage: 10, // 10% to creator vault
      lockupDuration: 30 * 24 * 3600, // 30 days
      vestingDuration: 180 * 24 * 3600, // 6 month vest
      recipient: account.address,
    },
    devBuy: {
      ethAmount: 0.1, // 0.1 ETH dev buy
    },
    // Use standard pool (WETH pair, 10 ETH starting mcap)
    pool: undefined,
  };

  console.log("🚀 Deploying $HEAP via Clanker SDK v4...\n");

  const result = await clanker.deploy(tokenConfig);

  if (result.error) {
    console.error(`\n❌ Deploy failed:`, result.error);
    process.exit(1);
  }

  console.log(`✅ Transaction submitted: ${result.txHash}`);
  console.log(`⏳ Waiting for confirmation...`);

  const receipt = await result.waitForTransaction();

  console.log(`\n✅ $HEAP deployed!`);
  console.log(`   Address: ${receipt.address}`);
  console.log(`   Tx:      ${result.txHash}`);
  console.log(`   Base:    https://basescan.org/address/${receipt.address}\n`);

  console.log("Add to .env:");
  console.log(`  HEAP_TOKEN_ADDRESS=${receipt.address}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
