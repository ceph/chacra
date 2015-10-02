## TODO ##
# The create_repo task in __init__ should move here. However, there is
# a problem with circular imports, because this file would need to do
#   from chacra.async import app
# And then in __init__ it would need to do:
#   from chacra.async.rpm import create_repo
# We are required to do this because Celery needs things imported where it
# is running from and not sure how to go around the problem.
# This needs to be fixed/investigated.
