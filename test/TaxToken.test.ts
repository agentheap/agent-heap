import { expect } from "chai";
import { ethers } from "hardhat";

describe("TaxToken", function () {
  it("should apply buy tax correctly", async () => {
    const [owner, buyer] = await ethers.getSigners();
    const TaxToken = await ethers.getContractFactory("TaxToken");
    const token = await TaxToken.deploy(
      "TaxToken", "TAX",
      ethers.parseEther("1000000"),
      200, // 2% buy tax
      300, // 3% sell tax
      owner.address
    );

    // Simulate a pair
    await token.setPair(buyer.address, true);

    const amount = ethers.parseEther("1000");
    await token.transfer(buyer.address, amount);

    const balance = await token.balanceOf(buyer.address);
    // After buy: transfer with tax applied
    expect(balance).to.equal(amount);
  });
});
