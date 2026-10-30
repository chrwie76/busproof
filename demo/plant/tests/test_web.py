"""The page stays what it claims: built from the contracts, with libraries that are what we took."""

import hashlib
import re
from pathlib import Path

from plant.machine import Machine
from plant.scu import Scu

WEB = Path(__file__).parents[1] / "web"
PAGE = (WEB / "index.html").read_text()


def page_list(name: str) -> set[str]:
    found = re.search(rf"const {name} = \[(.*?)\];", PAGE)
    assert found, name
    return set(re.findall(r'"(\w+)"', found[1]))


def test_the_page_offers_exactly_the_faults_there_are():
    assert page_list("FAULTS") == set(Machine.faults)
    assert page_list("FAULTS") | page_list("SCU_FAULTS") == set(Scu.faults)


def test_the_page_names_no_topic_it_could_read_from_a_contract():
    assert "acme" not in PAGE
    assert "packaging/" not in PAGE


def test_the_page_loads_nothing_from_the_internet():
    assert not re.search(r"""(src|href)=["']https?:""", PAGE)


def test_the_vendored_libraries_are_the_ones_the_readme_names():
    readme = (WEB / "vendor" / "README.md").read_text()

    for library in ("mqtt.min.js", "js-yaml.min.js"):
        digest = hashlib.sha256((WEB / "vendor" / library).read_bytes()).hexdigest()
        assert digest in readme, library
