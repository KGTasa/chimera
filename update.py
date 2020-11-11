import alembic.config
alembicArgs = ['--raiseerr', 'upgrade', 'head']
alembic.config.main(argv=alembicArgs)