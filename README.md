# PubMed PDF Downloader

`pubmed_pdf_downloader` is a Python package that allows users to bulk download PDFs of articles from PubMed Central using PMCIDs. The codebase is heavily copied over from [Pubmed-Batch-Download](https://github.com/billgreenwald/Pubmed-Batch-Download).

## Disclaimer

This tool is provided strictly for **personal study, academic research, and educational purposes**. It is not intended to infringe upon or circumvent the copyrights or intellectual property rights of any publisher, author, or rights holder.

- **Open Access only.** This tool primarily downloads articles from the [PMC Open Access Subset](https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/), which are made freely available under open licenses (e.g., Creative Commons). Users must respect the license terms attached to each individual article.
- **No circumvention of access controls.** This tool does not bypass paywalls, authentication mechanisms, or digital rights management (DRM) protections. It only retrieves content that is publicly and freely available.
- **User responsibility.** Users are solely responsible for ensuring that their use of downloaded content complies with applicable copyright laws, publisher terms of service, and the specific license under which each article is distributed. Bulk downloading may violate the terms of service of certain platforms even for open-access content.
- **No redistribution.** Downloaded articles should not be redistributed, republished, or used for commercial purposes unless explicitly permitted by the article's license.
- **Fair Use.** In jurisdictions that recognize fair use or fair dealing, downloading articles for private study or non-commercial research may be permitted, but this depends on local law and the specifics of each case.

The authors and contributors of this tool accept no liability for any misuse. If you are a rights holder and believe this tool facilitates infringement, please open an issue and we will address it promptly.

## Installation

To install the package, clone the repository and run the setup script:

```sh
git clone https://github.com/yourusername/pubmed_pdf_downloader.git
cd pubmed_pdf_downloader
pip install .
```
Alternatively, you can use pip once the package is uploaded to PyPI:
```
pip install pubmed_pdf_downloader
```

## Usage
To use the tool from the command line:
```
pubmed-pdf-downloader -pmf pmcids.txt -out fetched_pdfs -batch 5 -delay 10
```
This command will download PDFs listed in pmcids.txt to the fetched_pdfs directory, with a delay of 10 seconds after every 5 downloads.

Arguments
- `pmcids`: Comma-separated list of PMCIDs to fetch.
- `pmf`: File containing PMCIDs to fetch, one per line. If provided, -pmcids should not be used.
- `out`: Directory where downloaded PDFs will be saved.
- `errors`: Output file for recording PMCIDs that failed to download.
- `maxRetries`: Maximum number of retries for each article in case of failure.
- `batch`: Number of files to query before introducing a delay.
- `delay`: Time delay (in seconds) after each batch of queries.
