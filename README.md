# SlideShare Presentation Downloader

A lightweight Python command-line tool for downloading SlideShare presentations as high-quality PDF files.

The tool extracts the presentation information from a SlideShare URL, allows you to select the image quality, downloads the slides temporarily, converts them into a PDF, and automatically removes the temporary images after successful PDF creation.

## Features

* Download SlideShare presentations from the command line
* Supports direct URL input using `-url` / `--url`
* Interactive URL input when no URL is provided
* Supports three image quality levels:

  * `320px`
  * `638px`
  * `2048px`
* Interactive quality selection
* Quality validation using the first slide before downloading the entire presentation
* Automatically retries with another quality if the selected quality fails
* Downloads slides with sequential names:

  * `slide_001.jpg`
  * `slide_002.jpg`
  * `slide_003.jpg`
  * etc.
* Uses a temporary `.temp` directory for downloaded images
* Converts downloaded images to RGB JPEG before PDF generation
* Creates the final PDF in the current working directory
* Automatically removes temporary images after successful PDF creation
* Keeps the temporary images if PDF creation fails, making troubleshooting easier

## Requirements

* Python 3.9 or newer
* Internet connection
* A valid SlideShare presentation URL

### Python packages

Install the required dependencies with:

```bash
pip install requests beautifulsoup4 img2pdf pillow
```

Or, if a `requirements.txt` file is included:

```bash
pip install -r requirements.txt
```

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/slideshare-downloader.git
```

Move into the project directory:

```bash
cd slideshare-downloader
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Interactive mode

Run the script without arguments:

```bash
python slideshare_downloader.py
```

The program will ask for the SlideShare URL and image quality.

Example:

```text
============================================================
        SlideShare Presentation Downloader
============================================================

Enter SlideShare URL: https://www.slideshare.net/slideshow/example/123456789

URL: https://www.slideshare.net/slideshow/example/123456789
Presentation: example

Connecting to SlideShare...

Slides found: 25

Select image quality:
------------------------------------------------------------
1. 320px
2. 638px
3. 2048px

Enter option [1-3]:
```

### Using a URL argument

You can provide the URL directly:

```bash
python slideshare_downloader.py -url "https://www.slideshare.net/slideshow/example/123456789"
```

### Specify image quality

You can also select the quality from the command line:

```bash
python slideshare_downloader.py -url "https://www.slideshare.net/slideshow/example/123456789" -q 2048
```

Available quality values:

```text
320
638
2048
```

For example:

```bash
python slideshare_downloader.py -url "https://www.slideshare.net/slideshow/example/123456789" -q 638
```

## How It Works

The downloader follows this process:

```text
SlideShare URL
      │
      ▼
Fetch SlideShare page
      │
      ▼
Extract slide image URL
      │
      ▼
Detect number of slides
      │
      ▼
Select image quality
      │
      ▼
Download first slide
      │
      ├── Failed ──► Select another quality
      │
      ▼
Create .temp directory
      │
      ▼
Download all slides
      │
      ▼
Convert images to RGB JPEG
      │
      ▼
Create PDF in current directory
      │
      ▼
Delete .temp directory
      │
      ▼
       Done
```

## Temporary Files

During the download process, images are stored in:

```text
.temp/
```

Example:

```text
.temp/
├── slide_001.jpg
├── slide_002.jpg
├── slide_003.jpg
├── slide_004.jpg
└── ...
```

These files are only temporary.

After successful PDF creation, the `.temp` directory and all downloaded images are automatically deleted.

If PDF creation fails, the temporary files are intentionally kept so that the problem can be investigated without downloading the entire presentation again.

## Output

The final PDF is created in the directory where the program is executed.

For example:

```text
softcore-processorpptxsoftcore-processorpptxsoftcore-processorpptx.pdf
```

The output filename is automatically generated from the presentation name extracted from the SlideShare URL.

## Example

Command:

```bash
python slideshare_downloader.py -url "https://www.slideshare.net/slideshow/softcore-processorpptxsoftcore-processorpptxsoftcore-processorpptx/266441920" -q 2048
```

Output:

```text
============================================================
              DOWNLOAD COMPLETE
============================================================
Slides : 181/181
Quality: 2048px
PDF    : C:\Users\User\slideshare-downloader\softcore-processorpptxsoftcore-processorpptxsoftcore-processorpptx.pdf
============================================================
```

## Error Handling

The program checks for several possible problems, including:

* Invalid SlideShare URLs
* Unable to access the SlideShare page
* Missing slide information
* Missing first slide image
* Invalid slide count
* Failed image downloads
* Empty image responses
* Unsupported image formats
* PDF conversion errors

If the first slide cannot be downloaded at the selected quality, the program asks:

```text
Try another quality? [Y/n]:
```

This allows you to test another available quality without restarting the entire program.

## Project Structure

```text
slideshare-downloader/
│
├── slideshare_downloader.py
├── requirements.txt
├── README.md
└── .gitignore
```

The `.temp` directory is generated only while the program is running and should not be committed to Git.

## `.gitignore`

It is recommended to add:

```gitignore
.temp/
__pycache__/
*.py[cod]
.venv/
venv/
.env
```

## Disclaimer

This project is intended for educational and personal use.

Please respect SlideShare's terms of service, copyright restrictions, and the rights of presentation authors. Only download and use presentations when you have the appropriate permission or when the content is otherwise legally available for your intended use.

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.
