from pathlib import Path

from brownie import config, network, project, CommonHealthCheck
from eth_utils import is_checksum_address


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault


# Get Health Check value
def main():
    print(f"You are using the '{network.show_active()}' network")

    print(f"Getting Health Check params..." )
    print("""------------------ GETTING HS PARAMS ----------------""")
    healthCheck =  CommonHealthCheck.at("0x72f8ac48eb2a90876b3fa20016d6531319ec7b03")

    lossLimitRatio = healthCheck.lossLimitRatio()
    profitLimitRatio = healthCheck.profitLimitRatio()
    print(f"lossLimitRatio: {lossLimitRatio}")
    print(f"profitLimitRatio: {profitLimitRatio}")

    