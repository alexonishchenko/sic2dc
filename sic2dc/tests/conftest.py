from pathlib import Path

import pytest

from ruamel.yaml import YAML


@pytest.fixture(scope="function")
def arista_short_str() -> str:
    filename = Path(__file__).parent / Path('./configs/arista1_short.cfg')
    with open(filename, 'r') as f:
        result = f.read()
    return result


@pytest.fixture(scope="function")
def arista_short_dict() -> dict:
    filename = Path(__file__).parent / Path('./configs/arista1_short.yml')
    with open(filename, 'r') as f:
        yaml = YAML(typ='safe')
        result = yaml.load(f)
    return result
