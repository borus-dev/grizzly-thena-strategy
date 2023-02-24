import pytest
from brownie import config, Contract, accounts

import util

def test_deposit_withdraw(
    chain, token, vault, gov, strategy, user, amount, RELATIVE_APPROX
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    balanceOfWant = strategy.balanceOfWant()

    # withdrawal
    vaultShares = vault.balanceOf(user)
    maxLoss = 10 # 0.55% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )

def test_losses_multiple_deposits_withdraw(
    chain, token, vault, strategy, gov, user, user2, user3, amount, amount2, amount3, RELATIVE_APPROX
):
    # Deposit to the vault
    user_1_balance_before = token.balanceOf(user)
    user_2_balance_before = token.balanceOf(user2)
    user_3_balance_before = token.balanceOf(user3)

    totalDeposit = amount + amount2 + amount3

    token.approve(vault.address, amount, {"from": user})
    token.approve(vault.address, amount2, {"from": user2})
    token.approve(vault.address, amount3, {"from": user3})

    vault.deposit(amount, {"from": user})
    vault.deposit(amount2, {"from": user2})
    vault.deposit(amount3, {"from": user3})

    assert token.balanceOf(vault.address) == totalDeposit

    # Harvest to deposit funds on the strategy
    chain.mine(1)
    strategy.harvest({"from": gov})

    # Losses due to deposit fee and price impact
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == totalDeposit 

    maxLoss = 20 # 0.01% BPS
    
    # Withdrawal user
    vaultShares = vault.balanceOf(user)
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})
    # This loss is taken by the users left in the vault.
    # User has no profit & no loss
    assert pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_1_balance_before

    # Withdrawal user2
    vaultShares = vault.balanceOf(user2)
    vault.withdraw(vaultShares, user2, maxLoss,{"from": user2})
    # User2 has no profit & no loss
    assert pytest.approx(token.balanceOf(user2), rel=RELATIVE_APPROX) == user_2_balance_before

    # Withdrawal user3
    vaultShares = vault.balanceOf(user3)
    vault.withdraw(vaultShares, user3, maxLoss * 3,{"from": user3})

    assert pytest.approx(token.balanceOf(user3), rel=RELATIVE_APPROX) == user_3_balance_before

def test_deposit_withdraw_1(
    chain, token, vault, strategy, gov, user, amount, RELATIVE_APPROX,
    thenaReward, thenaReward_whale
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # tend()
    stratPrevTendAssets =  strategy.estimatedTotalAssets()
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.mine(1)

    strategy.tend({"from": gov})

    currentStratAssets = strategy.estimatedTotalAssets()

    # strategy.harvest({"from": gov})
    chain.mine(1)

    # withdrawal
    vaultShares = vault.balanceOf(user)
    maxLoss = 10 # 0.55% BPS
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )


def test_singe_harvest_multiple_deposits_withdraw_1(
    chain, token, vault, strategy, user, user2, user3, gov, amount, amount2, amount3, RELATIVE_APPROX,
    thenaReward, thenaReward_whale
):
    # Deposit to the vault
    user_1_balance_before = token.balanceOf(user)
    user_2_balance_before = token.balanceOf(user2)
    user_3_balance_before = token.balanceOf(user3)

    totalDeposit = amount + amount2 + amount3

    token.approve(vault.address, amount, {"from": user})
    token.approve(vault.address, amount2, {"from": user2})
    token.approve(vault.address, amount3, {"from": user3})

    vault.deposit(amount, {"from": user})
    vault.deposit(amount2, {"from": user2})
    vault.deposit(amount3, {"from": user3})

    pps_before = vault.pricePerShare()
    assert token.balanceOf(vault.address) ==totalDeposit

    # Harvest to deposit funds on the strategy
    chain.mine(1)
    strategy.harvest({"from": gov})

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == totalDeposit

    depositLoss = totalDeposit - strategy.estimatedTotalAssets();
    
    # Harvest 2-7 to get rewards
    vaultAssets =  vault.totalAssets()
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.mine()
    chain.sleep(86400) # 1 day of running the strategy
    chain.mine(1)
    pendingRewards = strategy.pendingRewards()

    strategy.harvest({"from": gov})

    chain.sleep(3600 * 6) # Wait for the funds to unlock
    chain.mine(1)

    maxLoss = 10 # 0.05% BPS

    assert vault.totalAssets() > totalDeposit
    
    # withdrawal user
    vaultShares = vault.balanceOf(user)
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})

    assert token.balanceOf(user) > user_1_balance_before

    # Withdrawal user2
    vaultShares = vault.balanceOf(user2)
    vault.withdraw(vaultShares, user2, maxLoss,{"from": user2})

    # Withdrawal user3
    vaultShares = vault.balanceOf(user3)
    vault.withdraw(vaultShares, user3, maxLoss,{"from": user3})

    
    assert token.balanceOf(user) > user_1_balance_before
    assert token.balanceOf(user2) > user_2_balance_before
    assert token.balanceOf(user3) > user_3_balance_before

def test_multiple_harvest_deposits_withdraw(
    chain, token, vault, strategy, user, user2, user3, gov, amount, amount2, amount3, RELATIVE_APPROX,
    thenaReward, thenaReward_whale
):
    # Deposit to the vault
    user_1_balance_before = token.balanceOf(user)
    totalDeposit = amount 
    token.approve(vault.address, amount, {"from": user})

    vault.deposit(amount, {"from": user})

    # Harvest 1 to deposit funds on the strategy
    chain.mine(1)
    strategy.harvest({"from": gov})
    initialLoss = strategy.estimatedTotalAssets() - totalDeposit
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == totalDeposit
    
    # Harvest 2 to get rewards
    chain.sleep(86400) # 1 day of running the strategy
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.mine(1)
    strategy.harvest({"from": gov})

    print(f"""ETA: {strategy.estimatedTotalAssets()}""")
    print(f"""initialLoss: {initialLoss}""")

    chain.sleep(3600 * 6) # Wait for the funds to unlock
    chain.mine(1)

    maxLoss = 10 # 0.05% BPS

    # withdrawal user
    vaultShares = vault.balanceOf(user)
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})

    assert token.balanceOf(user) > user_1_balance_before

def test_singe_harvest_multiple_deposits_withdraw_2(
    chain, token, vault, strategy, user, user2, user3, gov, amount, amount2, amount3, RELATIVE_APPROX,
    thenaReward, thenaReward_whale
):
    # Deposit to the vault
    user_1_balance_before = token.balanceOf(user)
    user_2_balance_before = token.balanceOf(user2)
    user_3_balance_before = token.balanceOf(user3)

    totalDeposit = amount + amount2 + amount3

    token.approve(vault.address, amount, {"from": user})
    token.approve(vault.address, amount2, {"from": user2})
    token.approve(vault.address, amount3, {"from": user3})

    vault.deposit(amount, {"from": user})
    vault.deposit(amount2, {"from": user2})
    vault.deposit(amount3, {"from": user3})

    pps_before = vault.pricePerShare()
    assert token.balanceOf(vault.address) ==totalDeposit

    # Harvest to deposit funds on the strategy
    chain.mine(1)
    strategy.harvest({"from": gov})

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == totalDeposit
    
    # Harvest 2-7 to get rewards
    vaultAssets =  vault.totalAssets()
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.mine(1)
    
    print(f"""ETA: {strategy.estimatedTotalAssets()}""")
    chain.sleep(3600 * 6) # Wait for the funds to unlock
    chain.mine(1)

    strategy.harvest({"from": gov})

    chain.sleep(3600 * 6) # Wait for the funds to unlock
    chain.mine(1)

    maxLoss = 10 # 0.05% BPS

    assert vault.pricePerShare() > pps_before
    
    # withdrawal user
    vaultShares = vault.balanceOf(user)
    vault.withdraw(vaultShares, user, maxLoss,{"from": user})

    # Withdrawal user2
    vaultShares = vault.balanceOf(user2)
    vault.withdraw(vaultShares, user2, maxLoss,{"from": user2})

    # Withdrawal user3
    vaultShares = vault.balanceOf(user3)
    vault.withdraw(vaultShares, user3, maxLoss,{"from": user3})
    
    assert token.balanceOf(user) > user_1_balance_before
    assert token.balanceOf(user2) > user_2_balance_before
    assert token.balanceOf(user3) > user_3_balance_before

def test_singe_harvest_multiple_deposits_withdraw_3(
    chain, token, vault, strategy, user, user2, user3, gov, amount, amount2, amount3, RELATIVE_APPROX,
    thenaReward, thenaReward_whale
):
    # Deposit to the vault
    user_1_balance_before = token.balanceOf(user)
    totalDeposit = amount
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
   
    # Harvest to deposit funds on the strategy
    chain.mine(1)
    strategy.harvest({"from": gov})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == totalDeposit
    
    vault.updateStrategyDebtRatio(strategy.address, 0 ,{"from": gov})
    chain.sleep(86400)
    util.airdrop_rewards(strategy, thenaReward, thenaReward_whale)
    chain.mine()

    strategy.harvest({"from": gov})
    vault.updateStrategyDebtRatio(strategy.address, 0 ,{"from": gov})
    strategy.harvest({"from": gov})

    chain.sleep(3600* 7)
    chain.mine()

    vaultAssets = vault.totalAssets()
    assert vaultAssets > amount
    assert strategy.estimatedTotalAssets() == 0

    # withdrawal user
    maxLoss = 10 
    vaultShares = vault.balanceOf(user)
    vault.withdraw(vaultShares, user, maxLoss, {"from": user})

    assert token.balanceOf(user) > user_1_balance_before
    assert token.balanceOf(user) - user_1_balance_before > 1e18
   
def test_singe_harvest_multiple_deposits_withdraw_4(
    chain, token, vault, strategy, user, user2, user3, gov, amount, amount2, amount3, RELATIVE_APPROX
):
    # Deposit to the vault
    user_1_balance_before = token.balanceOf(user)
    totalDeposit = amount
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
   
    # Harvest to deposit funds on the strategy
    chain.mine(1)
    strategy.harvest({"from": gov})
    stratInitialAssets = strategy.estimatedTotalAssets()
    assert pytest.approx(stratInitialAssets, rel=1e-3) == totalDeposit

    # Collect profits
    chain.sleep(1800)
    chain.mine()
    strategy.harvest({"from": gov})
    stratInitialAssets_after = strategy.estimatedTotalAssets()

    # Unlock profits on the vault
    chain.sleep(3600 * 24)
    chain.mine()

    vaultAssets = vault.totalAssets()

    vault.updateStrategyDebtRatio(strategy.address, 0 ,{"from": gov})

    # Get funds out of the strategy
    strategy.harvest({"from": gov})
    chain.sleep(3600* 7)
    chain.mine()

    vaultAssets_after = vault.totalAssets()
    assert vaultAssets_after > vaultAssets
    assert token.balanceOf(vault.address) > vaultAssets
    assert vaultAssets_after > amount
    assert strategy.estimatedTotalAssets() == 0

    # withdrawal user
    maxLoss = 10 
    vaultShares = vault.balanceOf(user)
    vault.withdraw(vaultShares, user, maxLoss, {"from": user})

    userProfits = token.balanceOf(user) - user_1_balance_before

    assert token.balanceOf(user) > user_1_balance_before
    assert userProfits > 0
   
