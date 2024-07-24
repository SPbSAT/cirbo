import typing as tp


CnfRaw = list[list[int]]


class Cnf:
    def __init__(self, cnf: CnfRaw):
        self._cnf = cnf
