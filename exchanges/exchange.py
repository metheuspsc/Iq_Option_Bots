from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class Exchange(ABC):
    username: str
    password: str
    account_type: str

    @property
    @abstractmethod
    def api(self):
        pass

    @property
    @abstractmethod
    def balance(self) -> float:
        pass

    @abstractmethod
    def candles_to_df(self, pair) -> pd.DataFrame:
        pass
