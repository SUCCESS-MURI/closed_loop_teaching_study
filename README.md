# Closed Loop Teaching

## Installation
- Install VS Code
- Do the set-up instructions from https://code.visualstudio.com/docs/python/tutorial-flask starting with the Prerequisites and Create Project Environment sections
- Select Interpretor to the `venv` and `Ctrl + Shift +` ` to open console within the env
- Install the following packages (if you get an error, try installing the following versions: 
```
- python 3.9
- flask 2.0.3
- flask-wtf 1.0.1
- flask-login 0.6.2
- flask-sqlalchemy 2.5.1
- flask-migrate 4.0.0
- sqlalchemy 1.4.27
- (the following package versions could be more flexible) 
- numpy 1.24.3
- scipy 1.10.1 
- matplotlib 3.7.1 
- pandas 2.0.1
- pingouin 0.5.3
- email-validator 2.0.0.post2
```
- Comment out bottom half of `__init__.py`
- Create the database using
```
flask db init
flask db migrate 
flask db upgrade
```
- Uncomment the bottom half of `__init__.py`
- Run the app with `python -m flask run`

When making changes to the structure of the database (e.g. adding a new column), purge the previous one with the following commands
```angular2html
rm -r app.db
rm -rf migrations
```

## Database Access
Opening the database in sqlite3:

```sqlite3 app.db```

Some helpful commands while in splite3:

```
# List all tables:
.tables

# List data in a table:
SELECT * FROM <table_name>;

# List all column names and data types in a table:
PRAGMA table_info(<table_name>);

# Export table to a .csv:
.mode csv
.output <filename>.csv
SELECT * FROM <table_name>;
.output stdout
```

To exit from sqlite, press Ctrl+D

## Useful Links
- https://stackoverflow.com/questions/56199111/visual-studio-code-cmd-error-cannot-be-loaded-because-running-scripts-is-disabl
- https://github.com/bevacqua/dragula/
- Alt + Shift + F is auto-indent
- Flask Login with Database https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
- DB to CSV with https://www.rebasedata.com/convert-sqlite-to-csv-online