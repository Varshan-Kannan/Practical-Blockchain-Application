// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Simple storage contract - same one we used in Remix
contract Storage {
    uint256 number;

    // save a number on chain (this is a transaction, costs gas)
    function store(uint256 num) public {
        number = num;
    }

    // read the saved number (this is a call, free)
    function retrieve() public view returns (uint256) {
        return number;
    }
}
