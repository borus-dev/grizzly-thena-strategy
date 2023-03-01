import pytest
from brownie import config, Contract

import sys
import os

script_dir = os.path.dirname( __file__ )
strategyDeploy_dir = os.path.join( script_dir ,  ".." , "scripts" )
sys.path.append( strategyDeploy_dir )

from deployStrategy import addHealthCheck, deploy

stratConfig = {
    "DEI_USDT": {
        "name":"StrategyThenaDEI_USDT",
        "masterChef":"0x1520D103D8B366C87A0b273E68a56B5f804c1947",
        "token_address": "0x5929dbBc11711D2B9e9ca0752393C70De74261F5",
        "whale":"0xde64f98baece7282973ce8d67cd73455d4748673",
    }, # NOTE Works
    "MAI_FRAX": {
        "name":"StrategyThenaMAI_FRAX",
        "masterChef":"0x556b0b722cc72369cea0ea9c4726a71fb2d1772d",
        "token_address": "0x49ad051F4263517BD7204f75123b7C11aF9Fd31C",
        "whale":"0xb4ce0c954bb129d8039230f701bb6503dca1ee8c",
    }, # NOTE Works
    "USDT_FRAX": {
        "name":"StrategyThenaUSDT_FRAX",
        "masterChef":"0x4b1f8ac4c46348919b70bcab62443eeafb770aa4",
        "token_address": "0x8D65dBe7206A768C466073aF0AB6d76f9e14Fc6D",
        "whale":"0x1c6c2498854662fdeadbc4f14ea2f30ca305104b",
    }, # NOTE Works
    "USDT_USDC": {
        "name":"StrategyThenaUSDT_USDC",
        "masterChef":"0x19beb32dc0fb085ef372e96e946be21ecee3fc51",
        "token_address": "0x618f9Eb0E1a698409621f4F487B563529f003643",
        "whale":"0x84912149f93d963ad5ddc3c2781b1950d160a4da",
    }, # NOTE Works
    "USDT_BUSD": {
        "name":"StrategyThenaUSDT_BUSD",
        "masterChef":"0x41ada56dd5702906549a71666541a39b0dbceb12",
        "token_address": "0x6321B57b6fdc14924be480c54e93294617E672aB",
        "whale":"0x82fa32993fff3bc87777136d28935b9e89a6195d",
    }, # NOTE Works
}

strat = stratConfig["USDT_BUSD"]
print("strat", strat)


@pytest.fixture
def gov(accounts):
    yield accounts[0]

@pytest.fixture
def rewards(accounts):
    yield accounts[0]

@pytest.fixture
def guardian(accounts):
    yield accounts[0]

@pytest.fixture
def management(accounts):
    yield accounts[0]

@pytest.fixture
def keeper(accounts):
    yield accounts[0]

@pytest.fixture
def strategist(accounts):
    yield accounts[0]

@pytest.fixture
def user(accounts):
    yield accounts[7]

@pytest.fixture
def user2(accounts):
    yield accounts[8]

@pytest.fixture
def user3(accounts):
    yield accounts[9]

@pytest.fixture
def userWithDAI(accounts):
    yield accounts.at("0xf89d7b9c864f589bbf53a82105107622b35eaa40", force=True)

@pytest.fixture
def userWithWeth(accounts):
    yield accounts.at("0x5AA53f03197E08C4851CAD8C92c7922DA5857E5d", force=True)

@pytest.fixture
def token():
    # address of the ERC-20 used by the strategy/vault (DAI) VolatileV1 AMM - GHNY/WBNB
    yield Contract.from_explorer(strat["token_address"])

@pytest.fixture
def thenaReward():
    reward_address = "0xF4C8E32EaDEC4BFe97E0F595AdD0f4450a863a11"
    yield Contract.from_explorer(reward_address)
    
@pytest.fixture
def thenaReward_whale(accounts):
    whale_address = "0x000000000000000000000000000000000000dead"
    yield accounts.at(whale_address, force=True)

@pytest.fixture
def amount(accounts, token, user):
    amount = 80 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at(strat["whale"], force=True)
    token.transfer(user, amount, {"from": reserve})
    yield amount
    
@pytest.fixture
def amount2(accounts, token, user2):
    amount = 30 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at(strat["whale"], force=True)
    token.transfer(user2, amount, {"from": reserve})
    yield amount

@pytest.fixture
def amount3(accounts, token, user3):
    amount = 10 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at(strat["whale"], force=True)
    token.transfer(user3, amount, {"from": reserve})
    yield amount

@pytest.fixture
def weth():
    token_address = "0x5AA53f03197E08C4851CAD8C92c7922DA5857E5d"
    yield Contract.from_explorer(token_address)

@pytest.fixture
def dai():
    token_address = "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3"
    yield Contract.from_explorer(token_address)

@pytest.fixture
def weth_amount(user, weth):
    weth_amount = 10 ** weth.decimals()
    user.transfer(weth, weth_amount)
    yield weth_amount

@pytest.fixture(scope="module")
def masterChef():
    masterChef = strat["masterChef"]
    yield masterChef

@pytest.fixture(scope="module")
def thenaLp():
    thenaLp = strat["token_address"]
    yield thenaLp

@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    vault.setManagementFee(0,{"from":gov})
    vault.setPerformanceFee(0,{"from":gov})
    yield vault

@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, gov, masterChef, thenaLp):
    strategy = strategist.deploy(
        Strategy,
        vault,
        masterChef,
        thenaLp,
    )    
    # strategy = deployStrategy(Strategy, strategist, gov ,vault)
    strategy.setKeeper(keeper)
    strategy.setDust(1e5, 1e5, {"from" :gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    # addHealthCheck(strategy, gov, gov)
    yield strategy

def deployStrategy(Strategy, strategist, gov, vault):
    return deploy(Strategy, strategist, gov, vault)



@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    # yield 1e-3 # 0.01% of slippage
    # yield 1e-2 # 0.1% of slippage
    yield 1e-2 # 0.1% of slippage

# Function scoped isolation fixture to enable xdist.
# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass
