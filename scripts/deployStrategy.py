from pathlib import Path
import sys
import os

from brownie import Strategy, accounts, config, network, project, web3
from eth_utils import is_checksum_address
import click

script_dir = os.path.dirname( __file__ )
strategyConfig_dir = os.path.join( script_dir )
sys.path.append( strategyConfig_dir )


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault

def main():
    print(f"You are using the '{network.show_active()}' network")


    vault = Vault.at("")
    strategy = Strategy.at("")

    print(
        f"""
        Strategy
        --------
        ->    name: {strategy.name()}
        ->    address: {strategy}

        Vault
        ------
        ->    name: {vault.name()}
        ->    address: {vault}
        """
    )
    gov = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))

    print(f"You are using: 'dev' [{gov.address}]")

    debt_ratio = 50 # 0.1%
    minDebtPerHarvest = 0  # Lower limit on debt add
    maxDebtPerHarvest = 1e+23 # Upper limit on debt add
    performance_fee = 0 # Strategist perf fee: 0% on basis points
   
    vault.addStrategy(
      strategy,
      debt_ratio,
      minDebtPerHarvest,
      maxDebtPerHarvest,
      performance_fee,
      {"from":gov}
    )

    addHealthCheck(strategy, gov, gov)
    # strategy.setDust(1e6, 0, {"from":gov})
    # strategy.setSecurityFactors(9990, {"from":gov})

def deploy(Strategy, deployer, gov ,vault):

    deployArgs = [
      vault, 
      "0x42EcaE09934DC71af220c84663c0A5C835DD0fC8", # _masterChef
      "0xA97E46DC17e2b678e5f049A2670fAe000b57F05E", # _thenaLp
    ]
    
    strategy = Strategy.deploy(*deployArgs, {"from": deployer})

    return strategy


def addHealthCheck(strategy, gov, deployer):
    healthCheck = "0x9434543bfe2a40cffae0905192fc02d593257348"
    strategy.setHealthCheck(healthCheck,{"from":deployer})
    return healthCheck

def get_address(msg: str, default: str = None) -> str:
    val = click.prompt(msg, default=default)

    # Keep asking user for click.prompt until it passes
    while True:

        if is_checksum_address(val):
            return val
        elif addr := web3.ens.address(val):
            click.echo(f"Found ENS '{val}' [{addr}]")
            return addr

        click.echo(
            f"I'm sorry, but '{val}' is not a checksummed address or valid ENS record"
        )
        # NOTE: Only display default once
        val = click.prompt(msg)
    
