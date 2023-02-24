import pytest
from brownie import config, Contract

import sys
import os

script_dir = os.path.dirname( __file__ )
strategyDeploy_dir = os.path.join( script_dir ,  ".." , "scripts" )
sys.path.append( strategyDeploy_dir )

from deployStrategy import addHealthCheck, deploy

stratConfig = {
    "GHNY_BNB": {
        "name":"StrategyThenaGHNY",
        "masterChef":"0x42EcaE09934DC71af220c84663c0A5C835DD0fC8",
        "token_address": "0xA97E46DC17e2b678e5f049A2670fAe000b57F05E",
        "whale":"0x1c6c2498854662fdeadbc4f14ea2f30ca305104b",
    },
    "XCAD": {
        "name":"StrategyThenaGHNY",
        "masterChef":"0x42EcaE09934DC71af220c84663c0A5C835DD0fC8",
        "token_address": "0xA97E46DC17e2b678e5f049A2670fAe000b57F05E",
        "whale":"0x1c6c2498854662fdeadbc4f14ea2f30ca305104b",
    },
}

strat = stratConfig["GHNY_BNB"]

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
    yield accounts.at("0x59ABf3837Fa962d6853b4Cc0a19513AA031fd32b", force=True)

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
    amount = 1 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x1c6c2498854662fdeadbc4f14ea2f30ca305104b", force=True)
    token.transfer(user, amount, {"from": reserve})
    yield amount
    
@pytest.fixture
def amount2(accounts, token, user2):
    amount = 0.4 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x1c6c2498854662fdeadbc4f14ea2f30ca305104b", force=True)
    token.transfer(user2, amount, {"from": reserve})
    yield amount

@pytest.fixture
def amount3(accounts, token, user3):
    amount = 1.2 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x2958c114b7dbad13605197be74eb78b58350d6d0", force=True)
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
    strategy.setDust(1e17, 1e17, {"from" :gov})
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
