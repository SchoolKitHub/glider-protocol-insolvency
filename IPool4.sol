// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Pool4 Interface
 * @dev Interface for the Pool4 contract on Ethereum
 * Address: 0x366049d336e73cfaf39c6a933780ca4c96ea084c
 */
interface IPool4 {
    function borrow(uint256 amount, uint256 maxRate, uint256 propTokenId) external;
    function poolBorrowed() external view returns (uint256);
}

/**
 * @title ERC20 Interface
 * @dev Minimal ERC20 interface for token transfers
 */
interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/**
 * @title PropToken Interface
 * @dev Interface for NFT collateral token
 */
interface IPropToken {
    function approve(address to, uint256 tokenId) external;
    function setApprovalForAll(address operator, bool approved) external;
    function safeTransferFrom(address from, address to, uint256 tokenId) external;
    function ownerOf(uint256 tokenId) external view returns (address);
    function getApproved(uint256 tokenId) external view returns (address);
}
