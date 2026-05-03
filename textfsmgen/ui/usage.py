"""
textfsmgen.ui.usage
===================

Provides the usage dialog and formatted help text UI for TextFSMGen.
"""

import re

from textfsmgen.libs.text import dedent_and_strip

import textfsmgen.config as config

from textfsmgen import ui
from textfsmgen.ui import widget

from textfsmgen.ui.common import (
    center_window,
    make_modal,
    render_formatted_text
)


window_width = 960 if ui.is_macos else 820 if ui.is_linux else 740
window_height = 770 if ui.is_macos else 780 if ui.is_linux else 720


def show_help(app, category):
    """Show Help Dialog based on category."""

    parent = app.root
    dialog = ui.Toplevel(parent)
    dialog.title(build_usage_title(category))

    widget.set_window_icon(dialog)

    if parent:
        center_window(
            parent, dialog, int(window_width * 0.9), int(window_height * 0.95),
            x_resizable=True, y_resizable=True
        )

    # Frame to hold textarea + scrollbar
    frame = ui.Frame(dialog)
    frame.pack(fill="both", expand=True)

    # Allow frame to expand
    frame.rowconfigure(0, weight=1)     # textarea grows vertically
    frame.rowconfigure(1, weight=0)  # fixed rows do NOT grow vertically
    frame.columnconfigure(0, weight=1)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(frame, wrap='none', state="disabled", bg=ui.readonly_text_bg_color)
    textarea.grid(row=0, column=0, sticky='nswe')  # noqa

    render_formatted_text(textarea, get_usage(category))

    # Add vertical scrollbar
    vscrollbar = ui.Scrollbar(
        frame, orient="vertical",
        command=textarea.yview
    )
    vscrollbar.grid(row=0, column=1, sticky='ns')

    # Add horizontal scrollbar
    hscrollbar = ui.Scrollbar(
        frame, orient="horizontal",
        command=textarea.xview
    )
    hscrollbar.grid(row=1, column=0, sticky='ew')

    # Link scrollbars to text area
    textarea.config(
        yscrollcommand=vscrollbar.set,
        xscrollcommand=hscrollbar.set
    )

    make_modal(dialog)


def build_usage_title(category: str) -> str:
    """Return a formatted usage title for the given category."""
    if category == "settings":
        return "Settings Guide - TextFSMGen CE"

    if category == "app":
        return "Getting Started with TextFSMGen CE"

    if category == "regex":
        return "Quickstart Regex Builder Tool - TextFSMGen CE"

    if category == "tester":
        return "Quickstart TextFSM Tester Tool - TextFSMGen CE"

    if category == "snippet_translator":
        return "Quickstart Snippet Translator Tool - TextFSMCGen CE"

    base = " ".join(category.split("_")).title()
    return f"{base} Usage - TextFSMGen CE"


def update_url_link(usage):
    for name, url in config.urls.items():
        replacing = rf"----\s*{name}\s*" + re.escape("</link>")
        replacement = f"---- {url}</link>"
        usage = re.sub(replacing, replacement, usage)
    return usage


def get_usage(category: str) -> str:
    """Return usage text for the given category."""
    usage = "Unknown Usage"
    if category == "snippet_translator":
        usage = get_snippet_translator_usage()

    elif category == "settings":
        usage = get_settings_guide()

    elif category == "app":
        usage = get_started_with_textfsmgen()

    elif category == "regex":
        usage = get_quickstart_regex_builder_tool()

    elif category == "tester":
        usage = get_quickstart_textfsm_tester_tool()

    usage = update_url_link(usage)

    return f"{usage}\n\n"


def get_snippet_translator_usage():
    """Return usage of snippet translator."""
    usage = dedent_and_strip("""
        The <bold>Snippet Translator Tool</bold> helps users quickly generate a <bold>TextFSMGen</bold> snippet 
        and optional Python verification code. It provides an iterative workflow for 
        translating raw text, refining the snippet, and validating the parsing logic.

        <bold>Interface Overview</bold>
        <bold>------------------</bold>

            <bold>1. User Input Area</bold>
               Where you paste or type raw text to be translated.
    
            <bold>2. Snippet Output Area</bold>
               Displays the generated TextFSMGen snippet. You can edit this snippet 
               and run translation again to refine the result.
    
            <bold>3. Read-Only Code Area</bold>  
               Shows Python verification code, snippet keyword explanations, 
               or error messages.
    
            <bold>4. Read-Only Result Area</bold>
               Displays the Python regex pattern or the output produced by 
               the verification code.

        <bold>Settings Overview</bold>
        <bold>-----------------</bold>

            <bold>1. Variable Checkbox</bold>
               Automatically generates variable names for snippet tokens when <bold>ON</bold>.
    
            <bold>2. Surrounding Notation Checkbox</bold>
               Treats common prefix or suffix punctuation as text instead of tokens 
               when <bold>ON</bold> and when Group is <bold>OFF</bold>.
    
            <bold>3. Group Checkbox</bold>
               Controls how tokens are grouped. When <bold>ON</bold>, each line in 
               the User Input Area becomes a single token. 
               When <bold>OFF</bold>, whitespace-separated tokens are used 
               (only the first non-empty line is supported).
    
            <bold>4. Generic Checkbox</bold>
               Controls whether group quantities are translated as generic matchers.
    
            <bold>5. Split Option</bold>
               Defines the separator used when splitting mixed tokens.
           
        <bold>Brief Step Walk Through Examples</bold>
        <bold>--------------------------------</bold>
        
        <bold>Example 1:</bold>
        <bold>----------</bold>
        
            <bold>Given data:</bold>
                result = -3.1/-4.5
            
            <bold>Expectation:</bold>
                Generate Python regex pattern that captures variable name, dividend, and divisor
            
            <bold>Expected Pattern:</bold>
                #############################################################
                # Equivalent snippet conversion:
                #  'word(var_v0) = mixed_number(var_v1)/mixed_number(var_v2)'
                #############################################################
                pattern = r"(?P<v0>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*) = (?P<v1>[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*)/(?P<v2>[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*)"
            
            <bold>Expected Result:</bold>
                {'name': 'result', 'dividend': '3.1', 'divisor': '4.5'}
        
            <bold>Steps:</bold>
            
                1. Enter or paste the given data to <bold>User Input Area</bold>.
                
                2. Use default settings.  
                   These are (Variable: <bold>ON</bold>), (Generic: <bold>ON</bold>), (Split: <bold>/</bold>)
                
                3. Click "<bold>Translate</bold>" to produce in Output Area: 
                   word(var_v0) = mixed_number(var_v1)/mixed_number(var_v2)
                
                4. Update variable names: 
                   - "<bold>v0</bold>" => "<bold>name</bold>"
                   - "<bold>v1</bold>" => "<bold>dividend</bold>"
                   - "<bold>v2</bold>" => "<bold>divisor</bold>"
                   - Then click "<bold>Iterate</bold>"
            
                <bold>5. Observe and verify:</bold>
                
                   <bold>5.1: Generated Pattern:</bold>
                   
                        #############################################################
                        # Equivalent snippet conversion:
                        #  'word(var_v0) = mixed_number(var_v1)/mixed_number(var_v2)'
                        #############################################################
                        pattern = r"(?P<v0>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*) = (?P<v1>[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*)/(?P<v2>[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*)"
                   
                   <bold>5.2: Result</bold>
                   
                        {'name': 'result', 'dividend': '3.1', 'divisor': '4.5'}
        
        <bold>References</bold>
        <bold>==========</bold>
        
            - <link>How to Use the Snippet Translator ---- how-to-use-snippet-translator</link>
            - <link>Demo: Snippet Translator ---- demo-snippet-translator</link>

    """)

    return usage


def get_settings_guide():
    guide = dedent_and_strip("""
        This guide provides a quick overview of the appropriate settings 
        for the <bold>TextFSM Generator</bold> application so that end‑users can obtain 
        the expected results.  Settings are organized into the following groups:
        
            - <bold>General Arguments Settings</bold> shared by <bold>Template Builder</bold>, 
              <bold>Category Template Builder</bold>, and <bold>Tabular Template Builder</bold>
            - <bold>Category Translator Arguments Settings</bold> for <bold>Category Template Builder</bold>.
            - <bold>Tabular Translator Arguments Settings</bold> for <bold>Tabular Template Builder</bold>.
            - Settings for <bold>Test Execution</bold>
            - Settings for <bold>Output Display</bold>
        
        <bold>General Arguments Settings</bold>
        <bold>==========================</bold>
        
            The "<bold>Author</bold>", "<bold>Email</bold>", "<bold>Company</bold>", and "<bold>Description</bold>" fields 
            populate the metadata header of the generated TextFSM template. 
            These values are shared by the <bold>Template Builder</bold>, 
            <bold>Category Template Builder</bold>, and <bold>Tabular Template Builder</bold>.

            Example:
                If the "<bold>Email</bold>" value is "<bold>john@abcxyz.com</bold>", the generated template 
                header will be:
                
                ################################################################################
                # Template is generated by TextFSMGen CE
                <bold># Email       : john@abcxyz.com</bold>
                # Created date: 2026-04-19
                ################################################################################
                Value v1 ([a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)
                
                Start
                  ^${v1}
        
        
        <bold>Category Translator Arguments</bold>
        <bold>=============================</bold>
        These settings apply to the <bold>Category Template Builder</bold>:
        
            - <bold>Use Category Translator</bold>:
              A one‑time action. When <bold>ON</bold>, the translator runs once and then resets to <bold>OFF</bold>.
              Default: <bold>OFF</bold>.
        
            - <bold>Separator</bold>:
              The separator used in (<left-identifier><separator><value>) pairs.
              Default: colon (:).
        
            - <bold>Count</bold>:
              Maximum number of (<left-identifier><separator><value>) pairs in Category Format.
              Default: 1.
        
            - <bold>Starting From</bold>:
              Adds a condition that instructs the TextFSM template to begin parsing from
              a specific line.
        
            - <bold>Ending At</bold>:
              Adds a condition that instructs the TextFSM template to stop parsing at
              a specific line.
        
            - <bold>Replacing</bold>:
              A post‑processing step applied after generating the tabular snippet and
              TextFSM template. This allows additional enhancements to improve parsing
              results. It is an automation mode that performs A‑to‑Z processing in one run.
        
        
        <bold>Tabular Translator Arguments</bold>
        <bold>============================</bold>
        These settings apply to the <bold>Tabular Template Builder</bold>:
        
            - <bold>Use Tabular Translator</bold>:
              A one‑time action. When <bold>ON</bold>, the translator runs once and then resets to <bold>OFF</bold>.
              Default: <bold>OFF</bold>.
        
            - <bold>Divider</bold>:
              Column separator. Can be single space, multiple spaces, comma, plus, pipe,
              or other characters. Default: empty.
        
            - <bold>Count</bold>:
              Total number of columns. Default: 0.
        
            - <bold>Widths</bold>:
              A list of column widths a list of integer. The last width my be
              omitted using a comma trailing.
              Acceptable formats:
                  7, 5,
                  7, 5, 3
        
            - <bold>Has Header Row</bold>:
              Enable this when the sample tabular data includes a header row. The generated
              template will create variables based on header names and will include a
              condition to prevent capturing the header in the parsed results.
              Example headerless data: "ls -la"
              Example headered data: "who -H"
        
            - <bold>Headers</bold>:
              Used to create template variables for headerless tabular data.
              If empty, auto‑generated column names are used.
              Acceptable formats:
                  NAME     LINE     TIME     COMMENT
                  NAME, LINE, TIME, COMMENT
                  ["NAME", "LINE", "TIME", "COMMENT"]
              The most accurate format is a list of strings.
        
            - Custom Header:
              Used when headerless data cannot be analyzed correctly using other parameters.
              Also useful when the user wants a specific expected structure.
              
              Example: "ls -la" output has 9 columns, but the user may want to merge
              month, date, and time/year into a single "date_time" column.
              
              Sample line:
                  drwxr-xr-x 1 tester 197609       0 Dec 19 15:49 ./
          
              Custom header example:
                  ---------- - ------ ------ ------- ------------ -----------------
        
            - <bold>Header Rows</bold>:
              Used for multi‑row headers. Rarely needed.
        
            - <bold>Starting From</bold>:
              Adds a condition that instructs the template to begin parsing from 
              a specific line.
        
            - <bold>Ending At</bold>:
              Adds a condition that instructs the template to stop parsing at 
              a specific line.
        
            - <bold>Replacing</bold>:
              Post‑processing step similar to Category Translator. Performs A‑to‑Z
              automation in one run.
        
        
        <bold>Test Execution Settings</bold>
        <bold>=======================</bold>
            - <bold>Interpreter</bold>:
              Select the Python interpreter. A Python virtual environment is recommended.
        
            - <bold_red>Always Ask</bold_red>:
              When <bold_green>ON</bold_green> (default), <bold_red>TextFSMGen prompts for confirmation</bold_red> 
              <bold_red>before running tests because execution requires saving a temporary script file</bold_red>.
              <bold>Recommended</bold>: <bold_green>ON</bold_green>.
        
            - <bold_red>Delete Temp File After Run</bold_red>:
              When <bold_green>ON</bold_green> (default), <bold_red>TextFSMGen automatically deletes the temporary file
              after execution</bold_red>.
              <bold>Recommended</bold>: <bold_green>ON</bold_green>.
        
        
        <bold>Output Display Options</bold>
        <bold>======================</bold>
        These options determine what is displayed in the Output Area when 
        the "Result" button is clicked. They provide a convenient way to 
        review the test data, the generated template, and the parsed results 
        in a single view.
        
            - <bold>Test Data</bold>:
              When checked, test data is displayed.
        
            - <bold>Template</bold>:
              When checked, the generated TextFSM template is displayed.
        
            - <bold>Tabular</bold>:
              When checked, parsed results are shown in table text format.
              When unchecked, results are shown using Python pprint.
        
            - <bold>Index</bold>:
              When checked, an index column is added to help visually inspect 
              or verify parsed results.
              
        <bold>References</bold>
        <bold>==========</bold>
        
            - <link>TextFSM Generator Settings Reference ---- textfsm-generator-settings-guide</link>

    """)
    return guide


def get_started_with_textfsmgen():
    usage = dedent_and_strip("""        
        The TextFSM Generator helps users quickly generate TextFSM templates, 
        verify parsed results, generate unittest scripts, pytest scripts, 
        or standalone Python test code, and perform test execution on the fly.
        
        <bold>Interface Overview</bold>
        ==================
        
        <bold>1. User Input Area</bold>
           <bold>----------------</bold>
           The User Input Area has two modes: User Input Mode and Test Data Mode.
        
           - User Input Mode allows the user to enter or edit a snippet.
           - Test Data Mode allows the user to provide sample data for verification.
        
           When TextFSMGen launches, User Input Mode is active by default.
        
           To switch modes:
           - Click the "Test Data" button to enter Test Data Mode. The button label
             changes to "Hide".
           - Click "Hide" to return to User Input Mode.
        
        <bold>2. Read-Only Output Area</bold>
           <bold>----------------------</bold>
           The Read-Only Output Area displays results generated by the application.
           It supports the following actions:
        
           - Build the TextFSM template
           - Display parsed results
           - Display generated unittest, pytest, or Python test code
           - Display test execution output


        <bold>Controls Buttons Overview</bold>
        <bold>=========================</bold>
        
        <bold>1. Test Data</bold>
           Allows switching between User Input Mode and Test Data Mode.
           When switching to Test Data Mode, three changes occur:
             - A visual effect is applied (not supported on macOS)
             - The application title is updated with "(Test Data Mode)"
             - The button label changes to "Hide"
           Clicking "Hide" returns the interface to User Input Mode.
        
        <bold>2. Open</bold>
           Loads data from a file into both the User Input Area and the Test Data Area.
        
        <bold>3. Save</bold>
           Saves User Input data, the generated TextFSM template, or test scripts.
           This button is disabled at application launch. It becomes enabled after the
           user loads data using the "Open" button or generates output using "Build."
        
        <bold>4. Copy</bold>
           Copies the current content to the clipboard.
           This button is disabled at application launch. It becomes enabled after the
           user loads data using "Open" or generates output using "Build."
        
        <bold>5. Paste</bold>
           Pastes clipboard content into either the User Input Area or the Test Data Area.
        
        <bold>6. Clear</bold>
           Clears selected text, or clears all User Input data, Test Data, and Output
           depending on the current context.
        
        <bold>7. Build</bold>
            Builds a TextFSM template using the TextFSMGen snippet from the User Input Area.
            If Test Data Mode is currently active, TextFSMGen automatically switches back
            to User Input Mode before starting the build process.
        
        <bold>8. Result</bold>
           Parses the generated TextFSM template using the provided test data.
           This button is disabled at application launch. It becomes enabled after the
           user successfully builds a TextFSM template.
        
        <bold>9. Python</bold>
           Generates a standalone Python test script using the current test data.
           This button is disabled at application launch or after clearing all data.
           It becomes enabled once a TextFSM template has been successfully built with
           valid test data.
        
        <bold>10. Unittest</bold>
            Generates a Python unittest script using the current test data.
            This button is disabled at application launch or after clearing all data.
            It becomes enabled once a TextFSM template has been successfully built with
            valid test data.
        
        <bold>11. Pytest</bold>
            Generates a pytest script using the current test data.
            This button is disabled at application launch or after clearing all data.
            It becomes enabled once a TextFSM template has been successfully built with
            valid test data.
        
        <bold>12. Execute</bold>
            Executes a standalone Python script, unittest, or pytest test.
            This requires a configured Python interpreter with the following packages:
              - TextFSMGen
              - Pytest
              - PyYAML
              - TextFSM
            The interpreter can be configured in the Settings panel.

        
        <bold>High Level Workflow Overview</bold>
        <bold>============================</bold>
        
        TextFSM Generator supports two primary workflows for generating TextFSM
        templates. Each workflow serves a different type of input and user experience.
        
        
        <bold>-------------------------------------------------------------------------------</bold>
        <bold>Free-Form Workflow Overview</bold>
        <bold>-------------------------------------------------------------------------------</bold>
        
        +-----------+   manually  +---------+  refine until   +-----------+
        | Free-Form |  -------->  | Snippet |  <----------->  |  TextFSM  |
        |  Input    |     edit    +---------+      match      | Generator |
        +-----------+                                         +-----------+
                                                                    |
                                                           generate |
                                                                    v
                                                         +------------------+
                                                         | TextFSM Template |
                                                         +------------------+
        
        <bold>Format of Free-Form Input:</bold>
        <bold>--------------------------</bold>
        
        <token-1>(<separator> ... <separator> <token-n>)?
        <new-line-separator>?
        ...
        
        Where:
        - <token>      : any sequence of non-whitespace characters
        - <separator>  : one or more whitespace characters
        
        Free-form input is unstructured data. Users must manually create 
        a TextFSMGen snippet to translate the data into a TextFSM template. 
        This requires manual effort, but the Snippet Translator tool can 
        automatically generate a correct snippet without requiring knowledge 
        of regular expressions.
        
        
        <bold>-------------------------------------------------------------------------------</bold>
        <bold>Semi-Structured Workflow Overview</bold>
        <bold>-------------------------------------------------------------------------------</bold>
        
        +-----------------+        +----------------------+    
        | Semi-Structured |        | TextFSM Generator    |  refine until  +---------+
        |     Input       | -----> +----------------------+ <------------> | Snippet |
        +-----------------+        | Translate => Snippet |     match      +---------+
                                   +----------------------+ 
                                              |
                                              | generate
                                              v
                                     +------------------+
                                     | TextFSM Template |
                                     +------------------+
        
        TextFSMGen supports two types of semi-structured data:
        1. Category-Format Data (key-value or section-based)
        2. Tabular Data (column-aligned or row-based)
        
        
        <bold>-------------------------------------------------------------------------------</bold>
        <bold>Format of Semi-Category Data</bold>
        <bold>-------------------------------------------------------------------------------</bold>
        
        <non-category-data-line>
        <left-identifier-1><separator><value-1><spacer>( ... <left-identifier-k><separator><value-k>)?
        ...
        <non-category-data-line>
        
        Where:
        - <non-category-data-line> : any line that does not match category format
        - <left-identifier>        : a token or group of tokens separated by whitespace
        - <separator>              : usually a punctuation character (commonly ":")
        - <value>                  : any characters
        - <spacer>                 : usually multiple whitespace characters
        
        Good examples of category-format data:
        - Windows "ipconfig"
        - Windows "nslookup"
        
        
        <bold>-------------------------------------------------------------------------------</bold>
        <bold>Format of Semi-Tabular Data</bold>
        <bold>-------------------------------------------------------------------------------</bold>
        
        <non-tabular-data-line>
        <header-line>
        <header-separator-line>
        <row>
        <non-tabular-data-line>
        
        <bold>Definitions:</bold>
        - <header-line>           : <header-1><separator> ... <separator><header-k>
        - <header-separator-line> : repeated punctuation separated by <separator>
        - <row>                   : <cell-1><separator> ... <separator><cell-k>
        
        Where:
        - <non-tabular-data-line> : may or may not resemble tabular data; users must
                                    verify correctness before approving the template
        - <header-line>           : may be present or absent; may contain multiple rows
        - <separator>             : single space, multiple spaces, or punctuation
        - <row>                   : cells separated by the separator; cells may be empty
        
        Good examples of tabular data:
        - Linux "ls -la"
        - PowerShell "ls" (row-based table)
        
        <bold>References</bold>
        <bold>==========</bold>
          
          - <link>Demo: Building TextFSM Template for IOS - show clock (Free-Form) ---- demo-ios-show-clock</link>
          - <link>Demo: Building TextFSM Template for Linux - stat file-name (Category-Form) ---- demo-linux-file-status-information</link>
          - <link>Demo: Building TextFSM Template for Linux - ls -la (Tabular Headerless Rows-Based Form) ---- demo-listing-files-in-long-format-on-linux</link>
          - <link>Demo: Building TextFSM template for Alias Powershell - ls (Tabular with Header Rows-Based Form) ---- demo-listing-files-on-powershell</link>
    """)

    return usage


def get_quickstart_regex_builder_tool():
    doc = dedent_and_strip("""
The Regex Builder Tool helps users quickly generate a regular expression pattern
along with a detailed explanation. This tool provides two ways to generate a pattern:
  - Select predefined keywords using checkboxes
  - Use user-provided data inputs

<bold>Interface Overview</bold>
<bold>------------------</bold>

<bold>1. Semantic Group</bold>
   Allows users to select predefined keywords and apply quantities to create
   more precise extraction patterns.

<bold>2. Data Group</bold>
   Contains eight input textboxes that allow users to generate patterns based
   on their own data samples.

<bold>3. Control Buttons and Settings</bold>
   <bold>3.1. Build</bold>
        Collects all parameters from keyword selections or user data and
        generates possible outcome snippets so users can review different
        scenarios.

   <bold>3.2. Aggregate</bold>
        Combines selected keywords or user data into a single aggregate keyword.
        Examples:
          + letters + digits -> word
          + letters + digits + punctuation -> mixed word
          + numbers + punctuation -> multiple non-whitespace

   <bold>3.3. Variable</bold>
        Allows users to assign a variable name for capturing matches.

   <bold>3.4. Allowed Empty</bold>
        Enables generation of patterns that match an empty string.

   <bold>3.5. Copy</bold>
        Copies the Pattern area or Explanation area to the clipboard.

   <bold>3.6. Paste</bold>
        Allows users to paste clipboard text into data textboxes, quantity
        textboxes, or the variable textbox.

   <bold>3.7. Reset</bold>
        Restores all settings to default values and clears all textboxes.
        Also clears the Pattern area, Explanation area, and Possible Outcomes group.

   <bold>3.8. Help</bold>
        Displays the QuickStart guide.

<bold>4. Possible Outcomes Group</bold>
   Appears only after selecting checkboxes or clicking Build.

<bold>5. Read-Only Pattern Area</bold>
   Displays the generated Python pattern statement.

<bold>6. Read-Only Explanation Area</bold>
   Displays the explanation for the generated pattern.


<bold>Semantic Overview</bold>
<bold>-----------------</bold>

<bold>1. anything</bold>
   Matches zero or more characters when the DOTALL regex flag is enabled.
   Without DOTALL, it does not match newline or carriage-return characters
   in ASCII or Unicode text.

<bold>2. something</bold>
   Matches one or more characters when the DOTALL regex flag is enabled.
   Without DOTALL, it does not match newline or carriage-return characters
   in ASCII or Unicode text.

<bold>3. space</bold>
   Matches a single blank space character.

<bold>4. spaces</bold>
   Matches one or more blank space characters.

<bold>5. whitespace</bold>
   Matches a single whitespace character. This includes:
       '\\t', '\\n', '\\x0b', '\\x0c', '\\r', '\\x1c', '\\x1d', '\\x1e', '\\x1f',
       ' ', '\\x85', '\\xa0', '\\u1680', '\\u2000', '\\u2001', '\\u2002',
       '\\u2003', '\\u2004', '\\u2005', '\\u2006', '\\u2007', '\\u2008',
       '\\u2009', '\\u200a', '\\u2028', '\\u2029', '\\u202f', '\\u205f', '\\u3000'

   Note: Python's definition of whitespace may differ from other languages,
   compilers, or interpreters.

<bold>6. whitespaces</bold>
   Matches one or more whitespace characters.

<bold>7. dot</bold>
   Matches any character when the DOTALL regex flag is enabled.
   Without DOTALL, it does not match newline or carriage-return characters
   in ASCII or Unicode text.

<bold>8. dots</bold>
   Matches one or more characters when the DOTALL regex flag is enabled.
   Without DOTALL, it does not match newline or carriage-return characters
   in ASCII or Unicode text.

<bold>9. alnum</bold>
   Matches one alphanumeric character (letter or digit).

<bold>10. alnums</bold>
    Matches one or more alphanumeric characters.

<bold>11. graph</bold>
    Matches one printable ASCII character (0x21 to 0x7E).

<bold>12. graphs</bold>
    Matches one or more printable ASCII characters.

<bold>13. non-whitespace</bold>
    Matches one non-whitespace character.

<bold>14. non-whitespaces</bold>
    Matches one or more non-whitespace characters.

<bold>15. digit</bold>
    Matches one digit.

<bold>16. digits</bold>
    Matches one or more digits.

<bold>17. number</bold>
    Matches any of the following forms:
        <digits>
        <digits>.<digits>
        .<digits>
        <digits>.
    Represents integer or floating‑point formats.

<bold>18. numbers</bold>
    Matches a sequence of <number> values separated by <whitespaces>.
    Valid forms include:
        <number>
        <number><whitespaces><number>

<bold>19. mixed_number</bold>
    Matches <prefix><number><suffix> where:
        prefix may be "+", "-", "$", "(", or similar symbols
        suffix may be "%", ")", "]", or a unit string

<bold>20. mixed_numbers</bold>
    Matches a sequence of <mixed_number> values separated by <whitespaces>.
    Valid forms include:
        <mixed_number>
        <mixed_number><whitespaces><mixed_number>

<bold>21. punctuation</bold>
    Matches one punctuation character.

<bold>22. punctuations</bold>
    Matches one or more punctuation characters.

<bold>23. letter</bold>
    Matches one letter from a–z or A–Z.

<bold>24. letters</bold>
    Matches one or more letters.

<bold>25. word</bold>
    Matches an alphanumeric string (letters, digits, underscore) that contains
    at least one letter.

<bold>26. words</bold>
    Matches a sequence of <word> values separated by <whitespaces>.
    Valid forms include:
        <word>
        <word><whitespaces><word>

<bold>27. mixed_word</bold>
    Matches a combination of alphanumeric characters and punctuation,
    containing at least one letter or digit.

<bold>28. mixed_words</bold>
    Matches a sequence of <mixed_word> values separated by <whitespaces>.
    Valid forms include:
        <mixed_word>
        <mixed_word><whitespaces><mixed_word>


<bold>Quantity Overview</bold>
<bold>=================</bold>

<bold>1. optional</bold>
   In most cases, matches zero or one semantic unit. However, when combined
   with a group, the current logic of the TextFSM Generator treats it as
   matching zero or one *group*, not zero or one semantic. For example,
   optional_word_group matches one or more words separated by whitespaces.

<bold>2. optional_group</bold>
   Matches one or more semantics separated by whitespaces.

<bold>3. group</bold>
   Matches two or more semantics separated by whitespaces.

<bold>4. some</bold>
   Matches one or more semantics when the semantic type is:
       space(s), whitespace(s), dot(s), alpha(s), graph(s),
       non_whitespace(s), digit(s), letter(s), punctuation(s)
   Matches one or more semantics separated by whitespaces when the type is:
       number, mixed_number, word, mixed_word

<bold>5. zero_or_one</bold>
   Matches zero or one semantic.

<bold>6. zero_or_more</bold>
   Matches zero or more semantics when the semantic type is:
       space(s), whitespace(s), dot(s), alpha(s), graph(s),
       non_whitespace(s), digit(s), letter(s), punctuation(s)
   Matches zero or more semantics separated by whitespaces when the type is:
       number, mixed_number, word, mixed_word

<bold>7. one_or_more</bold>
   Matches one or more semantics when the semantic type is:
       space(s), whitespace(s), dot(s), alpha(s), graph(s),
       non_whitespace(s), digit(s), letter(s), punctuation(s)
   Matches one or more semantics separated by whitespaces when the type is:
       number, mixed_number, word, mixed_word

<bold>8. exact quantity</bold>
   Matches an exact number of semantics when the semantic type is:
       space(s), whitespace(s), dot(s), alpha(s), graph(s),
       non_whitespace(s), digit(s), letter(s), punctuation(s)
   Matches an exact number of semantics separated by whitespaces when the type is:
       number, mixed_number, word, mixed_word

<bold>9. quantity range</bold>
   Matches a quantity range (low to high) of semantics when the semantic type is:
       space(s), whitespace(s), dot(s), alpha(s), graph(s),
       non_whitespace(s), digit(s), letter(s), punctuation(s)
   Matches a quantity range (low to high) of semantics separated by whitespaces
   when the type is:
       number, mixed_number, word, mixed_word
       

<bold>Other Configuration</bold>
<bold>===================</bold>

<bold>1. Variable</bold>
   Allows the user to assign a capture name for the generated pattern.

<bold>2. Allowed Empty</bold>
   Allows the user to specify that the pattern should match an empty string.
   
       
<bold>Brief Step Walk-Through Examples</bold>
<bold>--------------------------------</bold>

<bold>Example 1: Using Predefined Semantics</bold>
<bold>-------------------------------------</bold>

Click the "word" semantic.

The snippet "word()" will appear in the Possible Outcomes group.

The Pattern area will display:

        pattern = r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*"

The Explanation area will display:

        +------------------------------------------+
        |                  word()                  |
        +------------------------------------------+
        Pattern:   r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*"
        Operation: Matches one word containing alphanumeric or underscore
                   characters with at least one alphabetic character.
        Explanation:
            lst = ['event_loop', 'grid8', 'grain']

        Evaluating:
            [bool(re.fullmatch(pattern, item)) for item in lst]

        Produces:
            [True, True, True]

<bold>Note:</bold> The sample data used in this explanation is generated by the
      TextFSM Generator Samples module.


<bold>Example 2: Using User Data</bold>
<bold>--------------------------</bold>

Enter "Hello Python!" into one of the textboxes in the Data Group.

Click "Build".

The snippet "mixed_word_group()" will appear in the Possible Outcomes group.

The Pattern area will display:

        pattern = r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+"

The Explanation area will display:

        +------------------------------------------+
        |            mixed_word_group()            |
        +------------------------------------------+
        Pattern:   r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+"

        Explanation:
            lst = ['Hello Python!']

        Evaluating:
            [bool(re.fullmatch(pattern, item)) for item in lst]

        Produces:
            [True]

<bold>Note:</bold> The sample data in this explanation comes from user input.
      This snippet is always displayed first in the Possible Outcomes group.


<bold>References</bold>
<bold>==========</bold>

    - <link>How to Use the Regex Builder ---- how-to-use-regex-builder</link>

    """)
    return doc


def get_quickstart_textfsm_tester_tool():
    doc = dedent_and_strip("""
        <bold>------------------------------------------------------------</bold>
        <bold>TextFSM Tester Tool - QuickStart Guide</bold>
        <bold>------------------------------------------------------------</bold>
        
        The TextFSM Tester Tool allows users to quickly verify a TextFSM template 
        using sample test data. If a parsing error occurs, the tool displays 
        the error so the user can review and correct the template.
        
        <bold>Interface Overview</bold>
        <bold>------------------</bold>
        
        <bold>1. Template Area</bold>
           Load a TextFSM template from a file or sync it from the TextFSMGen editor.
        
        <bold>2. Test Data Area</bold>
           Load test data from a file or sync it from the TextFSMGen editor.
        
        <bold>3. Control Buttons and Settings</bold>
        
           <bold>3.1. Test</bold>
                Runs TextFSM parsing and displays the result in the Result Area.
                The output format depends on the selected mode: regular, tabular,
                tabular with index, JSON, or YAML.
        
           <bold>3.2. Output Mode Checkbox</bold>
                <bold>Mode 1:</bold> unchecked, label=Tabular
                        Displays result using pprint.pformat.
                <bold>Mode 2:</bold> checked, label=Tabular
                        Displays result in tabular text format.
                <bold>Mode 3:</bold> checked, label=Tabular with Index
                        Displays tabular text with an index column.
                <bold>Mode 4:</bold> checked, label=JSON
                        Displays result in JSON format.
                <bold>Mode 5:</bold> checked, label=YAML
                        Displays result in YAML format.
        
           <bold>3.3. Sync</bold>
                Syncs template and test data from the TextFSMGen editor.
        
           <bold>3.4. Open</bold>
                Loads a file into the Template Area if it contains a TextFSM template.
                Otherwise, loads the file into the Test Data Area.
        
           <bold>3.5. Save</bold>
                Saves the content of the selected area:
                - Template Area: saves the template
                - Test Data Area: saves the test data
                - Result Area: saves the parsed result
                Any other selection triggers a warning.
        
           <bold>3.6. Copy</bold>
                Copies the content of the selected area to the clipboard.
                Any other selection triggers a warning.
        
           <bold>3.7. Paste</bold>
                Pastes clipboard text into the selected editable area
                (Template or Test Data). Any other selection triggers a warning.
        
           <bold>3.8. Reset</bold>
                Clears the Template, Test Data, and Result areas and resets the
                output mode.
        
           <bold>3.9. Close</bold>
                Closes the TextFSM Tester dialog and preserves Template and Test Data
                for the next launch.
        
           <bold>3.10. Help</bold>
                 Displays this QuickStart guide.
        
        <bold>4. Readonly Result Area</bold>
           Displays parsed output or any parsing errors.
        
        <bold>Brief Walk-Through Example</bold>
        <bold>--------------------------</bold>
        
        Load this TextFSM template into the Template Area:
        
                ################################################################################
                # Template generated by TextFSMGen CE
                # Created date: 2026-04-27
                ################################################################################
                Value first ([a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)
                Value last  ([a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)
        
                Start
                  ^first: ${first}
                  ^last:  ${last}
        
        Load test data:
        
                first: Tom
                last: Johnson
        
        Parsed result when Output Mode is unchecked:
        
                [{'first': 'Tom', 'last': 'Johnson'}]
        
        Parsed result when Output Mode is Tabular:
        
                +-------+---------+
                | first |  last   |
                +-------+---------+
                |  Tom  | Johnson |
                +-------+---------+
        
        Parsed result when Output Mode is Tabular with Index:
        
                +-------+-------+---------+
                | index | first |  last   |
                +-------+-------+---------+
                |   1   |  Tom  | Johnson |
                +-------+-------+---------+
        
        Parsed result when Output Mode is JSON:
        
                [
                  {
                    "first": "Tom",
                    "last": "Johnson"
                  }
                ]
        
        Parsed result when Output Mode is YAML:
        
                - first: Tom
                  last: Johnson
        
        <bold>References</bold>
        <bold>==========</bold>
        
            - <link>How to Use the Template Tester ---- how-to-use-textfsm-tester</link>

    """)
    return doc