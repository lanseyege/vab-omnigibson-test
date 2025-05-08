import datetime
import json
import sys
from typing import Dict, List, Union

from pydantic import BaseModel, validator

from .general import InstanceFactory, Assignment


class ConcurrencyConfig(BaseModel):
    agent: Dict[str, int]
    task: Dict[str, int]


class DefinitionConfig(BaseModel):
    agent: Dict[str, InstanceFactory]
    task: Dict[str, InstanceFactory]


def get_predefined_structure():
    now = datetime.datetime.now()
    return {
        "TIMESTAMP": now.strftime("%Y-%m-%d-%H-%M-%S"),
        "TIMESTAMP_DATE": now.strftime("%Y-%m-%d"),
        "TIMESTAMP_TIME": now.strftime("%H-%M-%S"),
    }



