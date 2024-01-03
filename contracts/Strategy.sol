// SPDX-License-Identifier: AGPL-3.0

pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import { BaseStrategy, StrategyParams } from "./BaseStrategy.sol";
import { IERC20 } from "../interfaces/IERC20.sol";
import { SafeMath } from "./library/SafeMath.sol";
import { SafeERC20 } from "./library/SafeERC20.sol";
import { Address } from "./library/Address.sol";
import { ERC20 } from "./library/ERC20.sol";
import { Math } from "./library/Math.sol";

import { FullMath } from "../algebra/periphery/contracts/libraries/LiquidityAmounts.sol";
import { IAlgebraPool } from "../algebra/core/contracts/interfaces/IAlgebraPool.sol";
import { IAlgebraFactory } from "../algebra/core/contracts/interfaces/IAlgebraFactory.sol";
import { TickMath } from "../algebra/core/contracts/libraries/TickMath.sol";
import { ILpDepositor } from "../interfaces/ILpDepositor.sol";
import { IThenaRouter } from "../interfaces/IThenaRouter.sol";
import { IUniV3Router } from "../interfaces/IUniV3Router.sol";
import { IV1Pair } from "../interfaces/IThenaV1Pair.sol";

contract Strategy is BaseStrategy {
	using SafeERC20 for IERC20;
	using Address for address;
	using SafeMath for uint256;
	using TickMath for int24;

	/**
	 * @dev Tokens Used:
	 * {wbnb} - Required for liquidity routing when doing swaps.
	 * {thenaReward} - Token generated by staking our funds.
	 * {thenaLp} - LP Token for Thena exchange.
	 * {want} - Tokens that the strategy maximizes. IUniswapV2Pair tokens.
	 */
	address internal constant wbnb = address(0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c); // WBNB
	address public constant thenaReward = address(0xF4C8E32EaDEC4BFe97E0F595AdD0f4450a863a11); // THENA
	address internal usdt = address(0x55d398326f99059fF775485246999027B3197955); // USDT

	address internal v3Router = address(0x327Dd3208f0bCF590A66110aCB6e5e6941A4EfA0); // AlgebraFinance Router
	address public constant router = address(0x20a304a7d126758dfe6B243D0fc515F83bCA8431); // Thena Router
	ILpDepositor public masterChef; // {masterChef} - Depositor contract for Thena

	IAlgebraPool internal wbnbThePool = IAlgebraPool(0x51Bd5e6d3da9064D59BcaA5A76776560aB42cEb8);
	IAlgebraPool internal usdtWbnbPool =
		IAlgebraPool(0xD405b976Ac01023c9064024880999fC450A8668b);
	IAlgebraPool internal wbnbToken0Pool;
	IAlgebraPool internal wbnbToken1Pool;

	IV1Pair public thenaLp;
	IERC20 public token0;
	IERC20 public token1;

	uint256 public dust;
	uint256 public rewardDust;

	uint256 public maxSlippageIn; // bps
	uint256 public maxSlippageOut; // bps

	uint24 public maxSwapSlippage;

	bool internal abandonRewards;

	bool internal immutable isStable;
	uint256 internal constant basisOne = 10000;
	uint256 internal constant basisOnePool = 1000000;
	uint256 internal constant MAX = type(uint256).max;
	uint256 internal constant Q96 = 0x1000000000000000000000000;

	uint256 public minProfit;
	bool internal forceHarvestTriggerOnce;

	address internal constant voterTHE = 0x981B04CBDCEE0C510D331fAdc7D6836a77085030; // We send some extra THE here
	uint256 public keepTHE; // Percentage of THE we re-lock for boost (in basis points)

	constructor(
		address _vault,
		address _masterChef,
		address _thenaLp
	) public BaseStrategy(_vault) {
		require(_thenaLp == address(want), "Wrong lpToken");

		thenaLp = IV1Pair(_thenaLp);
		isStable = thenaLp.isStable();

		token0 = IERC20(thenaLp.token0());
		token1 = IERC20(thenaLp.token1());

		IAlgebraFactory factory = IAlgebraFactory(0x306F06C147f064A010530292A1EB6737c3e378e4);
		wbnbToken0Pool = IAlgebraPool(factory.poolByPair(wbnb, address(token0)));
		wbnbToken1Pool = IAlgebraPool(factory.poolByPair(wbnb, address(token1)));

		maxSlippageIn = 1;
		maxSlippageOut = 1;

		maxSwapSlippage = 50000; // 5%

		maxReportDelay = 30 days;
		minProfit = 1e21;

		keepTHE = 2000;

		dust = 10**uint256((ERC20(address(want)).decimals()));
		rewardDust = 10**uint256((ERC20(address(thenaReward)).decimals()));

		masterChef = ILpDepositor(_masterChef);
		require(masterChef.TOKEN() == address(want), "Wrong masterChef");

		assert(masterChef.rewardToken() == thenaReward);

		_giveAllowances();
	}

	//-------------------------------//
	//       Public View func        //
	//-------------------------------//

	function name() external view override returns (string memory) {
		return string(abi.encodePacked("ThenaStrategy ", "Pool ", ERC20(address(want)).symbol()));
	}

	function estimatedTotalAssets() public view override returns (uint256) {
		return balanceOfWant().add(balanceOfLPInMasterChef());
	}

	function balanceOfWant() public view returns (uint256) {
		return want.balanceOf(address(this));
	}

	function balanceOfLPInMasterChef() public view returns (uint256 _amount) {
		_amount = masterChef.balanceOf(address(this));
	}

	function balanceOfReward() public view returns (uint256 _thenaRewards) {
		_thenaRewards = IERC20(thenaReward).balanceOf(address(this));
	}

	function pendingRewards() public view returns (uint256 _thenaBalance) {
		_thenaBalance = masterChef.earned(address(this));
	}

	function estimatedHarvest() public view returns (uint256 profitInUsdt) {
		uint256 thenaBalance = pendingRewards().add(balanceOfReward());

		uint256 profitInWbnb = _getAmountOut(wbnbThePool, false, thenaBalance);

		profitInUsdt = _getAmountOut(usdtWbnbPool, false, profitInWbnb);
	}

	//-------------------------------//
	//      Internal Core func       //
	//-------------------------------//

	function prepareReturn(uint256 _debtOutstanding)
		internal
		override
		returns (
			uint256 _profit,
			uint256 _loss,
			uint256 _debtPayment
		)
	{
		// Claim THENA rewards
		_claimRewards();
		// Send some THENA to voter
		_sendToVoter();
		// Swap THENA for wBNB
		_sellRewards();
		// Swap wBNB for token0 & token1 and build the LP
		_convertToLpToken();

		uint256 assets = estimatedTotalAssets();
		uint256 wantBalance = balanceOfWant();
		uint256 debt = vault.strategies(address(this)).totalDebt;

		_debtPayment = _debtOutstanding;
		uint256 amountToFree = _debtPayment.add(_profit);

		if (assets >= debt) {
			_debtPayment = _debtOutstanding;
			_profit = assets.sub(debt);

			amountToFree = _profit.add(_debtPayment);

			if (amountToFree > 0 && wantBalance < amountToFree) {
				liquidatePosition(amountToFree);

				uint256 newLoose = balanceOfWant();

				// If we dont have enough money adjust _debtOutstanding and only change profit if needed
				if (newLoose < amountToFree) {
					if (_profit > newLoose) {
						_profit = newLoose;
						_debtPayment = 0;
					} else {
						_debtPayment = Math.min(newLoose.sub(_profit), _debtPayment);
					}
				}
			}
		} else {
			// Serious loss should never happen but if it does lets record it accurately
			_loss = debt.sub(assets);
		}

		// We're done harvesting, so reset our trigger if we used it
		forceHarvestTriggerOnce = false;
	}

	/**
	 * @notice
	 *  In simple autocompounding adjustPosition only deposits the LpTokens in masterChef.
	 */
	function adjustPosition(uint256 _debtOutstanding) internal override {
		// Lp assets before the operation
		uint256 pooledBefore = balanceOfLPInMasterChef();

		uint256 amountIn = balanceOfWant();
		if (amountIn > dust) {
			// Deposit all LpTokens in Thena masterChef
			_depositLpIntoMasterChef();
			_enforceSlippageIn(amountIn, pooledBefore);
		}
	}

	function liquidatePosition(uint256 _amountNeeded)
		internal
		override
		returns (uint256 _liquidatedAmount, uint256 _loss)
	{
		if (estimatedTotalAssets() <= _amountNeeded) {
			_liquidatedAmount = liquidateAllPositions();
			return (_liquidatedAmount, _amountNeeded.sub(_liquidatedAmount));
		}

		uint256 looseAmount = balanceOfWant();
		if (_amountNeeded > looseAmount) {
			uint256 toExitAmount = _amountNeeded.sub(looseAmount);

			_withdrawLpFromMasterChef(toExitAmount);

			_liquidatedAmount = Math.min(balanceOfWant(), _amountNeeded);
			_loss = _amountNeeded.sub(_liquidatedAmount);

			_enforceSlippageOut(toExitAmount, _liquidatedAmount.sub(looseAmount));
		} else {
			_liquidatedAmount = _amountNeeded;
		}
	}

	function liquidateAllPositions() internal override returns (uint256 _liquidated) {
		uint256 eta = estimatedTotalAssets();

		_withdrawLpFromMasterChef(balanceOfLPInMasterChef());

		_liquidated = balanceOfWant();

		_enforceSlippageOut(eta, _liquidated);
	}

	/**
	 * @notice
	 *  This withdraws Lp tokens and transfers them into newStrategy.
	 */
	function prepareMigration(address _newStrategy) internal override {
		_withdrawFromMasterChefAndTransfer(_newStrategy);
	}

	//-------------------------------//
	//      Internal Swap func       //
	//-------------------------------//

	/**
	 * @notice
	 *  Swaps THENA for WBNB.
	 */
	function _sellRewards() internal {
		uint256 thenaRewards = balanceOfReward();

		if (thenaRewards > rewardDust) {
			uint256 amountOut = _getAmountOut(wbnbThePool, false, thenaRewards);
			// THENA to WBNB
			IUniV3Router(v3Router).exactInput(
				IUniV3Router.ExactInputParams({
					path: abi.encodePacked(thenaReward, wbnb),
					recipient: address(this),
					deadline: block.timestamp,
					amountIn: thenaRewards,
					amountOutMinimum: FullMath.mulDiv(
						amountOut,
						basisOnePool.sub(maxSwapSlippage),
						basisOnePool
					)
				})
			);
		}
	}

	function _sendToVoter() internal {
		uint256 thenaBalance = balanceOfReward();
		uint256 sendToVoter = thenaBalance.mul(keepTHE).div(basisOne);

		if (sendToVoter > 0) {
			IERC20(thenaReward).safeTransfer(voterTHE, sendToVoter);
		}
	}

	/**
	 * @notice
	 *  Swaps half of the wbnb for token0 and token1 and adds liquidity.
	 */
	function _convertToLpToken() internal {
		uint256 wbnbBalance = IERC20(wbnb).balanceOf(address(this));
		uint256 amountIn = wbnbBalance.div(2);
		uint256 amountOut;
		bool zeroForOne;

		if (wbnbBalance > 1e15) {
			// If token0 or token1 is wbnb we skip the swap
			if (address(token0) != wbnb) {
				zeroForOne = address(wbnbToken0Pool.token0()) == wbnb;
				amountOut = _getAmountOut(wbnbToken0Pool, zeroForOne, amountIn);
				// 1/2 wbnb to token0
				IUniV3Router(v3Router).exactInput(
					IUniV3Router.ExactInputParams({
						path: abi.encodePacked(wbnb, address(token0)),
						recipient: address(this),
						deadline: block.timestamp,
						amountIn: amountIn,
						amountOutMinimum: FullMath.mulDiv(
							amountOut,
							basisOnePool.sub(maxSwapSlippage),
							basisOnePool
						)
					})
				);
			}
			if (address(token1) != wbnb) {
				zeroForOne = address(wbnbToken1Pool.token0()) == wbnb;
				amountOut = _getAmountOut(wbnbToken1Pool, zeroForOne, amountIn);
				// 1/2 wbnb to token1
				IUniV3Router(v3Router).exactInput(
					IUniV3Router.ExactInputParams({
						path: abi.encodePacked(wbnb, address(token1)),
						recipient: address(this),
						deadline: block.timestamp,
						amountIn: wbnbBalance.div(2),
						amountOutMinimum: FullMath.mulDiv(
							amountOut,
							basisOnePool.sub(maxSwapSlippage),
							basisOnePool
						)
					})
				);
			}
		}

		// Add liquidity to build the LpToken
		uint256 token0Balance = IERC20(token0).balanceOf(address(this));
		uint256 token1Balance = IERC20(token1).balanceOf(address(this));

		if (token0Balance > 0 && token1Balance > 0) {
			_addLiquidity(token0Balance, token1Balance);
		}
	}

	//-------------------------------//
	//    Internal Liquidity func    //
	//-------------------------------//

	/**
	 * @notice
	 *  Add liquidity to Thena.
	 */
	function _addLiquidity(uint256 token0Amount, uint256 token1Amount) internal {
		IThenaRouter(router).addLiquidity(
			address(token0),
			address(token1),
			isStable,
			token0Amount,
			token1Amount,
			0,
			0,
			address(this),
			block.timestamp
		);
	}

	//--------------------------------//
	//    Internal MasterChef func    //
	//--------------------------------//

	/**
	 * @notice
	 *  Deposits all the LpTokens in masterChef.
	 */
	function _depositLpIntoMasterChef() internal {
		uint256 balanceOfLpTokens = balanceOfWant();
		if (balanceOfLpTokens > 0) {
			masterChef.deposit(balanceOfLpTokens);
		}
	}

	/**
	 * @notice
	 *  Withdraws a certain amount from masterChef.
	 */
	function _withdrawLpFromMasterChef(uint256 amount) internal {
		uint256 toWithdraw = Math.min(amount, balanceOfLPInMasterChef());
		if (toWithdraw > 0) {
			masterChef.withdraw(toWithdraw);
		}
	}

	/**
	 * @notice
	 *  Claim all THENA rewards from masterChef.
	 */
	function _claimRewards() internal {
		masterChef.getReward();
	}

	/**
	 * @notice
	 *  AbandonRewards withdraws lp without rewards.
	 * @dev
	 *  Specify where to withdraw to. Migrate function already has safeTransfer of want.
	 */
	function _withdrawFromMasterChefAndTransfer(address _to) internal {
		if (abandonRewards) {
			_withdrawLpFromMasterChef(balanceOfLPInMasterChef());
		} else {
			_claimRewards();
			_withdrawLpFromMasterChef(balanceOfLPInMasterChef());
			IERC20(thenaReward).safeTransfer(_to, balanceOfReward());
		}
	}

	//-------------------------------//
	//     Internal Helpers func     //
	//-------------------------------//

	function _giveAllowances() internal {
		IERC20(address(thenaLp)).safeApprove(address(masterChef), 0);
		IERC20(address(thenaLp)).safeApprove(address(masterChef), MAX);

		IERC20(address(thenaLp)).safeApprove(router, 0);
		IERC20(address(thenaLp)).safeApprove(router, MAX);

		IERC20(wbnb).safeApprove(router, 0);
		IERC20(wbnb).safeApprove(router, MAX);

		IERC20(thenaReward).safeApprove(router, 0);
		IERC20(thenaReward).safeApprove(router, MAX);

		IERC20(token0).safeApprove(router, 0);
		IERC20(token0).safeApprove(router, MAX);

		IERC20(token1).safeApprove(router, 0);
		IERC20(token1).safeApprove(router, MAX);
	}

		/**
	 * @notice Gets an out amount for a swap, based on the pool TWAP
	 * @param pool The pool to use as a TWAP reference
	 * @param zeroForOne Direction of the swap according to pool token order
	 * @param amountIn Amount to swap
	 */
	function _getAmountOut(
		IAlgebraPool pool,
		bool zeroForOne,
		uint256 amountIn
	) internal view returns (uint256 amountOut) {
		uint32[] memory secondsAgo = new uint32[](2);
		secondsAgo[0] = 20;
		secondsAgo[1] = 0;

		(int56[] memory tickCumulatives, , , ) = pool.getTimepoints(secondsAgo);

		int24 avgTick = int24((tickCumulatives[1] - tickCumulatives[0]) / int56(20));
		uint160 avgSqrtRatioX96 = avgTick.getSqrtRatioAtTick();

		uint256 priceX96 = FullMath.mulDiv(avgSqrtRatioX96, avgSqrtRatioX96, Q96);

		amountOut = zeroForOne
			? FullMath.mulDiv(amountIn, priceX96, Q96)
			: FullMath.mulDiv(amountIn, Q96, priceX96);
	}

	/**
	 * @notice
	 *  Revert if slippage out exceeds our requirement.
	 * @dev
	 *  Enforce that amount exited didn't slip beyond our tolerance.
	 *  Check for positive slippage, just in case.
	 */
	function _enforceSlippageOut(uint256 _intended, uint256 _actual) internal view {
		uint256 exitSlipped = _intended > _actual ? _intended.sub(_actual) : 0;
		uint256 maxLoss = _intended.mul(maxSlippageOut).div(basisOne);
		require(exitSlipped <= maxLoss, "Slipped Out!");
	}

	/**
	 * @notice
	 *  Revert if slippage in exceeds our requirement.
	 * @dev
	 *  Enforce that amount exchange from want to LP tokens didn't slip beyond our tolerance.
	 *  Check for positive slippage, just in case.
	 */
	function _enforceSlippageIn(uint256 _amountIn, uint256 _pooledBefore) internal view {
		uint256 pooledDelta = balanceOfLPInMasterChef().sub(_pooledBefore);
		uint256 joinSlipped = _amountIn > pooledDelta ? _amountIn.sub(pooledDelta) : 0;
		uint256 maxLoss = _amountIn.mul(maxSlippageIn).div(basisOne);
		require(joinSlipped <= maxLoss, "Slipped in!");
	}

	function protectedTokens() internal view override returns (address[] memory) {}

	//-----------------------------//
	//    Public Triggers func     //
	//-----------------------------//

	/**
	 * @notice
	 *  Use this to determine when to harvest.
	 */
	function harvestTrigger(uint256 callCostInWei) public view override returns (bool) {
		StrategyParams memory params = vault.strategies(address(this));

		// Should not trigger if strategy is not active (no assets and no debtRatio)
		if (!isActive()) return false;

		// Trigger if profit generated is higher than minProfit
		if (estimatedHarvest() > minProfit) return true;

		// Harvest no matter what once we reach our maxDelay
		if (block.timestamp.sub(params.lastReport) > maxReportDelay) return true;

		// Trigger if we want to manually harvest, but only if our gas price is acceptable
		if (forceHarvestTriggerOnce) return true;

		// Otherwise, we don't harvest
		return false;
	}

	function ethToWant(uint256 _amtInWei) public view override returns (uint256) {}

	function tendTrigger(uint256 callCostInWei) public view override returns (bool) {
		return balanceOfWant() > 0;
	}

	//-------------------------------//
	//    Protected Setters func     //
	//-------------------------------//

	function setMinProfit(uint256 _minAcceptableProfit) external onlyKeepers {
		minProfit = _minAcceptableProfit;
	}

	/**
	 * @notice
	 *  This allows us to manually harvest with our keeper as needed.
	 */
	function setForceHarvestTriggerOnce(bool _forceHarvestTriggerOnce) external onlyKeepers {
		forceHarvestTriggerOnce = _forceHarvestTriggerOnce;
	}

	function setParams(uint256 _maxSlippageIn, uint256 _maxSlippageOut)
		external
		onlyVaultManagers
	{
		require(_maxSlippageIn <= basisOne);
		maxSlippageIn = _maxSlippageIn;

		require(_maxSlippageOut <= basisOne);
		maxSlippageOut = _maxSlippageOut;
	}

	/// @notice maxSwapSlippage in 1e6 scale, e.g 1% 10000, 10% 100000, etc
	function setSwapSlippage(uint24 _maxSwapSlippage) external onlyVaultManagers {
		require(maxSwapSlippage <= basisOne, "STH"); // Slippage too high
		maxSwapSlippage = _maxSwapSlippage;
	}

	function setDust(uint256 _dust, uint256 _rewardDust) external onlyVaultManagers {
		dust = _dust;
		rewardDust = _rewardDust;
	}

	function setKeep(uint256 _keepTHE) external onlyVaultManagers {
		require(_keepTHE <= 10_000, "Wrong input");
		keepTHE = _keepTHE;
	}

	/**
	 * @notice
	 *  Manually returns lps in masterChef to the strategy. Used in emergencies.
	 */
	function emergencyWithdrawFromMasterChef() external onlyVaultManagers {
		_withdrawLpFromMasterChef(balanceOfLPInMasterChef());
	}

	/**
	 * @notice
	 *  Manually returns lps in masterChef to the strategy when Thena masterchef is in emergency mode.
	 */
	function emergencyWithdrawFromMasterChefInEmergencyMode() external onlyVaultManagers {
		masterChef.emergencyWithdraw();
	}

	/**
	 * @notice
	 *  Toggle for whether to abandon rewards or not on emergency withdraws from masterChef.
	 */
	function setAbandonRewards(bool abandon) external onlyVaultManagers {
		abandonRewards = abandon;
	}

	receive() external payable {}
}

