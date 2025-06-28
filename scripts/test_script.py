import os
from pathlib import Path

print("Test script started")

# Test basic file operations
test_file = Path("test_output.txt")
try:
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Test successful!")
    print(f"Successfully wrote to {test_file.absolute()}")
except Exception as e:
    print(f"Error: {e}")

print("Test script completed")
