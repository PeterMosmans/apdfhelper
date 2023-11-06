#!/usr/bin/env python3

"""apdfhelper - perform various functions on PDF files

Copyright (C) 2023 Peter Mosmans [Go Forward]
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import logging
import sys

import typer
from pikepdf import Dictionary, OutlineItem, Page, Pdf, String

app = typer.Typer()


def open_pdf(infile: str) -> Pdf:
    """Open a PDF file."""
    try:
        pdf = Pdf.open(infile)
        return pdf
    except Exception as e:
        print(f"Could not open {infile}: {e}")
        sys.exit(-1)


def read_toc(filename: str) -> (dict, dict):
    """Return dictionaries from a file, containing page numbers and their bookmarks / titles.
    The first dictionary uses page number as the key.
    The second dictionary uses the title as key."""
    pages, titles = {}, {}
    if not filename:
        return pages, titles
    try:
        with open(filename, "r") as filehandle:
            for line in filehandle.read().splitlines():
                try:
                    index = int(line.split(" ")[0])
                    # Only store first entries
                    if index not in pages:
                        pages[index] = line[len(str(index)) + 1 :]
                    if line[len(str(index)) + 1 :] not in titles:
                        titles[line[len(str(index)) + 1 :]] = int(index)
                except (ValueError, IndexError) as e:
                    print(f"Could not read a valid page number for {line[0]}: {e}")
    except (IOError, UnicodeDecodeError) as e:
        logging.error(f"Could not read {filename}: {e}")
    logging.info(
        f"Read {len(pages)} different pages and {len(titles)} different titles"
    )
    return pages, titles


def read_links(filename: str, toc: str = None) -> dict:
    """Return a dictionary from a file containing named links, with named links and their page numbers.
    Format of the file is NAME PAGENUMBER.
    Note that NAME can contain spaces: The last value at the right is chosen.
    When toc is supplied, read bookmark titles from taht file.
    If the value at the right contains double quotes, a bookmark title is expected."""
    result = {}
    if not filename:
        return result
    try:
        pages, titles = read_toc(toc)
        with open(filename, "r") as filehandle:
            for line in filehandle.read().splitlines():
                try:
                    # Check whether it's a bookmark title or a page number:
                    if line[len(line) - 1] == '"':
                        link_title = line.split('"')[0].strip()
                        bookmark_title = line.split('"')[1]
                        if bookmark_title in titles:
                            # Convert bookmark title to page number
                            index = int(titles[bookmark_title])
                        else:
                            print(
                                f"Could not find an entry for {bookmark_title} in {toc}"
                            )
                            sys.exit(-1)
                    else:
                        split = line.split(" ")
                        link_title = " ".join(split[0 : len(split) - 1])
                        index = int(split[len(split) - 1])
                    result[link_title] = index
                except ValueError as e:
                    print(f"Could not read a valid page number for {line}: {e}")
                    sys.exit(-1)
    except IOError:
        logging.error("Could not read %s", filename)
    logging.info(f"Read {len(result)} named links from {filename}")
    return result


def save_pdf(pdf, filename="output.pdf"):
    """Save PDF to output file."""
    print(f"Saving PDF to {filename}")
    try:
        pdf.save(filename)
    except Exception as e:
        print(f"Could not save to {filename}: {e}")


def convert_bookmark_item(
    bookmark: OutlineItem, results: list, dictionary: dict, level: int = 0
) -> (list, dict):
    """Convert a bookmark (OutlineItem) into a title and page number.
    Return a textual representation of the bookmarks and a dictionary per page."""
    dest_index = 0
    if bookmark.action:
        link_type, link_target, dest_index = convert_link(bookmark.action)
    else:
        dest = bookmark.to_dictionary_object(None)["/Dest"]
        dest_index = Page(dest[0]).index + 1
    results.append(f"{' '*level}{bookmark.title} - {dest_index}")
    dictionary[dest_index] = bookmark.title
    for child in bookmark.children:
        results, dictionary = convert_bookmark_item(
            child, results, dictionary, level=level + 1
        )
    return results, dictionary


def retrieve_bookmarks(pdf: Pdf) -> (list, dict):
    """Read bookmarks from a PDF file and return them as textual list and a dictionary.
    Note that the dictionary will only contain the last title specified of that page."""
    results, dictionary = [], {}
    with pdf.open_outline() as outline:
        for item in outline.root:
            results, dictionary = convert_bookmark_item(item, results, dictionary)
    return results, dictionary


def delete_bookmarks(pdf: Pdf) -> Pdf:
    """Delete all bookmarks from a PDF."""
    with pdf.open_outline() as outline:
        outline.root.clear()
    return pdf


def import_bookmarks(pdf: Pdf, infile: str) -> Pdf:
    """Import bookmarks from infile and add them to PDF."""
    pages, titles = read_toc(infile)
    for title, page in titles.items():
        pdf = add_bookmark(pdf, title, page)
    return pdf


def add_bookmark(pdf: Pdf, title: str, page: int) -> Pdf:
    """Add bookmark to a PDF file."""
    with pdf.open_outline() as outline:
        item = OutlineItem(title, page - 1)
        outline.root.append(item)
    return pdf


def remove_page(pdf: Pdf, index: int) -> Pdf:
    """Remove a specific page and all of its keys in the dictionary.
    Note that the index is 1-based."""
    print(f"Removing page {index}")
    page = pdf.pages.p(index)
    for key in page.keys():
        del page[key]
    del pdf.pages[index - 1]
    return pdf


def convert_link(dictionary: Dictionary):
    """Convert an annotation / dictionary item into a link."""
    link_index = 0
    if "/S" in dictionary and dictionary["/S"] == "/URI":
        link_type = "external"
        link_target = dictionary.get("/URI")
    elif "/S" in dictionary and dictionary["/S"] == "/GoTo":
        link_type = "internal"
        link_target = dictionary.get("/D")[0]
        dest_page, dest_type = Page(dictionary.get("/D")[0]), dictionary.get("/D")[1]
        link_index = dest_page.index + 1
    return link_type, link_target, link_index


def retrieve_links(
    pdf: Pdf, index: int = 0, detailed: bool = False, resolve: bool = False
):
    """Retrieve and print out all links of a specific page, or all pages.
    Output format is: pagenumber left top right bottom [INTERNAL|EXTERNAL] link."""
    if resolve:
        resolved = resolve_names(pdf)
    else:
        resolved = {}
    for page in pdf.pages:
        if not index or (index and (page.index == index - 1)):
            if "/Annots" in page:
                for annot in page.Annots:
                    if "/Subtype" in annot and annot.get("/Subtype") == "/Link":
                        if detailed:
                            print(annot)
                        link_type, link_target, link_name = ["", "", ""]
                        left, top, right, bottom = annot.get("/Rect")
                        if annot.get("/A").get("/S") == "/URI":
                            link_type = "external"
                            link_target = annot.get("/A").get("/URI")
                        if annot.get("/A").get("/S") == "/GoTo":
                            link_type = "internal"
                            link_target = annot.get("/A").get("/D")
                            link_name = resolved.get(link_target, "broken")
                        print(
                            f"{page.index + 1} {left} {top} {right} {bottom} {link_type} {link_target} {link_name}"
                        )


def resolve_names(pdf: Pdf):
    """Resolve named links to page numbers and return a dictionary."""
    result = {}
    for kid in pdf.Root.Names.Dests.Kids:
        names = kid.Names
        for i in range(0, len(names), 2):
            name, dest = names[i], names[i + 1]
            try:
                page = Page(dest[0])
                result[name] = int(page.index + 1)
            except ValueError:
                pass
    return result


def rewrite_named_links(
    pdf: Pdf,
    configuration: str = None,
    toc: str = None,
    outfile: str = None,
    detailed: bool = False,
    fit: bool = False,
) -> Pdf:
    """Print all named links with their corresponding page number.
    If configuration is given, rewrite the name link to another page number.
    If outfile is given, write the resulting PDF to a file.
    If fit is given, rewrite the type of link to fit"""
    transformation = read_links(configuration, toc=toc)
    for kid in pdf.Root.Names.Dests.Kids:
        names = kid.Names
        for i in range(0, len(names), 2):
            name, dest = names[i], names[i + 1]
            # dest[0] = Page
            # dest[1] can be either "/XYZ" with left top zoom as [2], [3], [4]
            #                or "/Fit"
            try:
                if detailed:
                    print(f"{dest[1]}")
                if str(dest[1]) == "/XYZ":
                    if detailed:
                        print(f"{dest[2]} {dest[3]} {dest[4]}")
                    if fit and outfile:
                        print(f"Changing type of {name} link to 'Fit'")
                        dest[1] = String("/Fit")
                if name in transformation:
                    page = pdf.pages.p(transformation[name])
                    dest[0] = page.obj
                    print(f"{name} rewriting {transformation[name]}")
                else:
                    page = Page(dest[0])
                    print(f"{name} {page.index + 1}")
            except ValueError:
                if name in transformation:
                    page = pdf.pages.p(transformation[name])
                    dest[0] = page.obj
                    print(f"{name} rewriting {transformation[name]}")
                else:
                    print(f"{name} broken")
    return pdf


def retrieve_notes(
    pdf: Pdf, headers: bool = False, index: int = 0, detailed: bool = False
) -> list:
    """Retrieve all text annotations of a specific page, or all pages.
    If headers is specified, show a header (or bookmark title) per page."""
    result = []
    header = ""
    if headers:
        bookmarks, dictionary = retrieve_bookmarks(pdf)
    for page in pdf.pages:
        if not index or (index and (page.index == index - 1)):
            if headers:
                if page.index + 1 in dictionary:
                    header = f"\n{dictionary[page.index + 1]} (page {page.index + 1})\n"
                else:
                    header = f"\nPage {page.index + 1}\n"
            if "/Annots" in page:
                for annot in page.Annots:
                    if "/Subtype" in annot and annot.get("/Subtype") == "/FreeText":
                        if detailed:
                            left, top, right, bottom = annot.get("/Rect")
                            header += f"\n{left} {top} {right} {bottom} "
                        result.append(f"{header}{annot.Contents}")
                        header = ""
    return result


@app.command()
def bookmarks(
    infile: str,
    outfile: str = "",
    add: str = "",
    delete: bool = False,
    importfile: str = "",
    title: str = "",
    page: int = None,
    verbose: bool = False,
):
    """Manage bookmarks.
    --add TITLE: add a single new bookmark with TITLE on page --page
    --delete: delete all current bookmarks
    --toc FILENAME: delete all current bookmarks, and import bookmarks from FILENAME."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    pdf = open_pdf(infile)
    if add and page and outfile:
        pdf = add_bookmark(pdf, title, page)
    if delete and outfile:
        pdf = delete_bookmarks(pdf)
    if importfile and outfile:
        pdf = delete_bookmarks(pdf)
        pdf = import_bookmarks(pdf, importfile)
    if outfile:
        save_pdf(pdf, outfile)
    else:
        bookmarks, dictionary = retrieve_bookmarks(pdf)
        for bookmark in bookmarks:
            print(bookmark)


@app.command()
def compare(original: str, modified: str) -> bool:
    """Compare the number of notes and bookmarks from two PDF files."""
    errors = False
    original_meta, modified_meta = {}, {}
    original_meta["notes"], modified_meta["notes"] = retrieve_notes(
        open_pdf(original)
    ), retrieve_notes(open_pdf(modified))
    original_meta["bookmarks"], modified_meta["bookmarks"] = retrieve_bookmarks(
        open_pdf(original)
    ), retrieve_bookmarks(open_pdf(modified))
    if len(original_meta["notes"]) != len(modified_meta["notes"]):
        print(
            f"Number of notes don't match: {len(original_meta['notes'])} versus {len(modified_meta['notes'])}",
            file=sys.stderr,
        )
        errors = True
    else:
        print(f"Same number of notes: {len(original_meta['notes'])}")
    if len(original_meta["bookmarks"]) != len(modified_meta["bookmarks"]):
        print(
            f"Number of bookmarks don't match: {len(original_meta['bookmarks'])} versus {len(modified_meta['bookmarks'])}",
            file=sys.stderr,
        )
        errors = True
    else:
        print(f"Same number of bookmarks: {len(original_meta['bookmarks'])}")
    sys.exit(errors)


@app.command()
def remove(infile: str, outfile: str, ranges: str):
    """Remove ranges of pages from a PDF file and save to outfile. Specify a range using a '-', and multiple ranges or numbers using a ','."""
    pages = []
    try:
        for segment in ranges.split(","):
            subsegment = segment.split("-")
            if len(subsegment) > 1:
                pages += range(int(subsegment[0]), int(subsegment[1]) + 1)
            else:
                pages.append(int(subsegment[0]))
    except ValueError as e:
        print(
            f"Specify ranges using integers and '-', and use a ',' to specify multiple ranges: {e}"
        )
        sys.exit(-1)
    pdf = open_pdf(infile)
    for delete in sorted(pages, reverse=True):
        pdf = remove_page(pdf, delete)
    save_pdf(pdf, outfile)


@app.command()
def notes(infile: str, page: int = 0, headers: bool = False, detailed: bool = False):
    """Extract all annotations as text on a specific page, or all pages.
    Optionally specify the location in the file."""
    pdf = open_pdf(infile)
    result = retrieve_notes(pdf, index=page, headers=headers, detailed=detailed)
    for note in result:
        print(note)


@app.command()
def page_links(
    infile: str, page: int = 0, resolve: bool = False, detailed: bool = False
):
    """Display links on a specific page, or all pages.\n
    Output format is: pagenumber left top right bottom [INTERNAL|EXTERNAL] link.\n
    When resolve is given, specify the page number of the link instead of the named link.
    """
    pdf = open_pdf(infile)
    retrieve_links(pdf, index=page, resolve=resolve, detailed=detailed)


@app.command()
def links(infile: str, detailed: bool = False):
    """Extract all named links.\n
    Output format is: NAME PAGENUMBER"""
    pdf = open_pdf(infile)
    rewrite_named_links(pdf, detailed=detailed)


@app.command()
def split(infile: str, prefix: str):
    """Split one PDF into multiple single pages. The name uses prefix and the page number."""
    pdf = open_pdf(infile)
    for index, page in enumerate(pdf.pages, 1):
        single = Pdf.new()
        single.pages.append(page)
        save_pdf(single, f"{prefix}-{index:03d}.pdf")


@app.command()
def rewrite(
    infile: str,
    outfile: str,
    linkfile: str,
    toc: str = None,
    fit: bool = False,
    verbose: bool = False,
):
    """Rewrite links in a PDF file based on a configuration file.\n
    If fit is given, rewrite type of link to 'Fit to page'.
    If toc is given, parse page numbers from a table of contents file."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    pdf = Pdf.open(infile)
    pdf = rewrite_named_links(
        pdf, configuration=linkfile, toc=toc, outfile=outfile, fit=fit
    )
    if toc:
        pdf = delete_bookmarks(pdf)
        pdf = import_bookmarks(pdf, toc)
    if outfile:
        save_pdf(pdf, outfile)


if __name__ == "__main__":
    app()
