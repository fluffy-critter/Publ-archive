# Dreamcatcher
Quickstart site for Python+Flask+Peewee on Dreamhost/Passenger/etc.

## What this is

A simple way to build a site using my current favorite development environment in a way that is easy to develop locally and deploy onto Passenger-enabled hosting sites (in particular, Dreamhost).

It provides the following:

* `virtualenv` sandbox with easy setup
* a `passenger_wsgi.py` script that is Dreamhost-compatible (and probably works on other Passenger-based hosting setups)
* a `run.py` script that behaves the same way as Passenger
* a starter [Flask](http://flask.pocoo.org/) site which does pretty much nothing
* a basic [Peewee](http://peewee.readthedocs.org/) base schema with a not-terrible schema migration mechanism
* a simple configuration mechanism (`config.py`) which defaults to an SQLite database and has a commented-out MySQL configuration that is easy to switch to

## How to use it

### Development

These instructions assume you're on a UNIXy system (Linux, OSX, Windows + Git bash shell, etc.) and using git for your own version control. You could probably do this in other environments (like WIndows CMD.EXE) but why would you want to?

1. Create a git repo in your usual way
2. `git remote add dreamcatcher https://github.com/plaidfluff/dreamcatcher.git`
3. `git pull dreamcatcher master`
4. `cp config.py.dist config.py`
5. `./setup.sh`

You now have a virtualenv container. You can use `. env/bin/activate` to run within that container, or you can just do e.g. `env/bin/pip` et al to run the individual tools (for example, `env/bin/pip install some-random-package` or `env/bin/pip freeze > requirements.txt` or whatever).

You can also use `git pull dreamcatcher master` to pull updates from me. You'll probably need to fix any merge conflicts that occur in `requirements.txt`.

If you want to submit a patch against this repo, the easiest way is to fork the repo on Github, make your changes in that repo, and submit a pull request to me. (Advanced users can also set their `dreamcatcher` remote to their own Github fork etc.)

In any case, your site stuff goes into `dc_site/` and your common files (schemata, utilities, etc.) go into `dc_common/`. I like to use `dc_common/` for storing things like data formatters and so on. You can also rename these directories if you don't mind having to fix every single import in every single file and lose the ability to pull from upstream.

### Running locally

Just run `./run.py` which will spin up your Flask app on `localhost:5000`

### Running on Dreamhost

For the initial deployment, you'd want to do something like:

1. `git clone your-site-repository whatever.domain.com`
2. Set up the domain on Dreamhost to be fully-hosted, with the web directory at `whatever.domain.com/public`, and with Passenger support enabled
3. Set up your database, copy `config.py.dist` to `config.py`, and configure `config.py` to use your database
4. run `./setup.sh` from your site directory

And now your site should be working. Whenever you pull a new version for deployment, remember to run `./setup.sh` which tells Passenger to restart your servelet and then runs the schema migration.

Also, note that it's quite possible (and sometimes deirable) to just use the default SQLite configuration even in production, *but* be warned that at least in the case of Dreamhost, this can cause things to fail weirdly if you're trying to access the database from outside your servelet (such as doing a database-JSON import/export) because SQLite's locking behavior doesn't work too well on NFS.

## Caveats

* Flask usually puts static content into the `static/` directory. This instead puts it into `public/` (because that's where Dreamhost wants it). There is a dumb thunk to make it behave the same in `run.py` vs. Dreamhost deployment. Note that if there is a name conflict between something inside `public/` and a mapped route, the route takes precedence in `run.py` but the static content takes precedence in Dreamhost.
* `%2F` doesn't work correctly in a request path. This is apparently a problem with WSGI and Flask in general, and not something specific to this setup. (Passenger itself actually would allow `%2F` to work, but you'd have to do your own URL decoding and it wouldn't work the same way from `./run.py` so I opted to just inherit the WSGI limitation.)
