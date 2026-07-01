# Deployment Guide

## Prerequisites

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your PRIVATE_KEY and RPC URLs
```

## Local Test Deployment

```bash
# Start local Hardhat node
npx hardhat node

# Deploy contracts to local node
npx hardhat run scripts/deploy.js --network localhost
```

## Testnet Deployment (Base Sepolia)

```bash
# Ensure .env has:
#   PRIVATE_KEY=0x...
#   BASE_SEPOLIA_RPC=https://sepolia.base.org
#   BASESCAN_API_KEY=...

# Deploy
npx hardhat run scripts/deploy.js --network base_sepolia

# Verify on BaseScan
npx hardhat verify --network base_sepolia <DEPLOYED_ADDRESS> <CONSTRUCTOR_ARGS...>
```

## Networks Supported

| Network | RPC | Explorer | Faucet |
|---------|-----|----------|--------|
| Ethereum Sepolia | Infura/Alchemy | etherscan.io | sepoliafaucet.com |
| Base Sepolia | base.org | basescan.org | base.org/faucet |
| Polygon Amoy | polygon-rpc.com | polygonscan.com | faucet.polygon.technology |
| BSC Testnet | binance.org | testnet.bscscan.com | testnet.bnbchain.org/faucet-smart |

## Deploy Script Customization

Edit `scripts/deploy.js` to select which contract to deploy:

```javascript
// For SimpleToken
const Token = await hre.ethers.getContractFactory("SimpleToken");
const token = await Token.deploy("MyToken", "MTK", ethers.parseEther("1000000"));

// For TaxToken
const TaxToken = await hre.ethers.getContractFactory("TaxToken");
const taxToken = await TaxToken.deploy("TaxToken", "TX", ethers.parseEther("1000000"));

// For SimpleNFT
const NFT = await hre.ethers.getContractFactory("SimpleNFT");
const nft = await NFT.deploy("MyNFT", "MNFT", "https://base-uri.example.com/");

// For SimpleStaking
const Staking = await hre.ethers.getContractFactory("SimpleStaking");
const staking = await Staking.deploy();
```

## Client Deliverables Checklist

When delivering to a client, provide:
- [ ] Source contract (flattened or linked)
- [ ] ABI JSON
- [ ] Deployment transaction hash
- [ ] Verified contract link on block explorer
- [ ] Simple interaction script
- [ ] Brief usage documentation
