import csv, requests, sys, xml.sax

class IATIHandler(xml.sax.handler.ContentHandler):

    OUTPUT_SPEC = [
        ['IATI id', '#activity+id+v_iati_activities', 1],
        ['Last updated', '#date+updated', 1],
        ['Activity status', '#status', 1],
        ['Reporting org', '#org+name+reporting', 1],
        ['Participating org', '#org+name+participating', 3],
        ['Activity', '#activity+name', 1],
        ['Sector code', '#sector+code+v_iati_sectors', 3],
        ['Country code', '#country+code+recipient', 3],
        ['Planned start date', '#date+planned+start', 1],
        ['Actual start date', '#date+actual+start', 1],
        ['Planned end date', '#date+planned+end', 1],
        ['Actual end date', '#date+actual+end', 1],
    ]

    STATUS_TYPES = {
        '1': 'Pipeline/Identification',
        '2': 'Implementation',
        '3': 'Completion',
        '4': 'Post-completion',
        '5': 'Cancelled',
        '6': 'Suspended'
    }

    def __init__ (self, output_stream=None):
        xml.sax.handler.ContentHandler.__init__(self)
        self.element_stack = []
        self.activity = {}
        self.content = ''
        self.csv_output = csv.writer(output_stream if output_stream else sys.stdout)

    def startElement(self, name, atts):

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
            self.add_prop('#sector+code+v_iati_sectors', atts.get('code'))
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
            if self.STATUS_TYPES.get(atts.get('code')):
                self.add_prop('#status', self.STATUS_TYPES[atts['code']])
            
        self.element_stack.append(name)
        self.content = ''

    def endElement(self, name):
        self.element_stack.pop()

        if name == 'iati-activity':
            self.write_row()
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
        self.content += content

    def add_prop(self, hashtag, value):
        if not self.activity.get(hashtag):
            self.activity[hashtag] = []
        self.activity[hashtag].append(value)

    def has_parent(self, name):
        return (self.element_stack[-1] == name)

    def has_ancestor(self, name):
        return (name in self.element_stack)

    def write_headers(self):
        row = []
        for spec in self.OUTPUT_SPEC:
            for i in range(0, spec[2]):
                row.append(spec[0])
        self.csv_output.writerow(row)

    def write_hashtags(self):
        row = []
        for spec in self.OUTPUT_SPEC:
            for i in range(0, spec[2]):
                row.append(spec[1])
        self.csv_output.writerow(row)

    def write_row(self):
        row = []
        for spec in self.OUTPUT_SPEC:
            values = self.activity.get(spec[1])
            for i in range(0, spec[2]):
                if values and len(values) > i and values[i]:
                    row.append(values[i])
                else:
                    row.append('')
        self.csv_output.writerow(row)

for source in sys.argv[1:]:
    handler = IATIHandler()
    with requests.get(source, stream=True).raw as input:
        xml.sax.parse(input, handler)
