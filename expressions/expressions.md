# Claude Expression Display

A visual personality display for Claude that shows current expressions/emotions in a separate GUI window.

## Components

1. **expression_display.py** - Main GUI application that displays expression images
2. **send_expression.py** - Helper to send expression updates from Claude
3. **Expression images** - PNG files in the same directory

## Usage

### Start the display window:
```bash
python expression_display.py
```

The window will open and listen on `localhost:9876` for expression updates.

### Send expressions from Claude:
```bash
python send_expression.py thinking
python send_expression.py happy
python send_expression.py angry
```

### From Python code:
```python
from send_expression import send_expression, EXPRESSIONS

# Send any expression
send_expression('thinking')
send_expression('happy')

# See available expressions
print(EXPRESSIONS)
```

## Available Expressions

- angry
- annoyed
- biting_nails
- bored
- cheerful
- confused
- determined
- embarrassed
- flustered
- grumpy
- happy
- hiding
- laughing
- neutral
- playful
- pouting
- sad
- serious
- shy
- sleepy
- smug
- talking
- teasing
- thinking

## Protocol

The display accepts JSON messages over TCP:
```json
{"image": "thinking"}
```

Images are automatically resized to fit (max 380x380px).
