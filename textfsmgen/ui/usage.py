"""
textfsmgen.ui.usage
===================

Provides the usage dialog and formatted help text UI for TextFSMGen.
"""


from textfsmgen.libs.text import dedent_and_strip

from textfsmgen import ui

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

    ui.set_window_icon(dialog)

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

    textarea = ui.TextArea(frame, wrap='none', state="disabled")
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
        return "Main App Settings Guide - TextFSMGen CE"

    base = " ".join(category.split("_")).title()
    return f"{base} Usage - TextFSMGen CE"


def get_usage(category: str) -> str:
    """Return usage text for the given category."""
    if category == "snippet_translator":
        return get_snippet_translator_usage()

    if category == "settings":
        return get_settings_guide()

    return "Unknown Usage"


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
        
            - <link>Using Snippet Translator ---- https://github.com/Geeks-Trident-LLC/textfsmgen/wiki/How-To-Use-Snippet-Translator</link>
            - <link>Demo Snippet Translator ---- https://github.com/Geeks-Trident-LLC/textfsmgen/wiki/Demo-Snippet-Translator</link>

    """)

    return f"{usage}\n\n"


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
                  drwxr-xr-x 1 tester 197609 0 Dec 19 15:49 ./
          
              Custom header example:
                  ---------- - ------ ------ ------- -------------- -----------------
        
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
        
            - <link>TextFSM Generator Settings Guide ---- https://github.com/Geeks-Trident-LLC/textfsmgen/wiki/TextFSM-Generator-Settings-Guide</link>

    """)
    return f"{guide}\n\n"