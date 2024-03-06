# Closed-loop Teaching Study

## Running the study locally
- Install the following packages, preferably in an isolated environment like conda. If you get an error, try installing the specific version listed: 

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
* In `simple_game_test`, run the study with `python -m flask run`
* The main study code lives in `simple_game_test/app/routes.py`, which you can modify e.g. to change the experimental conditions (called `loop_conditions`).
* The algorithms for maintaining a running model of the human's beliefs (in a particle filter), determining the next demonstration or test to provide, etc, live in `simple_game_test/app/augmented_taxi/policy_summarization/*`. 

## Data analysis

* Run `analysis/data_analysis.py`. The data collected from the user study can found in `analysis/dfs_f23_processed.pickle`.

## Recreating the database (app.db)

- Comment out bottom half of `simple_game_test/app/__init__.py` 
- Create the database using

```
flask db init
flask db migrate 
flask db upgrade
```
- Uncomment the bottom half of `simple_game_test/app/__init__.py` before running the study again. 

When making changes to the structure of the database (e.g. adding a new column), purge the previous one with the following commands before recreating the database
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
