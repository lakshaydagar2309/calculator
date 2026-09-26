from decimal import Decimal, InvalidOperation, getcontext

getcontext().prec = 34

MAX_DIGITS = 16
LIMIT = Decimal("1e10000")
SYMBOLS = {"+": "+", "-": "−", "*": "×", "/": "÷"}


class CalcError(Exception):
    pass


def format_number(value):
    if value.is_zero():
        return "0"
    value = Decimal(format(value, f".{MAX_DIGITS}g")).normalize()
    exponent = value.adjusted()
    if exponent >= MAX_DIGITS or exponent < -7:
        mantissa = format(value.scaleb(-exponent).normalize(), "f")
        sign = "+" if exponent > 0 else "-"
        return f"{mantissa}e{sign}{abs(exponent)}"
    return format_entry(format(value, "f"))


def format_entry(text):
    sign = "-" if text.startswith("-") else ""
    text = text.lstrip("-")
    whole, dot, frac = text.partition(".")
    return f"{sign}{int(whole or '0'):,}{dot}{frac}"


class Calculator:
    def __init__(self):
        self.history = []
        self.clear()

    def clear(self):
        self.current = Decimal(0)
        self.typing = None
        self.operand_text = None
        self.operand_ready = False
        self.acc = None
        self.op = None
        self.last = None
        self.expression = ""
        self.error = None
        self.just_evaluated = False

    @property
    def display(self):
        if self.error:
            return self.error
        if self.typing is not None:
            return format_entry(self.typing)
        return format_number(self.current)

    def input_digit(self, digit):
        self._begin_entry()
        if sum(ch.isdigit() for ch in self.typing) >= MAX_DIGITS and self.typing not in ("0", "-0"):
            return
        if self.typing in ("0", "-0"):
            self.typing = self.typing[:-1] + digit
        else:
            self.typing += digit
        self.current = Decimal(self.typing)

    def input_decimal(self):
        self._begin_entry()
        if "." not in self.typing:
            self.typing += "."

    def backspace(self):
        if self.error:
            self.clear()
        elif self.just_evaluated:
            self.expression = ""
        elif self.typing is not None:
            self.typing = self.typing[:-1]
            if self.typing in ("", "-", "-0"):
                self.typing = "0"
            self.current = Decimal(self.typing)

    def clear_entry(self):
        if self.error or self.just_evaluated:
            self.clear()
            return
        self.current = Decimal(0)
        self.typing = None
        self.operand_text = None
        self.operand_ready = self.op is not None
        self._refresh_expression()

    def set_operator(self, op):
        if self.error:
            return
        if self.op and self.operand_ready:
            if not self._try(lambda: self._apply(self.acc, self.op, self.current)):
                return
            self.acc = self.current
        elif not self.op:
            self.acc = self.current
        self.op = op
        self.typing = None
        self.operand_text = None
        self.operand_ready = False
        self.just_evaluated = False
        self.expression = f"{format_number(self.acc)} {SYMBOLS[op]}"

    def equals(self):
        if self.error:
            self.clear()
            return
        if self.op:
            operand = self.current if self.operand_ready else self.acc
            text = self.operand_text or format_number(operand)
            expression = f"{format_number(self.acc)} {SYMBOLS[self.op]} {text} ="
            self.last = (self.op, operand)
            left, op = self.acc, self.op
        elif self.last:
            op, operand = self.last
            expression = f"{format_number(self.current)} {SYMBOLS[op]} {format_number(operand)} ="
            left = self.current
        else:
            self.expression = f"{self.operand_text or format_number(self.current)} ="
            self._finish()
            return

        self.expression = expression
        self.op = None
        self.acc = None
        if self._try(lambda: self._apply(left, op, operand)):
            self.history.insert(0, (expression, self.current))
            del self.history[20:]
            self._finish()

    def negate(self):
        if self.error:
            return
        if self.typing is not None:
            if self.typing not in ("0", "0."):
                self.typing = self.typing[1:] if self.typing.startswith("-") else "-" + self.typing
                self.current = Decimal(self.typing)
            return
        self._unary("negate", lambda x: -x)

    def reciprocal(self):
        def invert(x):
            if x.is_zero():
                raise CalcError("Cannot divide by zero")
            return 1 / x
        self._unary("1/", invert)

    def square(self):
        self._unary("sqr", lambda x: x * x)

    def square_root(self):
        def root(x):
            if x < 0:
                raise CalcError("Invalid input")
            return x.sqrt()
        self._unary("√", root)

    def percent(self):
        if self.error:
            return
        if self.op in ("+", "-"):
            value = self.acc * self.current / 100
        elif self.op in ("*", "/"):
            value = self.current / 100
        else:
            value = Decimal(0)
        self._set_operand(value, format_number(value))

    def paste(self, text):
        try:
            value = Decimal(text.replace(",", "").strip())
        except InvalidOperation:
            return False
        if not value.is_finite():
            return False
        if self.error or self.just_evaluated:
            self.clear()
        self._set_operand(value, None)
        return True

    def use_history(self, index):
        expression, value = self.history[index]
        self.clear()
        self.current = value
        self.expression = expression
        self.just_evaluated = True

    def clear_history(self):
        self.history.clear()

    def _begin_entry(self):
        if self.error or self.just_evaluated:
            self.clear()
        if self.typing is None:
            self.typing = "0"
            self.operand_text = None
            self.operand_ready = True
            self._refresh_expression()

    def _unary(self, label, fn):
        if self.error:
            return
        text = self.operand_text or format_number(self.current)
        if self.just_evaluated:
            self.expression = ""
        try:
            value = fn(self.current)
        except CalcError as exc:
            self.operand_text = f"{label}({text})"
            self._refresh_expression()
            self.error = str(exc)
            return
        self._set_operand(value, f"{label}({text})")

    def _set_operand(self, value, text):
        if abs(value) >= LIMIT:
            self.error = "Overflow"
            return
        self.current = value
        self.typing = None
        self.operand_text = text
        self.operand_ready = True
        self.just_evaluated = False
        self._refresh_expression()

    def _refresh_expression(self):
        if self.op:
            self.expression = f"{format_number(self.acc)} {SYMBOLS[self.op]}"
            if self.operand_text:
                self.expression += f" {self.operand_text}"
        elif not self.just_evaluated:
            self.expression = self.operand_text or ""

    def _apply(self, a, op, b):
        if op == "+":
            result = a + b
        elif op == "-":
            result = a - b
        elif op == "*":
            result = a * b
        elif b.is_zero():
            raise CalcError("Result is undefined" if a.is_zero() else "Cannot divide by zero")
        else:
            result = a / b
        if abs(result) >= LIMIT:
            raise CalcError("Overflow")
        self.current = result

    def _try(self, action):
        try:
            action()
            return True
        except (CalcError, InvalidOperation) as exc:
            self.error = str(exc) if isinstance(exc, CalcError) else "Invalid input"
            return False

    def _finish(self):
        self.typing = None
        self.operand_text = None
        self.operand_ready = False
        self.just_evaluated = True
