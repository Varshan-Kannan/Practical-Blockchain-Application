// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MessageBoard {
    string private message = "Hello from Solidity";

    event MessageUpdated(address indexed editor, string newMessage);

    function getMessage() public view returns (string memory) {
        return message;
    }

    function setMessage(string memory newMessage) public {
        message = newMessage;
        emit MessageUpdated(msg.sender, newMessage);
    }
}
