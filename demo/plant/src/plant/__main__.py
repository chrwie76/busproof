"""Start one unit: `python -m plant capper`. The same image, a different argument."""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

from plant.capper import Capper
from plant.contracts import read_plan, read_unit
from plant.filler import Filler
from plant.inspector import Inspector
from plant.link import serve
from plant.machine import Machine
from plant.scu import Scu

MACHINES: dict[str, type[Machine]] = {"filler": Filler, "capper": Capper, "inspector": Inspector}


def build(name: str, contracts: Path, config: dict) -> Machine:
    unit = read_unit(contracts, name)
    start = config["units"][name]
    acting = config["acting_seconds"]
    if name == "scu":
        return Scu(unit, read_plan(contracts), start, acting, config["silence_seconds"])
    return MACHINES[name](unit, start, acting)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="plant")
    parser.add_argument("unit", choices=[*sorted(MACHINES), "scu"])
    name = parser.parse_args().unit

    contracts = Path(os.environ["PLANT_CONTRACTS"])
    config_file = Path(os.environ["PLANT_CONFIG"])
    # Said at every start: which files this unit really follows.
    logging.getLogger("plant").info("contracts from %s, config from %s", contracts, config_file)
    config = json.loads(config_file.read_text())

    unit = build(name, contracts, config)
    url = os.environ["PLANT_MQTT_URL"]
    asyncio.run(serve(unit, url, config["tick_seconds"], config["report_seconds"]))


if __name__ == "__main__":
    main()
