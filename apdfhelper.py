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
from pikepdf import Page, Pdf, String

app = typer.Typer()


def read_links(filename):
    """Return a dictionary with named links and their page numbers.
    Format of the file is NAME PAGENUMBER.
    Note that NAME can contain spaces: The last value at the right is chosen."""
    result = {}
    if not filename:
        return result
    try:
        with open(filename, "r") as filehandle:
            for line in filehandle.read().splitlines():
                line = line.split(" ")
                # Take the outermost value, as sometimes names have spaces in them
                try:
                    result[line[0]] = int(line[len(line) - 1])
                except ValueError:
                    print(f"Could not read a valid page number for {line[0]}")
    except IOError:
        logging.error("Could not read %s", filename)
    print(f"Read {len(result)} links")
    return result


def save_pdf(pdf, filename="output.pdf"):
    """Save PDF to output file."""
    print(f"Saving PDF to {filename}")
    try:
        pdf.save(filename)
    except Exception as e:
        print(f"Could not save to {filename}: {e}")


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
                            if link_target in resolved:
                                link_name = resolved[link_target]
                            else:
                                link_name = "broken"
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
    outfile: str = None,
    detailed: bool = False,
    fit: bool = False,
):
    """Print all named links with their corresponding page number.
    If configuration is given, rewrite the name link to another page number.
    If outfile is given, write the resulting PDF to a file.
    If fit is given, rewrite the type of link to fit"""
    transformation = read_links(configuration)
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
    if outfile:
        save_pdf(pdf, outfile)


def retrieve_annotations(pdf: Pdf, location: bool = False, index: int = 0):
    """Retrieve all text annotations of a specific page, or all pages."""
    header = ""
    for page in pdf.pages:
        if not index or (index and (page.index == index - 1)):
            if location:
                header = f"\nPage {page.index + 1}\n"
            if "/Annots" in page:
                for annot in page.Annots:
                    if "/Subtype" in annot and annot.get("/Subtype") == "/FreeText":
                        #                        left, top, right, bottom = annot.get("/Rect")
                        print(f"{header}{annot.Contents}")
                        header = ""


def open_pdf(infile: str) -> Pdf:
    """Open a PDF file."""
    try:
        pdf = Pdf.open(infile)
        return pdf
    except Exception as e:
        print(f"Could not open {infile}: {e}")
        sys.exit(-1)


@app.command()
def remove(infile: str, outfile: str, start: int, stop: int):
    """Remove one or more pages from a PDF file and save to outfile."""
    pdf = open_pdf(infile)
    if stop < start or stop > len(pdf.pages):
        print(
            f"Please specify a valid range for start and stop: {len(pdf.pages)} pages found"
        )
        sys.exit(-1)
    for delete in reversed(range(start, stop + 1)):
        print(f"Removing page {delete}")
        page = pdf.pages.p(delete)
        for key in page.keys():
            del page[key]
        del pdf.pages[delete - 1]
    save_pdf(pdf, outfile)


@app.command()
def notes(infile: str, page: int = 0, location: bool = False):
    """Extract all annotations as text on a specific page, or all pages.
    Optionally specify the location in the file."""
    pdf = open_pdf(infile)
    retrieve_annotations(pdf, index=page, location=location)


@app.command()
def page_links(infile: str, page: int = 0, resolve: bool = False):
    """Display links on a specific page, or all pages.\n
    Output format is: pagenumber left top right bottom [INTERNAL|EXTERNAL] link.\n
    When resolve is given, specify the page number of the link instead of the named link.
    """
    pdf = open_pdf(infile)
    retrieve_links(pdf, index=page, resolve=resolve)


@app.command()
def links(infile: str, detailed: bool = False):
    """Extract all named links.\n
    Output format is: NAME PAGENUMBER"""
    pdf = open_pdf(infile)
    rewrite_named_links(pdf, configuration=None, outfile=None, detailed=detailed)


@app.command()
def rewrite(infile: str, outfile: str, linkfile: str, fit: bool = False):
    """Rewrite links in a PDF file based on a configuration file.\n
    If fit is given, rewrite type of link to 'Fit to page'."""
    pdf = Pdf.open(infile)
    rewrite_named_links(pdf, configuration=linkfile, outfile=outfile, fit=fit)


if __name__ == "__main__":
    app()
