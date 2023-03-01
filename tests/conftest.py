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
        "name":"StrategyThenaGHNY_BNB",
        "masterChef":"0x42EcaE09934DC71af220c84663c0A5C835DD0fC8",
        "token_address": "0xA97E46DC17e2b678e5f049A2670fAe000b57F05E",
        "whale":"0x1c6c2498854662fdeadbc4f14ea2f30ca305104b",
    }, # NOTE Works
    "XCAD_BUSD": {
        "name":"StrategyThenaXCAD_BUSD",
        "masterChef":"0x8395bC73C80a689F57bD987594936E15eA741C45",
        "token_address": "0x8dDc543CB4Be74D8A4979DcCFC79C18BdEFd2Dad",
        "whale":"0xde64f98baece7282973ce8d67cd73455d4748673",
    }, # NOTE Works
    "XCAD_BNB": {
        "name":"StrategyThenaXCAD_BNB",
        "masterChef":"0xA6fccd530AE7C4de8bCA9fF28403ea49637780Bf",
        "token_address": "0x3Ec80A1f547ee6FD5D7FC0DC0C1525Ff343D087C",
        "whale":"0xde64f98baece7282973ce8d67cd73455d4748673",
    }, # NOTE Works
    "DOLA_CUSD": {
        "name":"StrategyThenaDOLA_CUSD",
        "masterChef":"0xC2B56de677e6d35327E1Cf3dAF2357f20a4c8692",
        "token_address": "0x7061F52ed4942021924745D454d722E52e057e03",
        "whale":"0xde64f98baece7282973ce8d67cd73455d4748673",
    },  # NOTE CUSD does not have pools to switch for BNB only BUSD
        "DOLA_BNB": {
        "name":"StrategyThenaDOLA_CUSD",
        "masterChef":"0xA71bF9252106aB196F0494F5eCe149e71807c1eC",
        "token_address": "0xc5856601712E8a74d57cdc7a47fB1B41C1a6Fae2",
        "whale":"0xde64f98baece7282973ce8d67cd73455d4748673",
    },  # NOTE No whale available
    "DEUS_BNB": {
        "name":"StrategyThenaDEUS_BNB",
        "masterChef":"0x04034f879a737233bf0ef278b50fd06cc70c87e4",
        "token_address": "0xC8Da40f8A354530F04CE2dDe98Ebc2960a9eA449",
        "whale":"0x1c6c2498854662fdeadbc4f14ea2f30ca305104b",
    }, # NOTE Works
    "MULTI_BNB": {
        "name":"StrategyThenaMULTI_BNB",
        "masterChef":"0x8e89554687Aa59763362a32Da0117D70a72f568B",
        "token_address": "0x075E794F631eE81df1aadB510aC6Ec8803B0FA35",
        "whale":"0xde64f98baece7282973ce8d67cd73455d4748673",
    }, # NOTE Works
    "THENA_BNB": {
        "name":"StrategyThenaTHENA_BNB",
        "masterChef":"0x638b0cc37ffe5a040079F75Ae6C50C9A386dDCaF",
        "token_address": "0x63Db6ba9E512186C2FAaDaCEF342FB4A40dc577c",
        "whale":"0x1c6c2498854662fdeadbc4f14ea2f30ca305104b",
    }, # NOTE Works
    "THENA_BUSD": {
        "name":"StrategyThenaTHENA_BUSD",
        "masterChef":"0x8a8Ec422Fc51B2A88dD5BE489C40aAF1E1fa73d0",
        "token_address": "0x34B897289fcCb43c048b2Cea6405e840a129E021",
        "whale":"0x87f1f1f22f02c46ea3649a326cafba2c7a1df6b1",
    }, # NOTE Works
    "TAROT_BNB": {
        "name":"StrategyThenaTAROT_BNB",
        "masterChef":"0xf49bff8fb6a0ad43475d28be955e62c10c50a998",
        "token_address": "0xB2604B72b3Aa4aF8d0419c736de2D261b40ec755",
        "whale":"0x3c9ee43b96bd5d3a7060ace8c98d75736a1ebc67",
    }, # NOTE Works
    "LQDR_BNB": {
        "name":"StrategyThenaLQDR_BNB",
        "masterChef":"0x3b6321dc8e795ca8175656981e229b47f4f7c015",
        "token_address": "0xEC4484c7F7671914E897b1AEb8418Fe12E320f21",
        "whale":"0x3cde01de3bc9aedb7e363646c7e4b0ae23a81d6f",
    }, # NOTE Works
    "DAO_BNB": {
        "name":"StrategyThenaDAO_BNB",
        "masterChef":"0x82a41d1f472e5f26e6b591e427cde31932c0f5f1",
        "token_address": "0x948c553d8c25ad7bd034086f0aae9a9d3c028b90",
        "whale":"0xdab0e1a3bfe3388ad641a780d0cbe70a6e3af2a6",
    }, # NOTE Works
    "FIL_BNB": {
        "name":"StrategyThenaFIL_BNB",
        "masterChef":"0xb67505085e556765cd5a0c3cde2d15794c3119b5",
        "token_address": "0x1f06C7E323Bc3A5C94Bb6B760C128830cDF6ADfB",
        "whale":"0x1c6c2498854662fdeadbc4f14ea2f30ca305104b",
    }, # NOTE Works
    "stkBNB_BNB": {
        "name":"StrategyThenaStkBNB_BNB",
        "masterChef":"0xf26c84237f6c4a2268ac1d699475d2e07689ffb4",
        "token_address": "0x2B3510f57365aA17bFF8E6360EA67C136175dC6D",
        "whale":"0xfb4d6e2601477f03a7e1ba72a44fa6d68d446ad7",
    }, # NOTE Works
    "BNBx_BNB": {
        "name":"StrategyThenaBNBx_BNB",
        "masterChef":"0x0df5dfe92a0568373da2d705cdb5f68017c4b19a",
        "token_address": "0x6c83E45fE3Be4A9c12BB28cB5BA4cD210455fb55",
        "whale":"0x75db63125a4f04e59a1a2ab4acc4fc1cd5daddd5",
    }, # NOTE Works
}

strat = stratConfig["BNBx_BNB"]
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
    amount = 3 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at(strat["whale"], force=True)
    token.transfer(user, amount, {"from": reserve})
    yield amount
    
@pytest.fixture
def amount2(accounts, token, user2):
    amount = 2 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at(strat["whale"], force=True)
    token.transfer(user2, amount, {"from": reserve})
    yield amount

@pytest.fixture
def amount3(accounts, token, user3):
    amount = 1 * 10 ** token.decimals()
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
    strategy.setDust(1e10, 1e10, {"from" :gov})
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
