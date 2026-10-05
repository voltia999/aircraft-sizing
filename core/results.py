from dataclasses import dataclass, field


@dataclass
class Result():
    w0: float
    wf_w0: float
    we_w0: float
    history: list = field(default_factory=list)
    case: str = "first-order"

    @property
    def w_empty(self) -> float:
        return self.we_w0 * self.w0

    @property
    def w_fuel(self) -> float:
        return self.wf_w0 * self.w0
