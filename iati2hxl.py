﻿#!/usr/bin/python
"""Convert XML-formatted IATI activity reports to CSV-formatted HXL 3W"""

import csv, requests, sys, xml.sax

if sys.version_info < (3,):
    raise Exception("Python 3+ required")

class IATI2HXL(xml.sax.handler.ContentHandler):
    """SAX event handler to convert an IATI activity report to CSV-formatted HXL 3W"""

    OUTPUT_SPEC = [
        ['IATI id', '#activity+id+v_iati_activities', 1],
        ['Last updated', '#date+updated', 1],
        ['Activity status', '#status', 1],
        ['Reporting org', '#org+name+reporting', 1],
        ['Participating org', '#org+name+participating', 3],
        ['Activity', '#activity+name', 1],
        ['DAC sector', '#sector+name', 3],
        ['Country code', '#country+code+recipient', 3],
        ['Planned start date', '#date+planned+start', 1],
        ['Actual start date', '#date+actual+start', 1],
        ['Planned end date', '#date+planned+end', 1],
        ['Actual end date', '#date+actual+end', 1],
    ]
    """Specification for what data should appear in the CSV"""

    STATUS_CODES = {
        '1': 'Pipeline/Identification',
        '2': 'Implementation',
        '3': 'Completion',
        '4': 'Post-completion',
        '5': 'Cancelled',
        '6': 'Suspended'
    }
    """Lookup table for IATI status codes"""

    DAC_SECTOR_CODES = {
        "110": "Education",
        "111": "Education, Level Unspecified",
        "112": "Basic Education",
        "113": "Secondary Education",
        "114": "Post-Secondary Education",
        "120": "Health",
        "121": "Health, General",
        "122": "Basic Health",
        "130": "Population Policies/Programmes & Reproductive Health",
        "140": "Water Supply & Sanitation",
        "150": "Government & Civil Society",
        "151": "Government & Civil Society-general",
        "152": "Conflict, Peace & Security",
        "160": "Other Social Infrastructure & Services",
        "210": "Transport & Storage",
        "220": "Communications",
        "230": "Energy",
        "231": "Energy Policy",
        "232": "Energy generation, renewable sources",
        "233": "Energy generation, non-renewable sources",
        "234": "Hybrid energy plants",
        "235": "Nuclear energy plants",
        "236": "Energy distribution",
        "240": "Banking & Financial Services",
        "250": "Business & Other Services",
        "310": "Agriculture, Forestry, Fishing",
        "311": "Agriculture",
        "312": "Forestry",
        "313": "Fishing",
        "320": "Industry, Mining, Construction",
        "321": "Industry",
        "322": "Mineral Resources & Mining",
        "323": "Construction",
        "331": "Trade Policies & Regulations",
        "332": "Tourism",
        "410": "General Environment Protection",
        "430": "Other Multisector",
        "510": "General Budget Support",
        "520": "Developmental Food Aid/Food Security Assistance",
        "530": "Other Commodity Assistance",
        "600": "Action Relating to Debt",
        "720": "Emergency Response",
        "730": "Reconstruction Relief & Rehabilitation",
        "740": "Disaster Prevention & Preparedness",
        "910": "Administrative Costs of Donors",
        "930": "Refugees in Donor Countries",
        "998": "Unallocated / Unspecified"
    }
    """OECD DAC high-level sector codes"""

    def __init__ (self, output_stream=None):
        """Create a new SAX event handler for IATI->CSV conversion.
        @param output_stream: if provided, use this as the CSV output stream (defaults to sys.stdout)
        """
        super().__init__()

        self.element_stack = []
        self.activity = {}
        self.content = ''
        self.csv_output = csv.writer(output_stream if output_stream else sys.stdout)

    def startElement(self, name, atts):
        """Beginning of a nested XML element"""
        super().startElement(name, atts)

        # Trigger actions based on the element name
        if name == 'iati-activities':
            self.write_headers()
            self.write_hashtags()
        elif name == 'iati-activity':
            self.activity = {}
            self.add_prop('#date+updated', atts.get('last-updated-datetime')[:10])
        elif name == 'reporting-org':
            self.add_prop('#org+code+reporting', atts.get('ref'))
        elif name == 'participating-org':
            self.add_prop('#org+code+participating', atts.get('ref'))
        elif name == 'recipient-country':
            self.add_prop('#country+code+recipient', atts.get('code'))
        elif name == 'sector':
            code = atts.get('code')
            if code:
                sector = self.DAC_SECTOR_CODES.get(code[:3])
                self.add_prop('#sector+name', sector)
                self.add_prop('#sector+code+v_iati_sectors', code)
        elif name == 'activity-date':
            date = atts.get('iso-date')
            type = atts.get('type')
            if type == '1':
                self.add_prop('#date+planned+start', date)
            elif type == '2':
                self.add_prop('#date+actual+start', date)
            elif type == '3':
                self.add_prop('#date+planned+end', date)
            elif type == '4':
                self.add_prop('#date+actual+end', date)
        elif name == 'activity-status':
            if self.STATUS_CODES.get(atts.get('code')):
                self.add_prop('#status', self.STATUS_CODES[atts['code']])
            
        self.element_stack.append(name)
        self.content = ''

    def endElement(self, name):
        """End of a nested XML element"""
        super().endElement(name)
        
        self.element_stack.pop()

        # Trigger actions based on the element name
        if name == 'iati-activity':
            self.write_data()
        elif name == 'iati-identifier':
            self.add_prop('#activity+id+v_iati_activities', self.content)
        elif name == 'title':
            self.add_prop('#activity+name', self.content)
        elif name == 'narrative':
            if self.has_parent('reporting-org'):
                self.add_prop('#org+name+reporting', self.content)
            elif self.has_parent('participating-org'):
                self.add_prop('#org+name+participating', self.content)

    def characters(self, content):
        """Any chunk of character data (may not be complete)"""
        super().characters(content)

        # Add to the current text content (will be used by endElement)
        self.content += content

    def add_prop(self, hashtag, value):
        """Add a property to the current row (supports multiple values)"""
        if not self.activity.get(hashtag):
            self.activity[hashtag] = []
        self.activity[hashtag].append(value)

    def has_parent(self, name):
        """Check for a specific parent element"""
        return (self.element_stack[-1] == name)

    def write_headers(self):
        """Write the CSV header row"""
        row = []
        for spec in self.OUTPUT_SPEC:
            for i in range(0, spec[2]):
                row.append(spec[0])
        self.csv_output.writerow(row)

    def write_hashtags(self):
        """Write the CSV hashtag row"""
        row = []
        for spec in self.OUTPUT_SPEC:
            for i in range(0, spec[2]):
                row.append(spec[1])
        self.csv_output.writerow(row)

    def write_data(self):
        """Write the current activity as a CSV data row"""
        row = []
        for spec in self.OUTPUT_SPEC:
            values = self.activity.get(spec[1])
            for i in range(0, spec[2]):
                if values and len(values) > i and values[i]:
                    row.append(values[i])
                else:
                    row.append('')
        self.csv_output.writerow(row)


# If run from the command line
if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("Usage: {} URL ...".format(sys.argv[0]))
    for source in sys.argv[1:]:
        handler = IATI2HXL()
        with requests.get(source, stream=True).raw as input:
            xml.sax.parse(input, handler)
