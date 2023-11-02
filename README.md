# apdfhelper: Annotated PDF Helper

This tool is originally meant to customize a PDF planner, and enhance its usage.
It can:

- remove pages

  If you don't use certain pages (anymore), you can remove them.

- rewrite (broken) internal links

  Rewire named links in a document to specific pages.

- extract annotations

  Extract text annotations in text format.

- fix link types

  Ensure that internal links show the correct page, fitted in a PDF viewer.
  
Currently only a command-line version of this tool is supplied.

## Installation

Python 3 is required.

```bash
pip install -r requirements.txt
```

## Usage

### Remove one or more pages

```bash
remove [OPTIONS] INFILE OUTFILE START STOP

Remove one or more pages from a PDF file and save to outfile.

Arguments:
INFILE [required]
OUTFILE [required]
START [required]
STOP [required]
```

Example:

```
python apdfhelper.py  calendar.pdf modified.pdf 3 13
```

### Extract all named links from a PDF file

Instead of directly linking to page numbers, PDF links can be named. `links`
extracts all named links that are defined in a PDF file, with the page number
it's pointing to. This can be useful as input when rewriting links. If the link
says `broken`, it's pointing to a non-existing page. Note that this can be fixed
using `rewrite`.

Example:

```
python apdfhelper.py links calendar.pdf
```

### Extract annotations from a PDF file

Extract all text annotations from a PDF file, and optionally show the page
number of the annotation.

Example:

```
python apdfhelper.py notes --location calendar.pdf
```

This will return a list of all text annotations in a document, grouped per page.

### Rewrite links in a PDF file

Sometimes named links are broken: They point to non-existing pages. Or, you'd
like to rewire the location of a named link. Use as input a text file,
containing the named link, followed by a space and a page number.

Example:

```
mossery-dpln-2023_third-edition.indd:2023-02-Index:241 2
mossery-dpln-2023_third-edition.indd:2023-03-YO-H1:3 29
```

This rewrites the link named
`mossery-dpln-2023_third-edition.indd:2023-02-Index:241` to page 2, and the link
named `mossery-dpln-2023_third-edition.indd:2023-03-YO-H1:3` to page 29.

#### Usage

```
apdfhelper.py rewrite [OPTIONS] INFILE OUTFILE LINKS

  Rewrite links in a PDF file based on a configuration file.

  If fit is given, rewrite type of link to 'Fit to page'.

Arguments:
  INFILE   [required]
  OUTFILE  [required]
  LINKS    [required]

Options:
  --fit / --no-fit  [default: no-fit]
```

#### Example

```
python apdfhelper.py rewrite calendar.pdf output.pdf filecontaininglinks.txt --fit
```

### Detailed link information

If you'd like to see which page contains links (clickable areas), and what the
link points to, use `page-links`. The result is the page number on which the
link occurs, with the coordinates of the link (left, top, right, bottom), the
_type_ of link (internal or external), and what the link points to.

Optionally you can see which page number a link points to, which can be useful
for troubleshooting broken links on pages.

#### Usage

```bash
apdfhelper.py page-links [OPTIONS] INFILE

Display links on a specific page, or all pages.

Output format is: pagenumber left top right bottom [INTERNAL | EXTERNAL] link.

When resolve is given, specify the page number of the link instead of the
named link.

Arguments:
INFILE [required]

Options:
--page INTEGER [default: 0]
--resolve / --no-resolve [default: no-resolve]
```
