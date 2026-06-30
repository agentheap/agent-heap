const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with:", deployer.address);

  // Example: Deploy SimpleToken
  const Token = await hre.ethers.getContractFactory("SimpleToken");
  const token = await Token.deploy("MyToken", "MTK", hre.ethers.parseEther("1000000"));
  await token.waitForDeployment();

  console.log("SimpleToken deployed to:", await token.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
