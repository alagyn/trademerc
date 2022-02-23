from typing import List

from checks.check import CheckParent


class CheckManager:
    def __init__(self, checks: List[CheckParent]):
        self.checks = checks

    def update(self, dry: bool):
        for x in self.checks:
            x.update(dry)