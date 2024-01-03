// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.5.0;

interface IAlgebraFactory {
	/**
	 *  @notice Returns the pool address for a given pair of tokens and a fee, or address 0 if it does not exist
	 *  @dev tokenA and tokenB may be passed in either token0/token1 or token1/token0 order
	 *  @param tokenA The contract address of either token0 or token1
	 *  @param tokenB The contract address of the other token
	 *  @return pool The pool address
	 */
	function poolByPair(address tokenA, address tokenB) external view returns (address pool);
}
