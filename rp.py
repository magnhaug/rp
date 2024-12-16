#!/usr/bin/env python3
"""
rp (repo prompt) Command Line Tool
----------------------------------

This tool aggregates file content and prompt templates into a single, well-structured XML prompt,
compatible with https://github.com/mckaywrigley/o1-xml-parser.

Key changes in this version:
- Templates and file contents are now inserted as normal XML text nodes, not wrapped in CDATA.

Usage:
    rp [options] [additional_prompt ...]

Options:
    -p, --prompt <path>    Add a prompt template file. Can be repeated multiple times.
    -l, --list <path>      Add a file containing a newline-separated list of file paths.
                           Each listed file is included as a normal file.
    -f, --file <path>      Add a single file. Can be repeated multiple times.
    -o, --output <path>    Write output to the specified file. Otherwise, print to stdout.
    -s, --silent           Suppress stderr output.

Positional arguments:
    additional_prompt       Any additional string arguments without a flag are treated as
                           inline prompt templates.

Behavior:
    - Reads templates from -p and inline arguments, and files from -f or -l.
    - If no templates are provided, uses a default template.
    - Produces a <prompt> XML structure:
        <prompt>
          <templates>
            <template name="..."> ... </template>
            ...
          </templates>
          <files>
            <file path="..."> ... </file>
            ...
          </files>
        </prompt>
    - On success (if not silent), prints a token count to stderr.
    - On error, prints an error message to stderr (unless silent) and exits with non-zero code.

Assumptions:
    - Prompt template files and inline prompts are plain text.
    - Files (-f, and those listed by -l) are arbitrary text files.
    - Nonexistent/unreadable files cause an error and exit.
    - Token count is the number of whitespace-separated tokens in the final XML.

Compilation:
    - Can be compiled to a native binary (e.g. via PyInstaller).

Clean Code & Testing:
    - Uses argparse for robust argument parsing.
    - Includes basic tests at the end.
    - Validates file existence and readability.
    - Straightforward logic minimizes errors.

Security & Reliability:
    - No external dependencies beyond Python standard library.
    - Ensures well-structured XML output.

"""

import sys
import os
import argparse
import xml.etree.ElementTree as ET

def read_file_content(filepath):
    """Read and return the content of a file as a string.
    Raises IOError if the file cannot be read."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Aggregate prompts and files into a single XML prompt.")
    parser.add_argument('-p', '--prompt', action='append', help='Path to a prompt template file', default=[])
    parser.add_argument('-f', '--file', action='append', help='Path to a single file', default=[])
    parser.add_argument('-l', '--list', help='Path to a file containing a list of file paths')
    parser.add_argument('-o', '--output', help='Path to output file')
    parser.add_argument('-s', '--silent', action='store_true', help='Suppress stderr output')
    parser.add_argument('additional_prompts', nargs='*', help='Additional inline prompt templates')

    args = parser.parse_args(argv)

    prompt_paths = args.prompt[:] if args.prompt else []
    file_paths = args.file[:] if args.file else []
    inline_prompts = args.additional_prompts[:] if args.additional_prompts else []

    # Handle -l list file
    if args.list:
        if not os.path.isfile(args.list):
            if not args.silent:
                print(f"Error: List file '{args.list}' does not exist or is not accessible.", file=sys.stderr)
            return 1
        try:
            list_content = read_file_content(args.list)
        except IOError:
            if not args.silent:
                print(f"Error: Could not read list file '{args.list}'.", file=sys.stderr)
            return 1
        for line in list_content.splitlines():
            line = line.strip()
            if line:
                file_paths.append(line)

    # Read prompt templates
    templates = []
    for ppath in prompt_paths:
        if not os.path.isfile(ppath):
            if not args.silent:
                print(f"Error: Prompt template file '{ppath}' does not exist or is not accessible.", file=sys.stderr)
            return 1
        try:
            t_content = read_file_content(ppath)
        except IOError:
            if not args.silent:
                print(f"Error: Could not read prompt template file '{ppath}'.", file=sys.stderr)
            return 1
        templates.append((ppath, t_content))

    # Add inline prompt templates
    for idx, inline_prompt in enumerate(inline_prompts):
        templates.append((f"inline_prompt_{idx+1}", inline_prompt))

    if not templates:
        templates = [("default", "Please analyze the provided files and summarize their purpose and functionality.")]

    # Read files
    files_data = []
    for fpath in file_paths:
        if not os.path.isfile(fpath):
            if not args.silent:
                print(f"Error: File '{fpath}' does not exist or is not accessible.", file=sys.stderr)
            return 1
        try:
            f_content = read_file_content(fpath)
        except IOError:
            if not args.silent:
                print(f"Error: Could not read file '{fpath}'.", file=sys.stderr)
            return 1
        files_data.append((fpath, f_content))

    # Construct XML structure without CDATA
    prompt_el = ET.Element('prompt')
    templates_el = ET.SubElement(prompt_el, 'templates')
    for t_name, t_content in templates:
        t_el = ET.SubElement(templates_el, 'template')
        t_el.set('name', os.path.basename(t_name))
        t_el.text = t_content

    files_el = ET.SubElement(prompt_el, 'files')
    for f_name, f_content in files_data:
        f_el = ET.SubElement(files_el, 'file')
        f_el.set('path', f_name)
        f_el.text = f_content

    final_str = ET.tostring(prompt_el, encoding='utf-8', method='xml').decode('utf-8')

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as out_f:
                out_f.write(final_str)
        except IOError:
            if not args.silent:
                print(f"Error: Could not write to output file '{args.output}'.", file=sys.stderr)
            return 1
    else:
        print(final_str)

    if not args.silent:
        token_count = len(final_str.split())
        print(f"Success: Prompt generated with {token_count} tokens.", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())


# Basic Tests (Unmodified)
import unittest
from unittest.mock import patch, mock_open
import io

class TestRp(unittest.TestCase):
    @patch('builtins.open', new_callable=mock_open, read_data='Sample template content')
    @patch('os.path.isfile', return_value=True)
    def test_single_prompt_template(self, mock_isfile, mock_file):
        argv = ['-p', 'template.txt']
        with patch('sys.stderr', new_callable=io.StringIO) as fake_stderr:
            with patch('sys.stdout', new_callable=io.StringIO) as fake_stdout:
                exit_code = main(argv)
                self.assertEqual(exit_code, 0)
                output = fake_stdout.getvalue()
                self.assertIn("<templates>", output)
                self.assertIn("<template name=\"template.txt\">Sample template content</template>", output)
                self.assertIn("<files />", output)
                self.assertIn('Success: Prompt generated with', fake_stderr.getvalue())

    @patch('builtins.open', new_callable=mock_open, read_data='file content')
    @patch('os.path.isfile', return_value=True)
    def test_single_file(self, mock_isfile, mock_file):
        argv = ['-f', 'somefile.py']
        with patch('sys.stderr', new_callable=io.StringIO) as fake_stderr:
            with patch('sys.stdout', new_callable=io.StringIO) as fake_stdout:
                exit_code = main(argv)
                self.assertEqual(exit_code, 0)
                output = fake_stdout.getvalue()
                self.assertIn("<template name=\"default\">Please analyze the provided files and summarize their purpose and functionality.</template>", output)
                self.assertIn("<file path=\"somefile.py\">file content</file>", output)
                self.assertIn('Success: Prompt generated with', fake_stderr.getvalue())

    @patch('os.path.isfile', return_value=False)
    def test_missing_file(self, mock_isfile):
        argv = ['-f', 'missingfile.txt']
        with patch('sys.stderr', new_callable=io.StringIO) as fake_stderr:
            with patch('sys.stdout', new_callable=io.StringIO):
                exit_code = main(argv)
                self.assertNotEqual(exit_code, 0)
                self.assertIn("Error: File 'missingfile.txt' does not exist or is not accessible.", fake_stderr.getvalue())

    @patch('builtins.open', new_callable=mock_open, read_data='line1\nline2')
    @patch('os.path.isfile', return_value=True)
    def test_list_file(self, mock_isfile, mock_file):
        argv = ['-l', 'list.txt']
        mock_file.side_effect = [
            io.StringIO("file1.py\nfile2.md"),
            io.StringIO("print('hello world')"),
            io.StringIO("# Some markdown content")
        ]
        with patch('sys.stderr', new_callable=io.StringIO) as fake_stderr:
            with patch('sys.stdout', new_callable=io.StringIO) as fake_stdout:
                exit_code = main(argv)
                self.assertEqual(exit_code, 0)
                output = fake_stdout.getvalue()
                self.assertIn("<file path=\"file1.py\">print('hello world')</file>", output)
                self.assertIn("<file path=\"file2.md\"># Some markdown content</file>", output)
                self.assertIn('Success: Prompt generated with', fake_stderr.getvalue())

    @patch('builtins.open', new_callable=mock_open, read_data='fake content')
    @patch('os.path.isfile', return_value=True)
    def test_silent_mode(self, mock_isfile, mock_file):
        argv = ['-f', 'code.py', '-s']
        with patch('sys.stderr', new_callable=io.StringIO) as fake_stderr:
            with patch('sys.stdout', new_callable=io.StringIO) as fake_stdout:
                exit_code = main(argv)
                self.assertEqual(exit_code, 0)
                self.assertEqual('', fake_stderr.getvalue())
                output = fake_stdout.getvalue()
                self.assertIn("<file path=\"code.py\">fake content</file>", output)

    @patch('builtins.open', new_callable=mock_open, read_data='irrelevant')
    @patch('os.path.isfile', return_value=True)
    def test_inline_prompt(self, mock_isfile, mock_file):
        argv = ['This', 'is', 'an', 'inline', 'prompt']
        with patch('sys.stderr', new_callable=io.StringIO) as fake_stderr:
            with patch('sys.stdout', new_callable=io.StringIO) as fake_stdout:
                exit_code = main(argv)
                self.assertEqual(exit_code, 0)
                output = fake_stdout.getvalue()
                self.assertIn("<template name=\"inline_prompt_1\">This</template>", output)
                self.assertIn("<template name=\"inline_prompt_2\">is</template>", output)
                self.assertIn("<template name=\"inline_prompt_3\">an</template>", output)
                self.assertIn("<template name=\"inline_prompt_4\">inline</template>", output)
                self.assertIn("<template name=\"inline_prompt_5\">prompt</template>", output)
                self.assertIn('Success: Prompt generated with', fake_stderr.getvalue())
    