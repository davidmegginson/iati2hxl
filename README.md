% iati2hxl - convert IATI activity lists into to a simple HXL 3W-like representation

## Setup

        pip install iati2xml
        
or (at the root of the source code directory)

        python3 setup.py

## Usage

### Command line

        $ python -m iati2hxl.generator IATI_URL [IATI_URL ...]
        
### Python code

        import csv, iati2hxl.genhxl, sys
        
        with open('iati-file.xml', 'r') as input:
            output = csv.writer(sys.stdout)
            for row in iati2hxl.genhxl(input):
                output.writerow(row)

## Notes

This is designed to be efficient with large datasets: it streams
through the XML one iati-activity at a time, rather than reading it
all into memory at once.

## License

This code is released into the public domain.
