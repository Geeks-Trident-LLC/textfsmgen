# help_text.py

import textwrap


class HelpText:
    def __init__(self):
        self.snippet = "Inline snippet text."
        self.snippet_file = "Path to snippet file."
        self.sample_file = "Sample filename containing raw text sample."
        self.command = "Shell command to generate a real-world sample."
        self.show = (
            "Show output in human-readable form: snippet, template, result, or tabular."
        )

        self.save = textwrap.dedent("""
            Save output to file(s) or run in dry‑run mode.

            Formats: <kind>-<filename>,...
            dryrun(<kind>-<filename>,...)

            Kinds: sample, snippet, template, result
        """).strip()

        self.config = "Optional JSON config file."
        self.debug = "Print resolved parameters and sample metadata."

        self.create_config = "Preview the generated config (dry run)."
        self.create_config_file = "Generate the config and save it to FILE."

        self.create_golden_test = "Dry-run golden test creation."
        self.create_golden_test_path = "Create a golden test at the specified path."

        self.json = "Output machine-readable JSON instead of human text."


# ⭐ Single shared instance
HELP = HelpText()
