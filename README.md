# WinObjectIdParser
ObjectID Parsers and Tools

## Install

#### pip install
`pip install git+https://github.com/forensicmatt/WinObjectIdParser`

#### setup.py
`setup.py install`

## Usage
```
usage: objid_indx_parser.py [-h] -s SOURCE [--no_recover] [-o OUTPUT_TEMPLATE]
                            [--debug {ERROR,WARN,INFO,DEBUG}]

Parse the $O Index. The file can be found at \$Extend\$ObjId:$O.
    version: 0.0.1


optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The $O Index or a logical volume (logical volume:
                        \\.\C:).
  --no_recover          Do Not Recover Object Entries.
  -o OUTPUT_TEMPLATE, --output_template OUTPUT_TEMPLATE
                        Output template format.
  --debug {ERROR,WARN,INFO,DEBUG}
                        Debug level [default=ERROR]
```

## Output Templates
The output template is just a string that is used with Python's format function.

### Example:
#### JSON Record:
By default the output is in JSONL format. Here is a raw json record (that has been indented for easier
viewing).
```json
{
	"offset": 166016,
	"recovered": false,
	"flags": 0,
	"object_id": {
		"uuid": "b9f9ecdd-5d56-11e7-a978-40e23013d7af",
		"hex": "ddecf9b9565de711a97840e23013d7af",
		"timestamp": "2017-06-30 05:41:12.682415700",
		"timestamp_uint64": 137180940726824157,
		"version": 1,
		"variant": 2,
		"sequence": 10616,
		"mac": "40e23013d7af"
	},
	"mft_reference": {
		"reference": 844424930281828,
		"entry": 149860,
		"sequence": 3
	},
	"birth_volume": {
		"uuid": "82097100-06c3-44b1-b734-0a726fd96457",
		"hex": "00710982c306b144b7340a726fd96457",
		"timestamp": "2654-01-19 20:32:59.954406400",
		"timestamp_uint64": 338058883799544064,
		"version": 4,
		"variant": 2,
		"sequence": 14132,
		"mac": "0a726fd96457"
	},
	"birth_object": {
		"uuid": "b9f9ecdd-5d56-11e7-a978-40e23013d7af",
		"hex": "ddecf9b9565de711a97840e23013d7af",
		"timestamp": "2017-06-30 05:41:12.682415700",
		"timestamp_uint64": 137180940726824157,
		"version": 1,
		"variant": 2,
		"sequence": 10616,
		"mac": "40e23013d7af"
	},
	"birth_domain": {
		"uuid": "00000000-0000-0000-0000-000000000000",
		"hex": "00000000000000000000000000000000",
		"timestamp": "1582-10-15 00:00:00.000000000",
		"timestamp_uint64": 0,
		"version": 0,
		"variant": 0,
		"sequence": 0,
		"mac": "000000000000"
	}
}
```

#### Output Template
Lets say we want output to just display the mft entry, object id's timestamp, and the raw object id.
We could give an output template of the following: `{mft_reference[entry]},{object_id[timestamp]},{object_id[hex]}`

If we wanted to find the same record as the previous json output example we could then filter through
a grep like utility:

```
python .\objid_indx_parser.py -s \\.\C: -o "Recovered: {recovered},{mft_reference[entry]},{object_id[timestamp]},{object_id[hex]}" | rg ddecf9b9565de711a97840e23013d7af
```

If you run the tool with no output template, you get back the raw json. You can use that json output to
know which fields exist in the data.

#### Result
```
Recovered: False,149860,2017-06-30 05:41:12.682415700,ddecf9b9565de711a97840e23013d7af
```
