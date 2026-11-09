// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.34;

contract PriceFeed {
    address public oracle;
    int256 public value;
    uint256 public updatedAt;
    address public updater;
    uint80 public roundId;

    uint8 public constant decimals = 8;
    string public constant description = "ETH / USD Oracle";

    constructor(address oracleAddress) {
        oracle = oracleAddress;
    }

    function update(int256 newValue) external {
        require(msg.sender == oracle, "Not a oracle");
        value = newValue;
        updatedAt = block.timestamp;
        updater = msg.sender;
        roundId += 1;
    }

    function latestRoundData()
        external
        view
        returns (uint80, int256, uint256, uint256, uint80)
    {
        return (roundId, value, updatedAt, updatedAt, roundId);
    }
}
