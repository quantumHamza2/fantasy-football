# Fantasy Football Manager

Python learning project with a Flask web interface, MySQL storage and a command-line fantasy-team simulator. The web interface provides registration, login, players and team views; fantasy-team management and match simulation live in the CLI.

## Local setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r fantasy_football_app/requirements.txt
```

Start MySQL separately. Export `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DB` in your terminal; the default database name is `fantasy_football_db`. Use a dedicated development database. Set `FLASK_SECRET_KEY` to a long random value so login sessions survive restarts.

For a **new** database, run `python fantasy_football_app/logic/fantasy_logic.py` and choose the initialization option. Initialization creates sample Teams/Players and the web users table. It refuses an existing database rather than deleting data. Existing databases need a deliberate migration.

Run `python fantasy_football_app/app.py`, then open http://localhost:5001. Debug mode is off unless `FLASK_DEBUG=1`. Without a configured secret, a temporary random key is generated per process for local exploration.

## Checks and limits

`python -m unittest discover -s tests` checks public page rendering and login redirects without a database. Live MySQL operations still need integration testing. This local prototype needs CSRF protection, login throttling and deployment configuration before public use.

The CLI simulation generates sample performance; it does not connect to a live sports feed.
