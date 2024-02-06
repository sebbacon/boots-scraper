# Boots scraper

What it does:

* Iterate over store ids 1-7000, looking for stock levels of the specified VMPs.
* For stores that aren't found, record these in `output/stores_notfound.txt`
* Write the stock as JSON to per-VMP files.
* Combine these files into a single CSV.
* When run via Github actions, write the result back to the repo.


It takes about 15 mins to scrape one VMP.
Each job in a workflow can run for 6 hours.
So without modification, you can reliably track up to ~18 VMPs.

The master data is recorded at `outputs/stock_levels_all.csv`; 
for convenience, heat maps showing low stock by PCN are also generated
as png files in `outputs/`, named for the VMP.

