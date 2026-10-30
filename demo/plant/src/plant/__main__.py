"""Start one machine: `python -m plant capper`. The same image, a different argument."""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

from plant.capper import Capper
from plant.contracts import read_unit
from plant.link import serve
from plant.machine import Machine

MACHINES: dict[str, type[Machine]] = {"capper": Capper}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="plant")
    parser.add_argument("machine", choices=sorted(MACHINES))
    name = parser.parse_args().machine

    contracts = Path(os.environ["PLANT_CONTRACTS"])
    config_file = Path(os.environ["PLANT_CONFIG"])
    # Said at every start: which files this machine really follows.
    logging.getLogger("plant").info("contracts from %s, config from %s", contracts, config_file)
    config = json.loads(config_file.read_text())

    machine = MACHINES[name](
        read_unit(contracts, name), config["machines"][name], config["acting_seconds"]
    )
    url = os.environ["PLANT_MQTT_URL"]
    asyncio.run(serve(machine, url, config["tick_seconds"], config["report_seconds"]))


if __name__ == "__main__":
    main()
