# rp (Repo Prompt)

`rp` is a command-line tool that combines prompt templates and file contents into a structured XML prompt. This makes it easy to integrate with parsing tools like [o1-xml-parser](https://github.com/mckaywrigley/o1-xml-parser) and streamline repository analysis workflows.

## Features

- **Flexible Input:** Include prompt templates from files or inline arguments, and gather file contents directly or via a list file.
- **Structured XML Output:** Produces a `<prompt>` element with `<templates>` and `<files>` sections for easy parsing.
- **No CDATA Required:** Templates and file contents are included as normal XML text, simplifying downstream processing.
- **Silent Mode:** Suppress stderr output when needed, useful in automated pipelines.
- **Token Counting:** On success, reports a token count for the generated XML, aiding in analysis or size estimation.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
