import argparse
import sys
import os
import requests
from bs4 import BeautifulSoup
import re
import urllib
import time
import tarfile
import io

# code heavily taken from: https://github.com/billgreenwald/Pubmed-Batch-Download

def get_main_url(url):
    return "/".join(url.split("/")[:3])

def save_pdf_from_url(pdf_url, directory, name, headers):
    """Download a PDF from the given URL and save it. Returns True on success, False on failure."""
    try:
        # Handle OA tar.gz archives
        if pdf_url.startswith('oa_tgz:'):
            return _save_pdf_from_tgz(pdf_url[7:], directory, name, headers)

        response = requests.get(pdf_url, headers=headers, allow_redirects=True, timeout=30)
        response.raise_for_status()

        # Check if content is actually a PDF
        if not response.content.startswith(b'%PDF'):
            print(f"** Content from {pdf_url} is not a PDF (first bytes: {response.content[:20]})")
            return False

        with open(f'{directory}/{name}.pdf', 'wb') as f:
            f.write(response.content)
        print(f"** Successfully fetched and saved PDF for PMCID {name}. File size: {len(response.content)} bytes")
        return True
    except requests.RequestException as e:
        print(f"** Failed to download PDF from {pdf_url}: {e}")
        return False

def _save_pdf_from_tgz(tgz_url, directory, name, headers):
    """Download a tar.gz from the PMC OA archive and extract the PDF."""
    try:
        print(f"** Downloading OA archive from {tgz_url}...")
        response = requests.get(tgz_url, headers=headers, allow_redirects=True, timeout=120)
        response.raise_for_status()

        tar = tarfile.open(fileobj=io.BytesIO(response.content), mode='r:gz')
        pdf_members = [m for m in tar.getmembers() if m.name.endswith('.pdf')]
        if not pdf_members:
            print(f"** No PDF found in OA archive from {tgz_url}")
            return False

        pdf_data = tar.extractfile(pdf_members[0]).read()
        if not pdf_data.startswith(b'%PDF'):
            print(f"** Extracted file is not a valid PDF")
            return False

        with open(f'{directory}/{name}.pdf', 'wb') as f:
            f.write(pdf_data)
        print(f"** Successfully extracted and saved PDF for PMCID {name}. File size: {len(pdf_data)} bytes")
        return True
    except Exception as e:
        print(f"** Failed to extract PDF from OA archive: {e}")
        return False

def fetch(pmcid, finders, name, headers, error_pmids, args):
    uri = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid.strip()}"
    success = False
    if os.path.exists(f"{args['out']}/{pmcid}.pdf"):
        print(f"** Reprint #{pmcid} already downloaded and in folder; skipping.")
        return

    try:
        req = requests.get(uri, headers=headers)
        req.raise_for_status()
        soup = BeautifulSoup(req.content, 'html.parser')
        for finder in finders:
            print(f"Trying {finder}")
            pdf_url = eval(finder)(req, soup, headers)
            if pdf_url:
                if save_pdf_from_url(pdf_url, args['out'], name, headers):
                    success = True
                    break

        if not success:
            print(f"** Reprint {pmcid} could not be fetched with the current finders.")
            error_pmids.write(f"{pmcid}\t{name}\n")

    except requests.RequestException as e:
        print(f"** Request failed for PMCID {pmcid}: {e}")
        error_pmids.write(f"{pmcid}\t{name}\n")

def acs_publications(req, soup, headers):
    possible_links = [x for x in soup.find_all('a') if x.get('title') and ('high-res pdf' in x.get('title').lower() or 'low-res pdf' in x.get('title').lower())]
    if possible_links:
        print("** Fetching reprint using the 'ACS Publications' finder...")
        return get_main_url(req.url) + possible_links[0].get('href')
    return None

def future_medicine(req, soup, headers):
    possible_links = soup.find_all('a', attrs={'href': re.compile("/doi/pdf")})
    if possible_links:
        print("** Fetching reprint using the 'Future Medicine' finder...")
        return get_main_url(req.url) + possible_links[0].get('href')
    return None

def generic_citation_labelled(req, soup, headers):
    possible_links = soup.find_all('meta', attrs={'name': 'citation_pdf_url'})
    if possible_links:
        print("** Fetching reprint using the 'Generic Citation Labelled' finder...")
        return possible_links[0].get('content')
    return None

def nejm(req, soup, headers):
    possible_links = [x for x in soup.find_all('a') if x.get('data-download-type') and (x.get('data-download-type').lower() == 'article pdf')]
    if possible_links:
        print("** Fetching reprint using the 'NEJM' finder...")
        return get_main_url(req.url) + possible_links[0].get('href')
    return None

def pubmed_central_v2(req, soup, headers):
    possible_links = soup.find_all('a', attrs={'href': re.compile('/pmc/articles')})
    if possible_links:
        print("** Fetching reprint using the 'PubMed Central' finder...")
        return f"https://www.ncbi.nlm.nih.gov{possible_links[0].get('href')}"
    return None

def science_direct(req, soup, headers):
    try:
        new_uri = urllib.parse.unquote(soup.find_all('input')[0].get('value'))
        req = requests.get(new_uri, allow_redirects=True, headers=headers)
        req.raise_for_status()
        soup = BeautifulSoup(req.content, 'html.parser')
        possible_links = soup.find_all('meta', attrs={'name': 'citation_pdf_url'})
        if possible_links:
            print("** Fetching reprint using the 'Science Direct' finder...")
            return possible_links[0].get('content')
    except Exception as e:
        print(f"** Error in Science Direct finder: {e}")
    return None

def uchicago_press(req, soup, headers):
    possible_links = [x for x in soup.find_all('a') if x.get('href') and 'pdf' in x.get('href') and '.edu/doi/' in x.get('href')]
    if possible_links:
        print("** Fetching reprint using the 'UChicago Press' finder...")
        return get_main_url(req.url) + possible_links[0].get('href')
    return None

def europe_pmc_service(req, soup, headers):
    """Use Europe PMC service for PDF downloads"""
    pmc_match = re.search(r'PMC\d+', req.url)
    if pmc_match:
        pmc_id = pmc_match.group()
        print(f"** Fetching reprint using the 'Europe PMC Service' finder for {pmc_id}...")
        return f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmc_id}&blobtype=pdf"
    return None

def pmc_direct_pdf(req, soup, headers):
    """Try the direct PMC PDF URL pattern."""
    pmc_match = re.search(r'PMC\d+', req.url)
    if pmc_match:
        pmc_id = pmc_match.group()
        # Look for the PDF link in the page's download section
        pdf_link = soup.find('a', attrs={'href': re.compile(rf'/pmc/articles/{pmc_id}/pdf/')})
        if pdf_link:
            pdf_url = f"https://www.ncbi.nlm.nih.gov{pdf_link.get('href')}"
            print(f"** Fetching reprint using the 'PMC Direct PDF' finder for {pmc_id}...")
            return pdf_url
    return None

def pmc_oa_service(req, soup, headers):
    """Use the PMC Open Access web service to get the PDF from the OA archive.
    This bypasses the PoW challenge on the PMC website by downloading
    from the FTP/HTTPS archive directly."""
    pmc_match = re.search(r'PMC\d+', req.url)
    if not pmc_match:
        return None

    pmc_id = pmc_match.group()
    print(f"** Trying 'PMC OA Service' finder for {pmc_id}...")

    try:
        oa_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmc_id}"
        oa_resp = requests.get(oa_url, headers=headers, timeout=30)
        oa_resp.raise_for_status()

        oa_soup = BeautifulSoup(oa_resp.content, 'html.parser')
        link = oa_soup.find('link', attrs={'format': 'tgz'})
        if not link:
            print(f"** {pmc_id} not found in PMC Open Access subset.")
            return None

        tgz_url = link.get('href', '')
        # Convert FTP to HTTPS
        tgz_url = tgz_url.replace('ftp://ftp.ncbi.nlm.nih.gov/', 'https://ftp.ncbi.nlm.nih.gov/')
        return f"oa_tgz:{tgz_url}"
    except requests.RequestException as e:
        print(f"** PMC OA Service failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser._optionals.title = "Flag Arguments"
    parser.add_argument('-pmcids', help="Comma-separated list of PMCIDs to fetch. Must include -pmcids or -pmf.", default='%#$')
    parser.add_argument('-pmf', help="File with PMCIDs to fetch, one per line. Optionally, the file can be a TSV with a second column of names to save each PMCID's article with (without '.pdf' at the end). Must include -pmcids or -pmf", default='%#$')
    parser.add_argument('-out', help="Output directory for fetched articles. Default: fetched_pdfs", default="fetched_pdfs")
    parser.add_argument('-errors', help="Output file path for PMCIDs which failed to fetch. Default: unfetched_pmcids.tsv", default="unfetched_pmcids.tsv")
    parser.add_argument('-maxRetries', help="Change max number of retries per article on error 104. Default: 3", default=3, type=int)
    parser.add_argument('-batch', help="Number of files to query before waiting. Default: 10", default=10, type=int)
    parser.add_argument('-delay', help="Time delay in seconds after each batch of queries. Default: 5 seconds", default=5, type=int)
    args = vars(parser.parse_args())

    # Validate arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        exit(1)
    if args['pmcids'] == '%#$' and args['pmf'] == '%#$':
        print("Error: Either -pmcids or -pmf must be used. Exiting.")
        exit(1)
    if args['pmcids'] != '%#$' and args['pmf'] != '%#$':
        print("Error: -pmcids and -pmf cannot be used together. Ignoring -pmf argument.")
        args['pmf'] = '%#$'

    # Create output directory if it doesn't exist
    if not os.path.exists(args['out']):
        print(f"Output directory of {args['out']} did not exist. Created the directory.")
        os.mkdir(args['out'])

    headers = requests.utils.default_headers()
    headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

    if args['pmcids'] != '%#$':
        pmcids = args['pmcids'].split(",")
        names = pmcids
    else:
        pmcids = [line.strip().split() for line in open(args['pmf'])]
        if len(pmcids[0]) == 1:
            pmcids = [x[0] for x in pmcids]
            names = pmcids
        else:
            names = [x[1] for x in pmcids]
            pmcids = [x[0] for x in pmcids]

    finders = [
        'pmc_oa_service',
        'pmc_direct_pdf',
        'generic_citation_labelled',
        'pubmed_central_v2',
        'acs_publications',
        'uchicago_press',
        'nejm',
        'future_medicine',
        'science_direct',
        'europe_pmc_service',
    ]

    batch_count = 0
    with open(args['errors'], 'w+') as error_pmids:
        for pmcid, name in zip(pmcids, names):
            print(f"Trying to fetch PMCID {pmcid.strip()}")
            retries_so_far = 0
            while retries_so_far < args['maxRetries']:
                try:
                    fetch(pmcid, finders, name, headers, error_pmids, args)
                    retries_so_far = args['maxRetries']
                except requests.ConnectionError as e:
                    if '104' in str(e):
                        retries_so_far += 1
                        if retries_so_far < args['maxRetries']:
                            print(f"** Fetching of reprint {pmcid} failed due to error {e}, retrying ({retries_so_far}/{args['maxRetries']})")
                        else:
                            print(f"** Fetching of reprint {pmcid} failed after max retries due to error {e}")
                            error_pmids.write(f"{pmcid}\t{name}\n")
                    else:
                        print(f"** Fetching of reprint {pmcid} failed due to error {e}")
                        retries_so_far = args['maxRetries']
                        error_pmids.write(f"{pmcid}\t{name}\n")
                except Exception as e:
                    print(f"** Fetching of reprint {pmcid} failed due to error {e}")
                    retries_so_far = args['maxRetries']
                    error_pmids.write(f"{pmcid}\t{name}\n")
            batch_count += 1
            if batch_count % args['batch'] == 0:
                print(f"** Reached batch limit of {args['batch']} requests. Waiting for {args['delay']} seconds...")
                time.sleep(args['delay'])

if __name__ == "__main__":
    main()
