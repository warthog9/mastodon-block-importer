from mastodon import Mastodon
import configparser
import sys

from requests import Session
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from pprint import pprint

bans = []

config = configparser.ConfigParser()

config.read('config.ini')

pprint( config['parsers']['list'] )

try:
    parser_list = json.loads( config['parsers']['list'] )
except:
    print( "config file section prasers item 'list' does not parse as valid json, please fix" )
    sys.exit()

for x in parser_list:
    print("Parser: {}".format( x ) )
    module = __import__( x )
    getfrom = module.bans( config )
    bans.extend( getfrom.getbans() )

pprint( bans )

sys.exit()

dbans = {}
# ok first things first lets turn these lists into a combined dictionary
for ban in bans:
    #print("New ban:")
    #pprint( ban )
    domain = ban['domain']
    reason = ban['reason']

    if domain in dbans:
        dbans[domain]['reason'].append( reason )
    else:
        dbans[domain] = {}
        dbans[domain]['reason'] = []
        dbans[domain]['reason'].append( reason )

    print( dbans[domain]['reason'] )

pprint( dbans )

if "oauth" not in config['mastodon'] or config['mastodon']['oauth'] == "":
    Mastodon.create_app(
        'hulk-banner',
        scopes=['read', 'write'],
        api_base_url = config['base']['site'],
        to_file = 'pytooter_clientcred.secret'
    )
    print("Please add client_id to the config.ini")
    sys.exit()


if 'ignore_cert' in config['mastodon']:
    req_session = Session()
    if config['mastodon']['ignore_cert'] == "True":
        req_session.verify = False
    else:
        req_session.verify = True

else:
    req_session = None

mastodon = Mastodon(
    config['mastodon']['client_id'],
    config['mastodon']['client_secret'],
    config['mastodon']['oauth'],
    api_base_url = config['base']['site'],
    mastodon_version = "3.5.3",
    session = req_session
)

print( mastodon.domain_blocks() )

pg_conn = psycopg2.connect(
    database = config['postgres']['database'],
    user = config['postgres']['user'],
    password = config['postgres']['password'],
    host = config['postgres']['host'],
    port = config['postgres']['port']
    )

pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

pg_cur.execute("SELECT * from domain_blocks")
rows = pg_cur.fetchall()
for row in rows:
   # current schema
   pprint( row )

sql_insert_domain_block = """INSERT INTO domain_blocks ( domain, created_at, updated_at, severity, reject_media, reject_reports, private_comment, obfuscate ) VALUES ( %s, now(), now(), %s, %s, %s, %s, %s )"""

for domain in dbans:

    if not any( d['domain'] == domain for d in rows ):
        # ban currently doesn't exist
        print( "Missing ban for {}".format( domain ) )
        print( "    Reason: {}".format( "\n".join( dbans[domain]['reason'] ) ) )

        pg_cur.execute(
                sql_insert_domain_block,
                (
                    domain, # domain
                    # created_at is done by now(),
                    # updated_at is done by now(),
                    1,
                    'f', # reject_media
                    'f', # reject_reports
                    "\n".join( dbans[domain]['reason'] ), # private_comment,
                    'f' # obfuscate,
                    )
                )

pg_conn.commit()
