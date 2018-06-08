#!/usr/bin/python
"""Convert XML-formatted IATI activity reports to HXL 3W
If run from the command line, produce CSV output to STDOUT
The main entry point is genhxl()
"""

import csv, requests, sys

from xml.etree import ElementTree

from .mappings import STATUS_CODES, DAC_SECTOR_CODES, ISO_COUNTRY_NAMES, ISO_COUNTRY_CODES

if sys.version_info < (3,):
    raise Exception("Python 3+ required")


# Note that xml.etree supports only a limit XPath subset, so we need to specify attribute values separately

OUTPUT_SPEC = (
    # element, attribute, output occurrences, output header, output hashtag, mapping, mapping prefix len
    ('./iati-identifier', '', 1, 'IATI id', '#activity+id+v_iati_activities', None, None),
    ('.', 'last-updated-datetime', 1, 'Last updated', '#date+updated', None, None),
    ('./activity-status', 'code', 1, 'Activity status', '#status', STATUS_CODES, None),
    ('./reporting-org/narrative', '', 1, 'Reporting org', '#org+name+reporting', None, None),
    ('./participating-org/narrative', '', 3, 'Participating org', '#org+name+participating', None, None),
    ('./title/narrative', '', 1, 'Activity', '#activity+name', None, None),
    ('./sector', 'code', 3, 'DAC sector', '#sector+name', DAC_SECTOR_CODES, 3),
    ('./recipient-country', 'code', 5, 'Country name', '#country+name+recipient+i_en', ISO_COUNTRY_NAMES, None),
    ('./recipient-country', 'code', 5, 'Country code', '#country+code+recipient', ISO_COUNTRY_CODES, None),
    ('./activity-date[@type="1"]', 'iso-date', 1, 'Planned start date', '#date+planned+start', None, None),
    ('./activity-date[@type="2"]', 'iso-date', 1, 'Actual start date', '#date+actual+start', None, None),
    ('./activity-date[@type="3"]', 'iso-date', 1, 'Planned end date', '#date+planned+end', None, None),
    ('./activity-date[@type="4"]', 'iso-date', 1, 'Actual end date', '#date+actual+end', None, None),
)
"""Specification for what data should appear in the HXL output"""


def make_headers():
    """Create the CSV header row
    @returns: a list representing the header row
    """
    row = []
    for spec in OUTPUT_SPEC:
        for i in range(0, spec[2]):
            row.append(spec[0])
    return row

def make_hashtags():
    """Create the CSV hashtag row
    @returns: a list representing the HXL hashtag row
    """
    row = []
    for spec in OUTPUT_SPEC:
        for i in range(0, spec[2]):
            row.append(spec[1].replace('+', ' +'))
    return row

def make_row(activity_element):
    """Create a row for an aid activity
    @param activity_element: the iati-activity element tree
    @returns: a list representing a row of HXL data
    """
    row = []
    for xpath, attname, occurrences, header, tagspec, mapping, prefix_length in OUTPUT_SPEC:
        elements = activity_element.findall(xpath)
        for n in range(0, occurrences):
            value = ''
            if n < len(elements):
                element = elements[n]
                if attname:
                    value = element.attrib.get(attname, '')
                else:
                    value = element.text
            if mapping:
                if prefix_length is not None:
                    value = value[:prefix_length]
                value = mapping.get(value, value)
            if value is None:
                value = ''
            row.append(value)
    return row
    

def genhxl(input):
    """HXL generator from IATI data
    From any file-like object, read an XML-encoded list of IATI activities, and yield
    a tabular HXL dataset, one row at a time. Each row is a Python list of strings.
    @param input: a file-like object (such as an open file)
    @returns: yields lists of strings, one for each row.
    """

    # Start with the frontmatter
    yield make_headers()
    yield make_hashtags()

    # Create a row for each iati-activity element
    for event, element in ElementTree.iterparse(input):
        if element.tag == ('iati-activity'):
            row = make_row(element)
            element.clear()
            yield(row)


# If run from the command line
if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("Usage: {} URL ...".format(sys.argv[0]))

    output = csv.writer(sys.stdout)
    
    for source in sys.argv[1:]:
        with requests.get(source, stream=True) as response:
            response.raw.decode_content = True
            for row in genhxl(response.raw):
                output.writerow(row)
