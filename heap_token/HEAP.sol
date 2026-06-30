// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/// @title HEAP Token — self-contained ERC20
/// @notice Agent Heap ecosystem token with buyback and burn support.
///         No external dependencies — compiles standalone.
contract HEAP {
    // ── ERC20 state ────────────────────────────────────────────
    string public constant name = "Agent Heap";
    string public constant symbol = "HEAP";
    uint8 public constant decimals = 18;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // ── Ownable state ──────────────────────────────────────────
    address public owner;
    address public pendingOwner;

    // ── Buyback state ──────────────────────────────────────────
    bool public buybackEnabled;
    uint256 public totalBurned;
    uint256 public constant MAX_BUYBACK_BPS = 500; // 5% max per tx

    // ── Events ─────────────────────────────────────────────────
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner_, address indexed spender, uint256 value);
    event OwnershipTransferStarted(address indexed from, address indexed to);
    event OwnershipTransferred(address indexed from, address indexed to);
    event BuybackExecuted(uint256 amount, uint256 ethSpent);
    event TokensBurned(uint256 amount);

    // ── Errors ─────────────────────────────────────────────────
    error Unauthorized();
    error InsufficientBalance();
    error InsufficientAllowance();
    error InvalidRecipient();
    error BuybackDisabled();

    // ── Constructor ────────────────────────────────────────────
    constructor(address _admin, bool _mintInitialSupply) {
        owner = _admin;
        if (_mintInitialSupply) {
            uint256 initial = 1_000_000_000 * 10 ** 18; // 1B
            balanceOf[_admin] = initial;
            totalSupply = initial;
            emit Transfer(address(0), _admin, initial);
        }
    }

    // ── Modifiers ──────────────────────────────────────────────
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    // ── ERC20 core ─────────────────────────────────────────────
    function transfer(address to, uint256 amount) external returns (bool) {
        return _transfer(msg.sender, to, amount);
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        if (allowed != type(uint256).max) {
            if (amount > allowed) revert InsufficientAllowance();
            allowance[from][msg.sender] = allowed - amount;
        }
        return _transfer(from, to, amount);
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function _transfer(address from, address to, uint256 amount) internal returns (bool) {
        if (to == address(0)) revert InvalidRecipient();
        uint256 fromBal = balanceOf[from];
        if (amount > fromBal) revert InsufficientBalance();
        balanceOf[from] = fromBal - amount;
        balanceOf[to] += amount;
        emit Transfer(from, to, amount);
        return true;
    }

    // ── Ownable ────────────────────────────────────────────────
    function transferOwnership(address newOwner) external onlyOwner {
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert Unauthorized();
        emit OwnershipTransferred(owner, pendingOwner);
        owner = pendingOwner;
        pendingOwner = address(0);
    }

    // ── Mint / Burn ────────────────────────────────────────────
    function mint(address to, uint256 amount) external onlyOwner {
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }

    function burn(uint256 amount) external {
        if (amount > balanceOf[msg.sender]) revert InsufficientBalance();
        balanceOf[msg.sender] -= amount;
        totalSupply -= amount;
        totalBurned += amount;
        emit Transfer(msg.sender, address(0), amount);
        emit TokensBurned(amount);
    }

    // ── Buyback ────────────────────────────────────────────────
    function setBuybackEnabled(bool enabled) external onlyOwner {
        buybackEnabled = enabled;
    }
}
