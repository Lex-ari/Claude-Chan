#!/usr/bin/env python3
"""
Helper module to send expressions to the display
"""
import socket
import json

def send_expression(image_name, host='localhost', port=9876):
    """Send an expression to the display window"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            message = json.dumps({"image": image_name})
            s.sendall(message.encode('utf-8'))
            return True
    except Exception as e:
        print(f"Failed to send expression: {e}")
        return False

# Available expressions (matching PNG files in expressions directory)
EXPRESSIONS = [
    'angry',
    'annoyed',
    'biting_nails',
    'bored',
    'cheerful',
    'confused',
    'determined',
    'embarrassed',
    'flustered',
    'grumpy',
    'happy',
    'hiding',
    'laughing',
    'neutral',
    'playful',
    'pouting',
    'sad',
    'serious',
    'shy',
    'sleepy',
    'smug',
    'talking',
    'teasing',
    'thinking',
]

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python send_expression.py <expression_name>")
        print(f"Available expressions: {', '.join(EXPRESSIONS)}")
        sys.exit(1)

    expr_name = sys.argv[1].lower()
    if send_expression(expr_name):
        print(f"Sent: {expr_name}")
