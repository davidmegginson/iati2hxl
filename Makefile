PYTHON=$(HOME)/.virtualenvs/iati/bin/python
DATA="http://iati.dfid.gov.uk/iati_files/Country/DFID-Afghanistan-AF.xml"

all:
	$(PYTHON) iati2hxl.py $(DATA)

