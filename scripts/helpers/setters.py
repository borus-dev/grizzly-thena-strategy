from pathlib import Path

from brownie import Strategy, accounts, config, network, project, web3, CommonHealthCheck
from eth_utils import is_checksum_address
import click


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault

# Set Health Check lossLimit
def main():
    print(f"You are using the '{network.show_active()}' network")

    print("""------- SET HEALTHCHECK Loss Limit -------""")

    gov = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))

    healthCheck =  CommonHealthCheck.at("")

    healthCheck.setlossLimitRatio(150, {"from":gov})

    print(f"Getting Health Check params..." )
    lossLimitRatio = healthCheck.lossLimitRatio()
    profitLimitRatio = healthCheck.profitLimitRatio()
    print(f"lossLimitRatio: {lossLimitRatio}")
    print(f"profitLimitRatio: {profitLimitRatio}")

# Update Strategy Debt Ratio
def main():
    print(f"You are using the '{network.show_active()}' network")

    vault = Vault.at("")
    strategy = Strategy.at("")
    debtRatio = 100
    print(f"""    
        Update strategy -- DEBT RATIO --
        --------------------------------------------------

        Vault
        ------
        -> name: {vault.name()}
        -> address: {vault.address}

        Strategy
        --------
        -> name: {strategy.name()}
        -> address: {strategy.address}

        Params
        -------
        -> debt ratio: {debtRatio}
    """)
   
    gov = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))

    print(f"""Updating strategy: {strategy} """)
    # Update Strategy Debt Ratio to 10%
    vault.updateStrategyDebtRatio(strategy.address, debtRatio, {"from": gov})

    strategyInfo = vault.strategies(strategy)
    print(f"strategyInfo {strategy}: {strategyInfo}")

# Change Deposit Limit
def main():
    print(f"You are using the '{network.show_active()}' network")

    print("""------- CHANGE DEPOSIT LIMIT -------""")

    gov = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))

    vault = Vault.at("")

    vault.setDepositLimit(30_000_000_000_000_000_000_000, {"from": gov})

    print(f"Done!!!")
    

def get_address(msg: str, default: str = None) -> str:
    val = click.prompt(msg, default=default)

    Keep asking user for click.prompt until it passes
    while True:

        if is_checksum_address(val):
            return val
        elif addr := web3.ens.address(val):
            click.echo(f"Found ENS '{val}' [{addr}]")
            return addr

        click.echo(
            f"I'm sorry, but '{val}' is not a checksummed address or valid ENS record"
        )
        NOTE: Only display default once
        val = click.prompt(msg)
    
