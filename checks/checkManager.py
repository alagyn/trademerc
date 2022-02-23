from typing import List

from checks import Check


class CheckManager:
    def __init__(self, checks: List[Check]):
        self.checks = checks

    def update(self):
        for x in self.checks:
            x.update()