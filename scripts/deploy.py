from pathlib import Path

from brownie import Strategy, accounts, config, network, project, web3
from eth_utils import is_checksum_address
import click

API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault


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


def main():
    print(f"You are using the '{network.show_active()}' network")
    dev = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))
    print(f"You are using: 'dev' [{dev.address}]")

    if input("Is there a Vault for this strategy already? y/[N]: ").lower() == "y":
        vault = Vault.at(get_address("Deployed Vault: "))
        assert vault.apiVersion() == API_VERSION
    else:
        print("You should deploy one vault using scripts from Vault project")
        return  # TODO: Deploy one using scripts from Vault project

    print(
        f"""
    Strategy Parameters

       api: {API_VERSION}
     token: {vault.token()}
      name: '{vault.name()}'
    symbol: '{vault.symbol()}'
    """
    )
    publish_source = click.confirm("Verify source on bscscan?")
    if input("Deploy Strategy? y/[N]: ").lower() != "y":
        return

    deployArgs = [
      vault, 
      "0x1520D103D8B366C87A0b273E68a56B5f804c1947", # _masterChef
      "0x5929dbBc11711D2B9e9ca0752393C70De74261F5", # _thenaLp
    ]

    strategy = Strategy.deploy(
        *deployArgs, {"from": dev}, publish_source=publish_source
    )

    addHealthCheck(strategy, dev)
    
    addStrategy(strategy, vault, dev)

def addHealthCheck(strategy, deployer):
    healthCheck = "0x7578CC483C4a7b0765e1Ab72933877c80f7a1649"
    strategy.setHealthCheck(healthCheck,{"from": deployer})
    return healthCheck

def addStrategy(strategy, vault, deployer):
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": deployer})