# Pandoc: The Universal Document Converter

## What is Pandoc?

Pandoc is a powerful, open-source command-line tool that can convert files from one markup format into another. It is often described as the "Swiss-army knife" of document conversion due to the vast number of formats it supports. If you need to write a document in a comfortable format like Markdown and then convert it into a polished, professional format like PDF, DOCX, or a web page, Pandoc is the tool for the job.

Its strength lies in its ability to understand the semantic structure of a document, rather than just its appearance. This allows it to produce high-quality output that preserves headings, lists, tables, citations, and other structural elements across different formats.

## Key Features

-   **Wide Format Support**: Pandoc can read dozens of formats (including various flavors of Markdown, HTML, LaTeX, reStructuredText, and Word DOCX) and write to even more (including PDF, HTML5, EPUB, and slide show formats).
-   **High-Quality Typesetting**: When converting to PDF, Pandoc uses LaTeX by default, producing professional, publication-quality documents with excellent typography.
-   **Citation and Bibliography Support**: Pandoc has first-class support for citations using `citeproc`. It can automatically generate bibliographies in a wide variety of styles from sources like BibTeX, EndNote, or CSL JSON.
-   **Extensibility**: The tool can be extended with custom filters and writers written in Lua, allowing for complex transformations and the addition of new output formats.
-   **Cross-Platform**: Pandoc is available for Windows, macOS, and Linux, making it a reliable tool in any development environment.

## Installation

### Windows

For Windows, it's recommended to install Pandoc using the official installer, which will also install the necessary dependencies for PDF generation (like a LaTeX distribution).

1.  Download the latest installer from the [Pandoc GitHub releases page](https://github.com/jgm/pandoc/releases).
2.  Run the `.msi` installer and follow the on-screen instructions.
3.  The installer will automatically add Pandoc to your system's PATH, making it available from any command prompt (like PowerShell or CMD).

### macOS

Using Homebrew is the easiest way to install Pandoc on macOS:

```bash
brew install pandoc
```

For PDF output, you will also need a LaTeX distribution like MacTeX:

```bash
brew install --cask mactex
```

### Linux

On Debian/Ubuntu-based systems, you can install Pandoc using `apt`:

```bash
sudo apt-get install pandoc
```

## Common Usage Examples

Pandoc is run from the command line. The basic syntax is `pandoc [options] input_file -o output_file`.

### 1. Markdown to DOCX

This is a very common use case for creating reports or documents that need to be shared with non-technical users.

```bash
pandoc my_report.md -o my_report.docx
```

### 2. Markdown to PDF

To create a high-quality PDF, you need a LaTeX engine installed. The `-s` or `--standalone` flag is used to create a complete document with a proper header and footer.

```bash
pandoc --standalone my_document.md -o my_document.pdf
```

### 3. Markdown to HTML

Pandoc can generate clean, semantic HTML5. You can also embed a CSS stylesheet for styling.

```bash
# Simple conversion
pandoc my_article.md -o my_article.html

# Standalone HTML with a title and CSS
pandoc --standalone my_article.md --css=style.css --metadata title="My Awesome Article" -o my_article.html
```

### 4. Using a Reference Document for Styling

When converting to DOCX, you can use an existing Word document as a "template" to define the styles for your output file. This is incredibly useful for adhering to corporate branding or specific formatting requirements.

```bash
pandoc my_report.md --reference-doc=template.docx -o my_report.docx
```

In this example, Pandoc will use the styles (like Heading 1, Normal, etc.) defined in `template.docx` and apply them to the corresponding elements from `my_report.md`.
