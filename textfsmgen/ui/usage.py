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
    base = " ".join(category.split("_")).title()
    return f"{base} Usage - TextFSMGen CE"


def get_usage(category: str) -> str:
    """Return usage text for the given category."""
    if category == "snippet_translator":
        return get_snippet_translator_usage()

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
