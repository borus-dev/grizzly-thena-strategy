// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.5.0;
pragma experimental ABIEncoderV2;

interface IUniV3Router {
	struct ExactInputParams {
		bytes path;
		address recipient;
		uint256 deadline;
		uint256 amountIn;
		uint256 amountOutMinimum;
	}

	function exactInput(ExactInputParams calldata params)
		external
		payable
		returns (uint256 amountOut);
}
