import csv
import subprocess
import json
import tempfile
import os
import shutil
import argparse

# This script requires the 'anystyle' command-line tool to be installed.
# See https://anystyle.io/ for installation instructions.

def is_anystyle_installed():
    """Check if the anystyle command is in the system's PATH."""
    return shutil.which('anystyle') is not None

def parse_references_from_file(filepath):
    """
    Calls the anystyle command-line tool to parse a file of references.
    """
    command = ['anystyle', '--stdout', '-f', 'json', 'parse', filepath]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error parsing references from file: {filepath}")
        print(f"Stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from anystyle output: {e}")
        print(f"Raw output was: {result.stdout}")
        return None

def is_journal_article(parsed_reference):
    """
    Checks if a parsed reference is a journal article.
    """
    return parsed_reference and parsed_reference.get('type') == 'article-journal'

def main(input_file, output_file):
    """
    Reads patent references from a CSV file, parses them,
    and filters for journal articles.
    """
    if not is_anystyle_installed():
        print("Error: 'anystyle' command not found. Please install it from https://anystyle.io/")
        return

    original_rows = []
    with open(input_file, 'r') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        for row in reader:
            original_rows.append(row)

    # Use a temporary file to pass references to anystyle
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_f:
        temp_filepath = temp_f.name
        for row in original_rows:
            temp_f.write(row['other_reference_text'] + '\n')

    parsed_references = parse_references_from_file(temp_filepath)

    # Clean up the temporary file
    os.remove(temp_filepath)

    if parsed_references:
        with open(output_file, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            # Assuming the output from anystyle preserves the input order
            for i, parsed_ref in enumerate(parsed_references):
                if is_journal_article(parsed_ref):
                    writer.writerow(original_rows[i])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filter journal articles from a patent reference CSV file.')
    parser.add_argument('input_file', help='The path to the input CSV file.')
    parser.add_argument('output_file', help='The path to the output CSV file.')
    args = parser.parse_args()
    main(args.input_file, args.output_file)
