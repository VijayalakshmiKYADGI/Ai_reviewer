import json
import re
import os
import sys

#python json_cleanup_tool.py path\to\your\file.json
def strip_ansi_codes(text):
    """
    Removes ANSI escape sequences from a string.
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def cleanup_corrupted_json(input_file):
    """
    Cleans up a corrupted JSON file by:
    1. Preserving only '[index].message' entries.
    2. Stripping unnecessary ANSI escape sequences and decorative characters.
    3. Converting the result into a flat list of message strings.
    """
    output_file = input_file + ".tmp"
    cleaned_data = {}

    print(f"Reading {input_file}...")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Pattern to match: "[number].message": "..."
                match = re.search(r'"\[(\d+)\]\.message":\s*(".*")', line)
                if match:
                    index = match.group(1)
                    message_raw = match.group(2).strip()
                    
                    if message_raw.endswith(','):
                        message_raw = message_raw[:-1]
                    
                    try:
                        message_val = json.loads(message_raw)
                    except Exception:
                        message_val = message_raw.strip('"')

                    cleaned_msg = strip_ansi_codes(message_val)
                    cleaned_msg = cleaned_msg.replace('│', '').strip()

                    cleaned_data[int(index)] = cleaned_msg

        if not cleaned_data:
            print("No valid message entries found.")
            return

        # Sort by index and then take only the values
        sorted_indices = sorted(cleaned_data.keys())
        final_list = [cleaned_data[i] for i in sorted_indices]

        print(f"Writing cleaned data (preserved {len(final_list)} entries as a list)...")
        with open(output_file, 'w', encoding='utf-8') as f:
            # We wrap the results in a new structured object or just a plain list. 
            # Given the request "keep values only", a list is most efficient.
            json.dump({"messages": final_list}, f, indent=4, ensure_ascii=False)

        os.replace(output_file, input_file)
        print(f"Successfully cleaned: {input_file}")

    except Exception as e:
        print(f"An error occurred: {e}")
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    # Default target file or use command line argument
    target = r'c:\AI-reviwer\Ai_reviewer\hjsbhjsdbcjd.json'
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    if os.path.exists(target):
        cleanup_corrupted_json(target)
    else:
        print(f"File not found: {target}")
