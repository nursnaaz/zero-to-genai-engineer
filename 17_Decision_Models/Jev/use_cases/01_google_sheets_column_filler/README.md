# 01 Put Jev in Google Sheets

**Easy** | shapes used: `choice`

Type a column header plus allowed options; Jev fills every row. Because it can only pick from your list it can never invent a category.

## Run it

```bash
cd 01_google_sheets_column_filler
python3 fill_column.py
```

## Data

`data/expenses.csv` - 30 synthetic UAE/UK expense rows (merchant, amount, note).

## How it is tested

Asserts every filled value is inside the allowed option list.

## Result when I ran it

30/30 rows categorised, all inside the allowed set. Ambiguous row (Dubai Mall Parking, note 'parking while shopping') correctly surfaced at 0.54 confidence.

## Worth knowing

Also ships `Code.gs`, a real Google Apps Script add-on with a Jev menu that shades low-confidence cells yellow.

## Google Sheets add-on

`Code.gs` is a real Apps Script add-on. Extensions > Apps Script, paste it, then add `JEV_KEY` under Project Settings > Script Properties. Reload the sheet and use the Jev menu.

← [all use cases](../README.md)
