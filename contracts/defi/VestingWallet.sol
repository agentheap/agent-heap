// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title VestingWallet
 * @notice Token vesting with cliff, linear release, and multiple beneficiaries
 * @dev Commonly used for team tokens, investors, and advisor allocations.
 *      Each beneficiary has their own vesting schedule.
 */
contract VestingWallet is Ownable, ReentrancyGuard {
    IERC20 public token;

    struct VestingSchedule {
        uint256 totalAmount;
        uint256 cliff;       // Seconds after start when cliff ends
        uint256 duration;    // Total vesting duration in seconds
        uint256 start;       // Timestamp of vesting start
        uint256 claimed;
    }

    mapping(address => VestingSchedule) public schedules;
    address[] public beneficiaries;

    event ScheduleCreated(address indexed beneficiary, uint256 amount, uint256 duration);
    event TokensReleased(address indexed beneficiary, uint256 amount);
    event ScheduleRevoked(address indexed beneficiary);

    constructor(address _token) Ownable(msg.sender) {
        require(_token != address(0), "Invalid token address");
        token = IERC20(_token);
    }

    function createSchedule(
        address beneficiary,
        uint256 amount,
        uint256 cliffDuration,
        uint256 vestingDuration
    ) external onlyOwner {
        require(beneficiary != address(0), "Invalid beneficiary");
        require(amount > 0, "Amount must be > 0");
        require(schedules[beneficiary].totalAmount == 0, "Schedule exists");
        require(cliffDuration <= vestingDuration, "Cliff > duration");

        schedules[beneficiary] = VestingSchedule({
            totalAmount: amount,
            cliff: cliffDuration,
            duration: vestingDuration,
            start: block.timestamp,
            claimed: 0
        });
        beneficiaries.push(beneficiary);

        emit ScheduleCreated(beneficiary, amount, vestingDuration);
    }

    function releasable(address beneficiary) public view returns (uint256) {
        VestingSchedule storage s = schedules[beneficiary];
        if (s.totalAmount == 0) return 0;

        uint256 elapsed = block.timestamp - s.start;

        if (elapsed < s.cliff) return 0;

        if (elapsed >= s.duration) {
            return s.totalAmount - s.claimed;
        }

        uint256 vested = (s.totalAmount * elapsed) / s.duration;
        return vested - s.claimed;
    }

    function release(address beneficiary) external nonReentrant {
        uint256 amount = releasable(beneficiary);
        require(amount > 0, "Nothing to release");

        schedules[beneficiary].claimed += amount;
        token.transfer(beneficiary, amount);

        emit TokensReleased(beneficiary, amount);
    }

    function revokeSchedule(address beneficiary) external onlyOwner {
        VestingSchedule storage s = schedules[beneficiary];
        require(s.totalAmount > 0, "No schedule");

        uint256 remaining = s.totalAmount - s.claimed;
        s.totalAmount = s.claimed; // Prevent further claims
        delete schedules[beneficiary];

        if (remaining > 0) {
            token.transfer(owner(), remaining);
        }

        emit ScheduleRevoked(beneficiary);
    }

    function getBeneficiaries() external view returns (address[] memory) {
        return beneficiaries;
    }

    function deposit(uint256 amount) external onlyOwner {
        token.transferFrom(msg.sender, address(this), amount);
    }
}
