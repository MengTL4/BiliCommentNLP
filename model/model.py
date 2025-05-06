from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ReqRespondModel:
    code: int
    respDict: dict
    respText: str

    def is_success(self):
        return 200 <= self.code < 300

