from brownie import Contract

def stateOfStrat(msg, strategy, token):
    print(f'\n===={msg}====')
    wantDec = 10 ** token.decimals()
    print(f'Balance of {token.symbol()}: {strategy.balanceOfWant() / wantDec}')
    print(f'Balance of Bpt: {strategy.balanceOfBpt() / wantDec}')
    print(f'Estimated Total Assets: {strategy.estimatedTotalAssets() / wantDec}')

# Balancer uses blocks count to give rewards so the Chain.sleep() method of timetravel does not work
# Chain.mine() is too slow so the best solution is to airdrop rewards
def airdrop_rewards(strategy, thenaReward, thenaReward_whale):
    amount = 1000 * 1e18
    thenaReward.approve(strategy, 2 ** 256 - 1, {'from': thenaReward_whale})
    thenaReward.transfer(strategy, amount, {'from': thenaReward_whale})