from textpress.cli.cli_main import __doc__ as cli_doc

HELP_PAGE = (
    (cli_doc or "")
    + """
Commands can be run on a URL, .docx file, or Markdown file and in most cases formats
will be detected automatically.

Textpress maintains a file cache and a workspace for intermediate files, by default
using `./textpress` as the workspace root. You can remove these at any time.

Typical usage: Save a Gemini Deep Research report to Google Docs and export as .docx.
Then you can use it:

```shell
# Save your API key
tp setup

# Convert to clean Markdown
tp convert ~/Downloads/'Airspeed Velocity of Unladen Birds.docx'
# See results
less textpress/workspace/docs/airspeed_velocity_of_unladen_birds_1.doc.md

# Convert and format as nicer HTML
tp format ~/Downloads/'Airspeed Velocity of Unladen Birds.docx' --show

# If desired: edit the Markdown then view again
tp format textpress/workspace/docs/airspeed_velocity_of_unladen_birds_1.doc.md --show

# Publish formatted Markdown to Textpress
tp publish textpress/workspace/docs/airspeed_velocity_of_unladen_birds_1.doc.md --show
```

For all commands: `tp --help`

For more information: https://textpress.md 

GitHub: https://github.com/jlevy/textpress
"""
)
