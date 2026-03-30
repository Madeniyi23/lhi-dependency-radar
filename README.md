# LHI Dependency Radar

**See what breaks before it breaks.**

LHI Dependency Radar is a Python script for ArcGIS Online and ArcGIS Enterprise that helps GIS teams find where a hosted feature layer is being used across common item types before making risky changes.

## Why it exists

A common ArcGIS Online bottleneck is dependency visibility. Teams want to know:
- What maps or apps use this hosted feature layer?
- Can I safely change or retire this item?
- What might break if I update the schema or swap a service?

This tool is a lightweight first pass at solving that problem.

## Current version

This repo contains **v1.2**, which:
- prompts for org URL, username, password, and target feature layer item ID
- scans common dependency item types
- checks for matches using:
  - item ID
  - service URL
  - layer URLs
  - table URLs
- exports:
  - a detailed dependency CSV
  - a one-row summary CSV

## Scanned item types

- Web Map
- Dashboard
- Web Experience
- Web Mapping Application
- StoryMap

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/main.py
```

## Outputs

The script writes two CSV files into the folder where you run it:

- `dependency_report_v1_2.csv`
- `dependency_summary_v1_2.csv`

## Example workflow

1. Run the script.
2. Enter your ArcGIS Online or Enterprise org URL.
3. Enter your username and password.
4. Enter the hosted feature layer item ID you want to inspect.
5. Review the detailed and summary CSV outputs.

## Notes

This is a practical MVP, not a full dependency engine. It relies on scanning item data returned by ArcGIS and matching target strings within that data. That means:
- it can miss some dependency patterns
- it is best used as a first-pass discovery tool
- it may be extended later with field-level checks, risk scoring, and governance reporting

## Roadmap ideas

- owner filtering
- item type filtering
- field-level dependency checks
- confidence scoring improvements
- cleanup advisor mode
- hosted view governance mode

## License

MIT
