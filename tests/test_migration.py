import pytest
from conftest import deployStrategy
import util

def test_funds_migration(
    chain,
    token,
    vault,
    strategy,
    amount,
    Strategy,
    strategist,
    gov,
    user,
    RELATIVE_APPROX,
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    chain.sleep(1)
    strategy.harvest({"from":gov})

    estimatedTotalAssets = strategy.estimatedTotalAssets()
    assert pytest.approx(estimatedTotalAssets, rel=RELATIVE_APPROX) == amount

    rewards = strategy.balanceOfReward()
    balanceOfLPTokens = strategy.balanceOfWant() + strategy.balanceOfLPInMasterChef()

    # Deploy new strategy
    new_strategy = deployStrategy(Strategy, strategist, gov, vault)
    # Migrate to a new strategy


    # Harvest new strategy to re-invest everything
    strategy.harvest({"from":gov})
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    new_strategy.harvest({"from":gov})
    # assert that the old strategy does not have any funds
    assert strategy.estimatedTotalAssets() == 0
    assert strategy.balanceOfWant() == 0
    assert strategy.balanceOfLPInMasterChef() == 0

    # assert that all the funds ( want, LP and rewards) have been migrated correctly
    assert  pytest.approx(new_strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)== estimatedTotalAssets
    totalLpTokens = new_strategy.balanceOfWant() +  new_strategy.balanceOfLPInMasterChef()
    assert  pytest.approx(totalLpTokens, rel=RELATIVE_APPROX) == balanceOfLPTokens
    # assert  pytest.approx(new_strategy.balanceOfReward(), rel=RELATIVE_APPROX) == rewards


def test_migration(
    chain,
    token,
    vault,
    strategy,
    amount,
    Strategy,
    strategist,
    gov,
    user,
    RELATIVE_APPROX,
    sexReward, solidReward,  sexReward_whale , solidReward_whale
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    #Deposit Funds on the strategy
    strategy.harvest({"from":gov})
    stratInitialAssets = strategy.estimatedTotalAssets()
    pricePerShare = vault.pricePerShare()

    assert pytest.approx(stratInitialAssets, rel=RELATIVE_APPROX) == amount

    # Deploy new strategy
    new_strategy = deployStrategy(Strategy, strategist, gov, vault)
    new_strategy.setKeeper(gov)

    assert (strategy.address != new_strategy.address)
    # Migrate to a new strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})

    newStratEstimatedAssets = new_strategy.estimatedTotalAssets()

    assert vault.totalAssets() >= amount
    assert strategy.estimatedTotalAssets() == 0

    # Run strategy to make sure we are still earning money
    util.airdrop_rewards(new_strategy, sexReward, solidReward,  sexReward_whale , solidReward_whale)
    chain.mine(1)
    new_strategy.tend({"from": gov})


    assert new_strategy.estimatedTotalAssets() >  newStratEstimatedAssets
    assert new_strategy.estimatedTotalAssets() > stratInitialAssets

    new_strategy.harvest({"from":gov})
    chain.sleep(3600*6)
    chain.mine(1)

    assert vault.totalAssets() > amount
    assert vault.pricePerShare() > pricePerShare
