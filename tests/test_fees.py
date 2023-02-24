import util
import brownie
import pytest


def test_fees_multiple_harvests(chain,gov, strategist, vault, strategy, token, amount, user, RELATIVE_APPROX, thenaReward, thenaReward_whale):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from": gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Harvest 1: 
    vaultAssets =  0
    time = 86400 * 30 # 1 day of running the strategy
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.mine(1)
    strategy.harvest({"from": gov})

    chain.sleep(3600 * 6) # wait for the funds to unlock
    chain.mine(1)
    currentVaultAssets = vault.totalAssets()

    assert vaultAssets < currentVaultAssets
    vaultAssets = currentVaultAssets

    time = 86400 * 30 # 1 day of running the strategy
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.mine(1)
    strategy.harvest({"from": gov})

    chain.sleep(3600 * 6) # wait for the funds to unlock
    chain.mine(1)
    currentVaultAssets = vault.totalAssets()

    assert vaultAssets < currentVaultAssets
    vaultAssets = currentVaultAssets

    netProfit = vault.totalAssets() - amount

    # Withdraw user funds
    userVaultShares = vault.balanceOf(user)
    maxLoss = 10 # 0.05% BPS
    vault.withdraw(userVaultShares, user, maxLoss,{"from": user})
    userProfit = token.balanceOf(user) - user_balance_before

    assert pytest.approx(userProfit, rel=10e-2) == netProfit
   
    # Transfer strategist fees to strategists
    # sharesInStrat = vault.balanceOf(strategy)
    # vault.transferFrom(strategy, strategist, sharesInStrat, {"from":strategist});
    # strategist_bal_before = token.balanceOf(strategist)

    # # Withdraw strategist fees
    # strategistShares = vault.balanceOf(strategist)
    # vault.withdraw(strategistShares, strategist, maxLoss,{"from": strategist})
    # stratFees = token.balanceOf(strategist) - strategist_bal_before

    # # Withdraw governance Fees
    # gov_bal_before = token.balanceOf(gov)
    # govShares = vault.balanceOf(gov)
    # vault.withdraw(govShares, gov, maxLoss,{"from": gov})
    # govFees = token.balanceOf(gov) - gov_bal_before

    # expectedFeesProfit =  netProfit * 0.1

    # assert pytest.approx(expectedFeesProfit, rel=10e-2) == stratFees
    # assert pytest.approx(expectedFeesProfit, rel=10e-2) == govFees

    # assert pytest.approx(stratFees + govFees + userProfit, rel=10e-3) == netProfit

def test_fees_after_autocompounding(chain, vault, strategy , token, amount,gov, user, thenaReward, thenaReward_whale):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # Tend 1: Re-invest rewards   
    stratPrevTendAssets =  strategy.estimatedTotalAssets()
   
    time = 86400 * 30 # 1 day of running the strategy
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.sleep(3600)
    chain.mine(1)

    strategy.tend({"from": gov})

    currentStratAssets = strategy.estimatedTotalAssets()
    
    assert stratPrevTendAssets == currentStratAssets
    stratPrevTendAssets = currentStratAssets
    time = 86400 * 30 # 1 day of running the strategy
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.sleep(3600)
    chain.mine(1)

    strategy.tend({"from": gov})

    currentStratAssets = strategy.estimatedTotalAssets()

    assert stratPrevTendAssets == currentStratAssets
    stratPrevTendAssets = currentStratAssets
    
    # strategy.setCollectFeesEnabled(True, {"from":gov})

    strategy.harvest({"from": gov})
    chain.sleep(3600 * 6) # wait for the funds to unlock
    chain.mine(1)
    eta = vault.totalAssets()
    print(f"vault.totalAssets(): {vault.totalAssets()}")
    print(f"ETA: {eta}")
    print(f"pricePerShare: {vault.pricePerShare()}")

    # assert grossProfit == netProfit
    #Withdraw user funds
    userVaultShares = vault.balanceOf(user)
    print(f"userVaultShares: {userVaultShares}")
    maxLoss = 10 # 0.05% BPS
    vault.withdraw(userVaultShares, user, maxLoss, {"from": user})

    userProfit = token.balanceOf(user) - user_balance_before
    print(f"""userProfit: {userProfit} """)
    print(f"""token.balanceOf(user): {token.balanceOf(user)} """)
    print(f"""user_balance_before: {user_balance_before} """)
    assert pytest.approx(userProfit, rel=10e-2) == eta - amount

