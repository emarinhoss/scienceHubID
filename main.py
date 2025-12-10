import csv
import subprocess
import json
import tempfile
import os
import shutil
import argparse
import sys

# This script supports two parsers:
# 1. anystyle-cli: https://anystyle.io/
# 2. GROBID: https://grobid.readthedocs.io/

def is_anystyle_installed():
    """Check if the anystyle command is in the system's PATH."""
    return shutil.which('anystyle') is not None

def is_grobid_available():
    """Check if GROBID Python client is installed."""
    try:
        import grobid_client
        return True
    except ImportError:
        return False

def parse_references_anystyle(filepath):
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

def parse_references_grobid(filepath, grobid_server='http://localhost:8070'):
    """
    Uses GROBID to parse a file of references.
    Each line in the file should be a separate reference.
    """
    try:
        from grobid_client.grobid_client import GrobidClient
    except ImportError:
        print("Error: grobid-client-python is not installed.")
        print("Install it with: pip install grobid-client-python")
        return None

    # Create temporary input and output directories
    with tempfile.TemporaryDirectory() as temp_input_dir, \
         tempfile.TemporaryDirectory() as temp_output_dir:

        # Copy the file to the input directory with a .txt extension
        input_filename = 'references.txt'
        input_file_path = os.path.join(temp_input_dir, input_filename)
        shutil.copy(filepath, input_file_path)

        # Initialize GROBID client with server URL
        client = GrobidClient(grobid_server=grobid_server)

        # GROBID expects input directory with .txt files (one reference per line)
        try:
            # Process the citation list
            client.process(
                service="processCitationList",
                input_path=temp_input_dir,
                output=temp_output_dir,
                n=10
            )

            # Read the output XML file
            output_filename = os.path.splitext(input_filename)[0] + '.tei.xml'
            output_path = os.path.join(temp_output_dir, output_filename)

            if not os.path.exists(output_path):
                print(f"Error: GROBID did not produce output file: {output_path}")
                # List files in output directory for debugging
                print(f"Files in output directory: {os.listdir(temp_output_dir)}")
                return None

            # Parse the GROBID XML output
            return parse_grobid_xml(output_path)

        except Exception as e:
            print(f"Error processing with GROBID: {e}")
            print(f"Make sure GROBID server is running at {grobid_server}")
            return None

def parse_grobid_xml(xml_filepath):
    """
    Parse GROBID TEI-XML output to extract reference types.
    Returns a list of parsed references in a format similar to anystyle.
    """
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        print("Error: xml module not available")
        return None

    try:
        tree = ET.parse(xml_filepath)
        root = tree.getroot()

        # Define XML namespace
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

        parsed_refs = []

        # Find all biblStruct elements (each represents a parsed reference)
        for bibl in root.findall('.//tei:biblStruct', ns):
            ref_type = bibl.get('type', 'unknown')

            # Map GROBID types to a common format
            # GROBID uses types like 'article', 'book', etc.
            parsed_ref = {'type': ref_type}

            # Extract analytic (article/chapter) info
            analytic = bibl.find('.//tei:analytic', ns)
            if analytic is not None:
                # If there's an analytic section, it's likely an article
                parsed_ref['type'] = 'article-journal'

            parsed_refs.append(parsed_ref)

        return parsed_refs

    except Exception as e:
        print(f"Error parsing GROBID XML: {e}")
        return None

def is_journal_article(parsed_reference, parser_type='anystyle'):
    """
    Checks if a parsed reference is a journal article.
    Supports both anystyle and GROBID output formats.
    """
    if not parsed_reference:
        return False

    ref_type = parsed_reference.get('type', '')

    if parser_type == 'anystyle':
        return ref_type == 'article-journal'
    elif parser_type == 'grobid':
        # GROBID may use different type names
        return ref_type in ['article-journal', 'article']

    return False

def main(input_file, output_file, parser_type='anystyle', grobid_server='http://localhost:8070'):
    """
    Reads patent references from a CSV file, parses them,
    and filters for journal articles.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        parser_type: 'anystyle' or 'grobid'
        grobid_server: GROBID server URL (only used if parser_type='grobid')
    """
    # Validate parser availability
    if parser_type == 'anystyle':
        if not is_anystyle_installed():
            print("Error: 'anystyle' command not found.")
            print("Install it from https://anystyle.io/")
            print("Or try using --parser grobid instead")
            return
    elif parser_type == 'grobid':
        if not is_grobid_available():
            print("Error: 'grobid-client-python' is not installed.")
            print("Install it with: pip install grobid-client-python")
            print("Or try using --parser anystyle instead")
            return
    else:
        print(f"Error: Unknown parser type '{parser_type}'")
        print("Valid options are: anystyle, grobid")
        return

    # Read input CSV
    original_rows = []
    with open(input_file, 'r') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        for row in reader:
            original_rows.append(row)

    print(f"Read {len(original_rows)} references from {input_file}")

    # Use a temporary file to pass references to the parser
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_f:
        temp_filepath = temp_f.name
        for row in original_rows:
            temp_f.write(row['other_reference_text'] + '\n')

    # Parse references using selected parser
    print(f"Parsing references using {parser_type}...")
    if parser_type == 'anystyle':
        parsed_references = parse_references_anystyle(temp_filepath)
    elif parser_type == 'grobid':
        parsed_references = parse_references_grobid(temp_filepath, grobid_server)

    # Clean up the temporary file
    os.remove(temp_filepath)

    if parsed_references:
        journal_count = 0
        with open(output_file, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            # Assuming the output from parser preserves the input order
            for i, parsed_ref in enumerate(parsed_references):
                if is_journal_article(parsed_ref, parser_type):
                    writer.writerow(original_rows[i])
                    journal_count += 1

        print(f"Found {journal_count} journal articles out of {len(parsed_references)} references")
        print(f"Results written to {output_file}")
    else:
        print("Error: Failed to parse references")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Filter journal articles from a patent reference CSV file.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use anystyle (default)
  python3 main.py input.csv output.csv

  # Use anystyle explicitly
  python3 main.py input.csv output.csv --parser anystyle

  # Use GROBID (requires GROBID server running)
  python3 main.py input.csv output.csv --parser grobid

  # Use GROBID with custom server URL
  python3 main.py input.csv output.csv --parser grobid --grobid-server http://localhost:8080
        """
    )
    parser.add_argument('input_file', help='The path to the input CSV file.')
    parser.add_argument('output_file', help='The path to the output CSV file.')
    parser.add_argument('--parser', choices=['anystyle', 'grobid'], default='anystyle',
                        help='Parser to use: anystyle (default) or grobid')
    parser.add_argument('--grobid-server', default='http://localhost:8070',
                        help='GROBID server URL (default: http://localhost:8070)')
    args = parser.parse_args()
    main(args.input_file, args.output_file, args.parser, args.grobid_server)
