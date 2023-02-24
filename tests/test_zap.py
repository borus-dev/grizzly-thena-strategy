def test_correct_zap(chain, vault, strategy, token, amount,gov, user, RELATIVE_APPROX):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds to the strategy
    chain.sleep(1)
    strategy.harvest({"from":gov})
    print(f""" 
    1º Harvest
    ----------
    want: {strategy.balanceOfWant()}

    """)
    assert strategy.balanceOfWant() < 1e18

    # Harvest 2-7: 
    chain.sleep(86400) # 1 day of running the strategy
    chain.mine(1)
    strategy.harvest({"from":gov})
    print(f""" 
    1º Harvest
    ----------
    want: {strategy.balanceOfWant()}

    """)
    assert strategy.balanceOfWant() < 1e18
