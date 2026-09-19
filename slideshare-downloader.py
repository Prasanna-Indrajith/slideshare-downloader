import argparse
import shutil
from pathlib import Path
from urllib.parse import urlparse

import img2pdf
import requests
from bs4 import BeautifulSoup
from PIL import Image


QUALITY_OPTIONS = (320, 638, 2048)
REQUEST_TIMEOUT = 30

TEMP_DIRECTORY_NAME = ".temp"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


def print_header():
    """Display the application header."""
    print()
    print("=" * 60)
    print("        SlideShare Presentation Downloader")
    print("=" * 60)
    print()


def print_separator():
    """Print a terminal separator."""
    print("-" * 60)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Download a SlideShare presentation "
            "and convert it to PDF."
        )
    )

    parser.add_argument(
        "-url",
        "--url",
        dest="url",
        help="SlideShare presentation URL",
    )

    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        choices=QUALITY_OPTIONS,
        help="Image quality in pixels (320, 638, or 2048)",
    )

    return parser.parse_args()


def is_valid_url(url):
    """Check whether the URL is a valid SlideShare URL."""
    try:
        parsed_url = urlparse(url)

        return (
            parsed_url.scheme in ("http", "https")
            and bool(parsed_url.netloc)
            and "slideshare.net" in parsed_url.netloc.lower()
        )

    except Exception:
        return False


def get_url_from_user():
    """Prompt the user for a SlideShare URL."""
    while True:
        url = input("Enter SlideShare URL: ").strip()

        if not url:
            print("Error: URL cannot be empty.")
            continue

        if not is_valid_url(url):
            print("Error: Please enter a valid SlideShare URL.")
            continue

        return url


def get_presentation_name(url):
    """Extract the presentation name from the SlideShare URL."""
    try:
        presentation_part = url.split("/slideshow/", 1)[1]
        presentation_name = presentation_part.split("/", 1)[0]

        if presentation_name:
            return presentation_name

    except (IndexError, AttributeError):
        pass

    return "slideshare_presentation"


def get_quality_from_user():
    """Prompt the user to select image quality."""
    print()
    print("Select image quality:")
    print_separator()

    for index, quality in enumerate(
        QUALITY_OPTIONS,
        start=1,
    ):
        print(f"{index}. {quality}px")

    print()

    while True:
        try:
            selected_option = int(
                input("Enter option [1-3]: ").strip()
            )

            if 1 <= selected_option <= len(QUALITY_OPTIONS):
                return QUALITY_OPTIONS[selected_option - 1]

            print(
                "Invalid option. "
                "Please select 1, 2, or 3."
            )

        except ValueError:
            print(
                "Invalid input. "
                "Please enter a number."
            )


def ask_try_another_quality():
    """Ask whether the user wants to try another quality."""
    while True:
        choice = input(
            "\nTry another quality? [Y/n]: "
        ).strip().lower()

        if choice in ("", "y", "yes"):
            return True

        if choice in ("n", "no"):
            return False

        print("Please enter Y or N.")


def create_http_session():
    """Create a configured HTTP session."""
    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": USER_AGENT
        }
    )

    return session


def fetch_presentation(url, session):
    """Download and parse the SlideShare page."""
    print()
    print("Connecting to SlideShare...")

    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not access the SlideShare page:\n{error}"
        ) from error

    return BeautifulSoup(
        response.content,
        "html.parser",
    )


def extract_slide_information(soup):
    """
    Extract:
        - Base slide image URL
        - Total number of slides
    """

    first_slide = soup.find(id="slide1")

    if not first_slide:
        raise RuntimeError(
            "Could not find slide information "
            "on the SlideShare page."
        )

    image = first_slide.find("img")

    if not image:
        raise RuntimeError(
            "Could not find the first slide image."
        )

    base_url = image.get("src")

    if not base_url:
        raise RuntimeError(
            "The first slide does not contain "
            "a valid image URL."
        )

    slide_preview = soup.find(
        id="slide-preview-0"
    )

    if not slide_preview:
        raise RuntimeError(
            "Could not determine the number of slides."
        )

    aria_label = slide_preview.get(
        "aria-label",
        "",
    )

    prefix = "Slide 1 of "

    if not aria_label.startswith(prefix):
        raise RuntimeError(
            "Could not determine the number of slides."
        )

    try:
        slide_count = int(
            aria_label.replace(prefix, "")
        )

    except ValueError as error:
        raise RuntimeError(
            "Invalid slide count received "
            "from SlideShare."
        ) from error

    if slide_count <= 0:
        raise RuntimeError(
            "Invalid slide count."
        )

    return base_url, slide_count


def build_slide_url(
    base_url,
    quality,
    slide_number,
):
    """Build the URL for a specific slide."""

    quality_url = base_url.replace(
        "320",
        str(quality),
    )

    quality_url = quality_url.replace(
        "/85/",
        "/75/",
    )

    if slide_number == 1:
        return quality_url

    return quality_url.replace(
        "-1-",
        f"-{slide_number}-",
        1,
    )


def create_temp_directory():
    """
    Create a temporary image directory.

    If an old .temp directory exists, remove it first.
    """

    temporary_directory = Path(
        TEMP_DIRECTORY_NAME
    )

    if temporary_directory.exists():
        shutil.rmtree(
            temporary_directory
        )

    temporary_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return temporary_directory


def remove_temp_directory(
    temporary_directory,
):
    """Remove the temporary image directory."""

    if temporary_directory.exists():
        try:
            shutil.rmtree(
                temporary_directory
            )

        except OSError as error:
            print()
            print(
                "Warning: Could not remove "
                f"temporary directory: {error}"
            )


def download_first_slide(
    base_url,
    quality,
    temporary_directory,
    session,
):
    """
    Download slide 1.

    This is used as the quality validation step.

    Returns:
        True  -> success
        False -> failure
    """

    slide_url = build_slide_url(
        base_url=base_url,
        quality=quality,
        slide_number=1,
    )

    slide_path = (
        temporary_directory
        / "slide_001.jpg"
    )

    print()
    print(
        f"Testing {quality}px quality..."
    )

    print(
        "[  1] Downloading first slide...",
        end=" ",
        flush=True,
    )

    try:
        response = session.get(
            slide_url,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            print(
                f"FAILED "
                f"(HTTP {response.status_code})"
            )
            return False

        if not response.content:
            print("FAILED (empty response)")
            return False

        slide_path.write_bytes(
            response.content
        )

        print("OK")

        return True

    except requests.RequestException as error:
        print(f"FAILED ({error})")
        return False


def download_remaining_slides(
    base_url,
    quality,
    slide_count,
    temporary_directory,
    session,
):
    """Download slides 2 through the final slide."""

    downloaded_count = 1

    if slide_count == 1:
        return downloaded_count

    print()
    print("Downloading remaining slides...")
    print_separator()

    for slide_number in range(
        2,
        slide_count + 1,
    ):

        slide_url = build_slide_url(
            base_url=base_url,
            quality=quality,
            slide_number=slide_number,
        )

        slide_path = (
            temporary_directory
            / f"slide_{slide_number:03d}.jpg"
        )

        try:
            response = session.get(
                slide_url,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:

                if not response.content:
                    print(
                        f"[{slide_number:>3}/"
                        f"{slide_count}] "
                        f"Failed - empty response"
                    )
                    continue

                slide_path.write_bytes(
                    response.content
                )

                downloaded_count += 1

                print(
                    f"[{slide_number:>3}/"
                    f"{slide_count}] "
                    f"Downloaded"
                )

            else:
                print(
                    f"[{slide_number:>3}/"
                    f"{slide_count}] "
                    f"Failed - "
                    f"HTTP {response.status_code}"
                )

        except requests.RequestException as error:
            print(
                f"[{slide_number:>3}/"
                f"{slide_count}] "
                f"Failed - {error}"
            )

    return downloaded_count


def convert_to_pdf(
    temporary_directory,
    presentation_name,
):
    """
    Convert downloaded slide images into a PDF.

    The PDF is created in the current working directory.
    """

    image_files = sorted(
        temporary_directory.glob(
            "slide_*.jpg"
        )
    )

    if not image_files:
        raise RuntimeError(
            "No slide images were found."
        )

    print()
    print("Preparing images for PDF...")

    converted_files = []

    for image_path in image_files:

        try:
            with Image.open(
                image_path
            ) as image:

                # Convert RGBA / LA / P / RGB etc.
                # into a normal RGB image.
                if image.mode != "RGB":
                    image = image.convert("RGB")

                image.save(
                    image_path,
                    "JPEG",
                    quality=95,
                )

            converted_files.append(
                str(image_path)
            )

        except Exception as error:
            raise RuntimeError(
                f"Could not process "
                f"{image_path.name}: {error}"
            ) from error

    # PDF is created in the current directory.
    pdf_path = (
        Path.cwd()
        / f"{presentation_name}.pdf"
    )

    print()
    print("Converting slides to PDF...")

    try:
        with open(
            pdf_path,
            "wb",
        ) as pdf_file:

            pdf_file.write(
                img2pdf.convert(
                    converted_files
                )
            )

    except Exception as error:

        raise RuntimeError(
            f"Could not create PDF:\n{error}"
        ) from error

    return pdf_path


def download_presentation(
    presentation_name,
    slide_count,
    base_url,
    requested_quality,
    session,
):
    """
    Handle quality selection, complete download,
    PDF conversion and temporary file cleanup.
    """

    while True:

        if requested_quality is not None:
            selected_quality = requested_quality

            print()
            print(
                f"Selected quality: "
                f"{selected_quality}px"
            )

        else:
            selected_quality = (
                get_quality_from_user()
            )

        print()
        print(
            f"Testing quality: "
            f"{selected_quality}px"
        )

        print_separator()

        # ----------------------------------------------------
        # Create temporary image directory
        # ----------------------------------------------------

        temporary_directory = (
            create_temp_directory()
        )

        # ----------------------------------------------------
        # Test first slide
        # ----------------------------------------------------

        first_slide_success = (
            download_first_slide(
                base_url=base_url,
                quality=selected_quality,
                temporary_directory=temporary_directory,
                session=session,
            )
        )

        if not first_slide_success:

            remove_temp_directory(
                temporary_directory
            )

            print()
            print_separator()
            print(
                f"Quality {selected_quality}px "
                "failed."
            )
            print_separator()

            if not ask_try_another_quality():
                print()
                print("Download cancelled.")
                return None

            # Force interactive quality selection
            # after a failed attempt.
            requested_quality = None

            continue

        print()
        print(
            f"Quality {selected_quality}px "
            "is working."
        )

        print()
        print(
            f"Temporary directory: "
            f"{temporary_directory}"
        )

        # ----------------------------------------------------
        # Download remaining slides
        # ----------------------------------------------------

        downloaded_count = (
            download_remaining_slides(
                base_url=base_url,
                quality=selected_quality,
                slide_count=slide_count,
                temporary_directory=temporary_directory,
                session=session,
            )
        )

        print()
        print(
            f"Downloaded: "
            f"{downloaded_count}/"
            f"{slide_count} slides"
        )

        # ----------------------------------------------------
        # Check whether every slide was downloaded
        # ----------------------------------------------------

        if downloaded_count != slide_count:

            print()
            print(
                "Error: Not all slides were downloaded."
            )

            print(
                f"Expected: {slide_count}"
            )

            print(
                f"Downloaded: {downloaded_count}"
            )

            print()
            print(
                "Temporary images were kept at:"
            )

            print(
                f"{temporary_directory.resolve()}"
            )

            return None

        # ----------------------------------------------------
        # Convert images to PDF
        # ----------------------------------------------------

        try:

            pdf_path = convert_to_pdf(
                temporary_directory=temporary_directory,
                presentation_name=presentation_name,
            )

        except RuntimeError as error:

            print()
            print(
                f"Error: {error}"
            )

            print()
            print(
                "Temporary images were kept at:"
            )

            print(
                f"{temporary_directory.resolve()}"
            )

            return None

        # ----------------------------------------------------
        # PDF created successfully
        # ----------------------------------------------------

        print()
        print(
            "PDF created successfully."
        )

        # ----------------------------------------------------
        # Remove temporary images
        # ----------------------------------------------------

        print(
            "Removing temporary images..."
        )

        remove_temp_directory(
            temporary_directory
        )

        return {
            "pdf_path": pdf_path,
            "downloaded_count": downloaded_count,
            "slide_count": slide_count,
            "quality": selected_quality,
        }


def main():
    """Application entry point."""

    print_header()

    arguments = parse_arguments()

    # --------------------------------------------------------
    # Get URL
    # --------------------------------------------------------

    url = arguments.url

    if not url:
        url = get_url_from_user()

    if not is_valid_url(url):
        print()
        print(
            "Error: Invalid SlideShare URL."
        )
        return 1

    print(
        f"URL: {url}"
    )

    # --------------------------------------------------------
    # Presentation name
    # --------------------------------------------------------

    presentation_name = (
        get_presentation_name(url)
    )

    print(
        f"Presentation: "
        f"{presentation_name}"
    )

    # --------------------------------------------------------
    # HTTP session
    # --------------------------------------------------------

    session = create_http_session()

    # --------------------------------------------------------
    # Fetch SlideShare page
    # --------------------------------------------------------

    try:

        soup = fetch_presentation(
            url=url,
            session=session,
        )

        (
            base_url,
            slide_count,
        ) = extract_slide_information(
            soup
        )

    except RuntimeError as error:

        print()
        print(
            f"Error: {error}"
        )

        return 1

    # --------------------------------------------------------
    # Presentation information
    # --------------------------------------------------------

    print()
    print(
        f"Slides found: {slide_count}"
    )

    # --------------------------------------------------------
    # Download presentation
    # --------------------------------------------------------

    result = download_presentation(
        presentation_name=presentation_name,
        slide_count=slide_count,
        base_url=base_url,
        requested_quality=arguments.quality,
        session=session,
    )

    if result is None:
        return 1

    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("              DOWNLOAD COMPLETE")
    print("=" * 60)

    print(
        f"Slides : "
        f"{result['downloaded_count']}/"
        f"{result['slide_count']}"
    )

    print(
        f"Quality: "
        f"{result['quality']}px"
    )

    print(
        f"PDF    : "
        f"{result['pdf_path']}"
    )

    print("=" * 60)
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())