// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface AggregatorV3Interface {
    function decimals() external view returns (uint8);
    function description() external view returns (string memory);
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

contract PriceConsumer {
    AggregatorV3Interface public feed;
    uint256 public maxAge;

    constructor(address feedAddress, uint256 maxAgeSeconds) {
        feed = AggregatorV3Interface(feedAddress);
        maxAge = maxAgeSeconds;
    }

    function getPrice() public view returns (int256 price, uint256 ageSeconds) {
        (, int256 answer, , uint256 updatedAt, ) = feed.latestRoundData();
        require(updatedAt != 0, "No data available");
        require(block.timestamp - updatedAt <= maxAge, "Data is stale");
        return (answer, block.timestamp - updatedAt);
    }

    function usdToWei(uint256 usd) external view returns (uint256){
        (int256 price, ) = getPrice();

        require(price > 0, "Invalid price");

        return (usd * 1e18 * (10 ** feed.decimals()))
        / uint256(price);
    }
}
