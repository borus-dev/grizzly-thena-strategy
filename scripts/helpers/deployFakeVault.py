from pathlib import Path

from brownie import config, Contract, accounts, project

API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault

def main():
  gov = accounts[0]
  token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"  # this should be the address of the ERC-20 used by the strategy/vault (DAI)
  token =  Contract.from_explorer(token_address)
  vault = gov.deploy(Vault)
  vault.initialize(token, gov, gov, "", "", gov, gov)
  vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
  vault.setManagement(gov, {"from": gov})
  vault.setManagementFee(0,{"from":gov})
  vault.setPerformanceFee(0,{"from":gov})