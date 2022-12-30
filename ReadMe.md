## ReadMe

We use Selenium to scrape data from embedded PDFs that are designed to be difficult to scrape.

Our target website is https://www.allcryptowhitepapers.com/whitepaper-overview/ and it uses pdf-embedder (https://github.com/wp-plugins/pdf-embedder).

Our strategy consists of saving the canvases and merging them to a PDF.

We also scrape weblinks from a table.

Instructions:
Run ```pip install -r requirements.txt``` to install dependencies.

The scraper automates approximately 70% of the proces and will take 4 days to run in total.
