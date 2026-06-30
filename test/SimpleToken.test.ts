import { expect } from "chai";
import { ethers } from "hardhat";

describe("SimpleToken", function () {
  it("should deploy with correct name, symbol, and supply", async () => {
    const Token = await ethers.getContractFactory("SimpleToken");
    const token = await Token.deploy("TestToken", "TST", ethers.parseEther("1000000"));

    expect(await token.name()).to.equal("TestToken");
    expect(await token.symbol()).to.equal("TST");
    expect(await token.totalSupply()).to.equal(ethers.parseEther("1000000"));
  });

  it("should allow owner to mint tokens", async () => {
    const [owner, addr1] = await ethers.getSigners();
    const Token = await ethers.getContractFactory("SimpleToken");
    const token = await Token.deploy("TestToken", "TST", ethers.parseEther("1000"));

    await token.mint(addr1.address, ethers.parseEther("500"));
    expect(await token.balanceOf(addr1.address)).to.equal(ethers.parseEther("500"));
  });

  it("should not allow non-owner to mint", async () => {
    const [_, addr1] = await ethers.getSigners();
    const Token = await ethers.getContractFactory("SimpleToken");
    const token = await Token.deploy("TestToken", "TST", ethers.parseEther("1000"));

    await expect(
      token.connect(addr1).mint(addr1.address, ethers.parseEther("500"))
    ).to.be.revertedWithCustomError(token, "OwnableUnauthorizedAccount");
  });
});
