"""Mean reversion strategy — ο κοινός, καθαρός πυρήνας λογικής.

Σχεδιαστική αρχή (κεντρική στην εργασία): η στρατηγική είναι μια ντετερμινιστική
συνάρτηση των δεδομένων. Δεν κάνει I/O, δεν αγγίζει βάση/exchange/δίκτυο, και δεν
εξαρτάται από numpy/pandas — μόνο την stdlib. Το ίδιο αντικείμενο τρέχει αυτούσιο
στο backtesting (ιστορικά κεριά) και στον live executor (streaming κεριά).

Λογική (long-only mean reversion):
  * ΕΙΣΟΔΟΣ (BUY): όταν η τιμή πέσει στο/κάτω από την κάτω Bollinger band
    (ισοδύναμα z-score ≤ -num_std) -> oversold, αναμένουμε επαναφορά προς τον μέσο.
  * ΕΞΟΔΟΣ (SELL): όταν η τιμή επιστρέψει στον/πάνω από τον κινητό μέσο
    (z-score ≥ exit_z) -> κλείσιμο θέσης.
  * Αλλιώς: HOLD.

Η μέθοδος evaluate() δέχεται την τρέχουσα θέση (in_position) ως όρισμα αντί να την
κρατά η ίδια — παραμένει έτσι καθαρή. Ο caller (backtester ή executor) περνά την
προσομοιωμένη ή την πραγματική θέση.
"""
import statistics
from dataclasses import dataclass
from enum import Enum

from app.models.market import Candle


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Decision:
    signal: Signal
    price: float
    mean: float | None
    std: float | None
    upper: float | None
    lower: float | None
    z_score: float | None
    reason: str


class MeanReversionStrategy:
    def __init__(self, window: int = 20, num_std: float = 2.0, exit_z: float = 0.0):
        if window < 2:
            raise ValueError("window πρέπει να είναι >= 2")
        self.window = window
        self.num_std = num_std
        self.exit_z = exit_z

    def evaluate(self, candles: list[Candle], in_position: bool = False) -> Decision:
        closes = [c.close for c in candles]
        price = closes[-1] if closes else 0.0

        if len(closes) < self.window:
            return Decision(Signal.HOLD, price, None, None, None, None, None,
                            "warmup: ανεπαρκή δεδομένα")

        window = closes[-self.window:]
        mean = statistics.fmean(window)
        std = statistics.pstdev(window)
        upper = mean + self.num_std * std
        lower = mean - self.num_std * std
        z = (price - mean) / std if std > 0 else 0.0

        if not in_position:
            if price <= lower:
                return Decision(Signal.BUY, price, mean, std, upper, lower, z,
                                "τιμή ≤ κάτω band (oversold) -> είσοδος")
            return Decision(Signal.HOLD, price, mean, std, upper, lower, z, "καμία είσοδος")
        else:
            if z >= self.exit_z:
                return Decision(Signal.SELL, price, mean, std, upper, lower, z,
                                "επαναφορά στον μέσο -> έξοδος")
            return Decision(Signal.HOLD, price, mean, std, upper, lower, z, "διατήρηση θέσης")
