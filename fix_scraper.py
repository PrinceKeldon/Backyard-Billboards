#!/usr/bin/env python3

with open("scraper.py", "r") as f:
    content = f.read()

# Find the integrate_external_data function definition
start_string = "@staticmethod\ndef integrate_external_data(deals, api_type=None):"
end_string = "        return deals\n        \n    except Exception as e:\n        logger.error(f\"Error enriching deals with external data: {str(e)}\")\n        return deals"

# Get the complete function
full_function = content[content.find(start_string):content.find(end_string) + len(end_string)]

# Find any duplicates of this function
if content.count(full_function) > 1:
    # Replace only the second occurrence
    parts = content.split(full_function, 2)
    content = parts[0] + full_function + parts[2]

# Fix any unterminated triple quotes
if '"""' in content:
    count = content.count('"""')
    if count % 2 != 0:  # Odd number of """ means unterminated
        content = content.replace('"""', '"""', count - 1) + '"""'

with open("scraper.py", "w") as f:
    f.write(content)

print("Fixed scraper.py")
