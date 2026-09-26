# Calculator

A desktop calculator inspired by the Windows calculator, built with Python and Tkinter.

## Features

- Addition, subtraction, multiplication and division
- Percent, 1/x, x², square root and +/-
- CE, C and backspace
- Precise decimal math (0.1 + 0.2 = 0.3)
- History panel: click a past result to reuse it
- Clear error messages such as "Cannot divide by zero"
- Keyboard support

## How to run

Requires Python 3.9 or newer (Tkinter is included with Python).

```bash
python main.py
```

## Keyboard shortcuts

| Key | Action |
|---|---|
| 0-9, `.` | Enter numbers |
| `+` `-` `*` `/` | Operators |
| Enter or `=` | Equals |
| Backspace | Delete last digit |
| Esc | Clear (C) |
| Delete | Clear entry (CE) |
| `%` | Percent |
| `r` / `q` / `@` | 1/x / x² / square root |
| F9 | +/- |
| Ctrl+H | Show history |
| Ctrl+C / Ctrl+V | Copy / paste |

## Project structure

- `calculator.py` - calculation logic
- `main.py` - user interface
