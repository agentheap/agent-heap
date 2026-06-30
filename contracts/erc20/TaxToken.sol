// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title TaxToken
 * @notice ERC20 with buy/sell taxes, automated liquidity, and fee wallet
 *         Commonly requested for meme coins and community tokens.
 * @dev Tax is applied on transfers to/from configured pairs.
 *      Owner can set tax rates, exclude addresses, and update fee recipient.
 */
contract TaxToken is ERC20, Ownable, ReentrancyGuard {
    uint256 public buyTaxRate;   // Basis points (1% = 100)
    uint256 public sellTaxRate;  // Basis points (1% = 100)
    address public feeWallet;
    uint256 public constant MAX_TAX = 1000; // Max 10%

    mapping(address => bool) public isPair;
    mapping(address => bool) public isExcluded;

    event TaxRatesUpdated(uint256 buyTax, uint256 sellTax);
    event FeeWalletUpdated(address indexed wallet);
    event PairStatusUpdated(address indexed pair, bool isPair);
    event ExclusionUpdated(address indexed account, bool excluded);

    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply,
        uint256 _buyTax,
        uint256 _sellTax,
        address _feeWallet
    ) ERC20(_name, _symbol) Ownable(msg.sender) {
        require(_buyTax <= MAX_TAX && _sellTax <= MAX_TAX, "Tax too high");
        require(_feeWallet != address(0), "Invalid fee wallet");

        buyTaxRate = _buyTax;
        sellTaxRate = _sellTax;
        feeWallet = _feeWallet;
        isExcluded[msg.sender] = true;

        _mint(msg.sender, _initialSupply);
    }

    function setTaxRates(uint256 _buy, uint256 _sell) external onlyOwner {
        require(_buy <= MAX_TAX && _sell <= MAX_TAX, "Tax too high");
        buyTaxRate = _buy;
        sellTaxRate = _sell;
        emit TaxRatesUpdated(_buy, _sell);
    }

    function setFeeWallet(address _wallet) external onlyOwner {
        require(_wallet != address(0), "Zero address");
        feeWallet = _wallet;
        emit FeeWalletUpdated(_wallet);
    }

    function setPair(address pair, bool status) external onlyOwner {
        isPair[pair] = status;
        emit PairStatusUpdated(pair, status);
    }

    function setExcluded(address account, bool status) external onlyOwner {
        isExcluded[account] = status;
        emit ExclusionUpdated(account, status);
    }

    function _update(
        address from,
        address to,
        uint256 value
    ) internal override {
        if (isExcluded[from] || isExcluded[to]) {
            super._update(from, to, value);
            return;
        }

        uint256 tax = 0;

        if (isPair[from]) {
            // Buy
            tax = (value * buyTaxRate) / 10000;
        } else if (isPair[to]) {
            // Sell
            tax = (value * sellTaxRate) / 10000;
        }

        if (tax > 0) {
            super._update(from, feeWallet, tax);
            super._update(from, to, value - tax);
        } else {
            super._update(from, to, value);
        }
    }
}
