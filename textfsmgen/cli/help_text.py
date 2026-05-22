# help_text.py

import textwrap


class HelpText:
    def __init__(self):
        self.snippet = "Inline snippet text."
        self.snippet_file = "Path to snippet file."
        self.sample_file = "Sample filename containing raw text sample."
        self.command = "Shell command to generate a real-world sample."
        self.show = (
            "Show output in human-readable form: snippet | template | result | tabular."
        )

        self.save = textwrap.dedent("""
            Save selected outputs to file(s).
            
            Format: <kind>-<filename>,...
            
            Kinds:  sample | snippet | template | result
        """).strip()

        self.config = "Optional JSON config file."
        self.debug = "Print resolved parameters and sample metadata."
        self.dry_run = "Simulate all write operations; no files are created."

        self.create_config = "Generate the config and save it to FILE."
        self.create_golden_test = "Create a golden test at the specified path."
        self.json = "Output machine-readable JSON instead of human text."


# ⭐ Single shared instance
HELP = HelpText()
