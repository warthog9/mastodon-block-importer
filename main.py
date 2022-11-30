#!/usr/bin/python3
# coding: UTF-8

"""Launches the magic.  Not much happens here."""


import configparser
import sys
import json
from pprint import pprint
import psycopg2
from psycopg2.extras import RealDictCursor
import validators

from mastodon import Mastodon
from requests import Session

if __name__ == '__main__':
    _BANS = []
    _CONFIG = configparser.ConfigParser()
    _CONFIG.read('config.ini')
    _IMPORTED_FLAG = "imported:"

    pprint(_CONFIG['parsers']['list'])

    try:
        parser_list = json.loads(_CONFIG['parsers']['list'])
    except:
        print("config file section parsers item 'list' does not parse as valid json, please fix")
        sys.exit(-1)

    for parser in parser_list:
        print(f"Parser: {parser}")
        module = __import__(parser)
        getfrom = module.Bans(_CONFIG)
        _BANS.extend(getfrom.getbans())

    #pprint(_BANS)

    try:
        explicitly_allowed = json.loads( _CONFIG['allowed']['list'] )
    except Exception as e:
        print( "Config Error - allowed 'list' does not parse as valid json" )
        sys.exit(-1)

    d_BANS = {}
    # ok first things first lets turn these lists into a combined dictionary
    for ban in _BANS:
        #print("New ban:")
        #pprint( ban )
        domain = ban['domain']
        reason = ban['reason']

        if '*' in domain:
            print( "{} is obfuscated - useless to import".format( domain ) )
            continue

<<<<<<< Updated upstream
=======
        if not validators.domain( domain ):
            print( "'{}' domain not valid - moving on".format( domain ) )
            continue

>>>>>>> Stashed changes
        if reason is None:
            reason = ""

        if domain in explicitly_allowed:
            print( "{} found in remote block list, explicitly allowing by config".format( domain ) )
            continue
        elif not reason is None and reason.startswith( _IMPORTED_FLAG ):
            print( "{} was imported remotely, not adding to ours, need a first hand reference".format( domain ) )
            continue
        elif domain in d_BANS:
            d_BANS[domain]['reason'].append(reason)
        else:
            # new ban
            d_BANS[domain] = {}
            d_BANS[domain]['reason'] = []
            d_BANS[domain]['reason'].append(reason)

        #print(d_BANS[domain]['reason'])

    #pprint(d_BANS)

    # *CURRENTLY* this isn't useful, lets get the helpers sorted and come back to it
    #if "oauth" not in _CONFIG['mastodon'] or _CONFIG['mastodon']['oauth'] == "":
    #    Mastodon.create_app(
    #        'hulk-banner',
    #        scopes=['read', 'write'],
    #        api_base_url=_CONFIG['base']['site'],
    #        to_file='pytooter_clientcred.secret'
    #    )
    #    print("Please add client_id to the _CONFIG.ini")
    #    sys.exit()
    #
    #
    #if 'ignore_cert' in _CONFIG['mastodon']:
    #    req_session = Session()
    #    if _CONFIG['mastodon']['ignore_cert'] == "True":
    #        req_session.verify = False
    #    else:
    #        req_session.verify = True
    #
    #else:
    #    req_session = None
    #
    #mastodon = Mastodon(
    #    _CONFIG['mastodon']['client_id'],
    #    _CONFIG['mastodon']['client_secret'],
    #    _CONFIG['mastodon']['oauth'],
    #    api_base_url=_CONFIG['base']['site'],
    #    mastodon_version="3.5.3",
    #    session=req_session
    #)

    #print(mastodon.domain_blocks())

    pg_conn = psycopg2.connect(
        database=_CONFIG['postgres']['database'],
        user=_CONFIG['postgres']['user'],
        password=_CONFIG['postgres']['password'],
        host=_CONFIG['postgres']['host'],
        port=_CONFIG['postgres']['port']
    )

    pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

    pg_cur.execute("SELECT * from domain_blocks")
    rows = pg_cur.fetchall()
    #for row in rows:
    #    # current schema
    #    pprint(row)

    sql_insert_domain_block = """INSERT INTO domain_blocks ( domain, created_at, updated_at, severity, reject_media, reject_reports, private_comment, public_comment, obfuscate ) VALUES ( %s, now(), now(), %s, %s, %s, %s, %s, %s )"""
    sql_update_comment_domain_block = """UPDATE domain_blocks SET updated_at = now(),  private_comment = %s WHERE domain = %s"""

    for domain in d_BANS:
        if not any(d['domain'] == domain for d in rows):
            # ban currently doesn't exist
            print("Missing ban for {}".format(domain))
            print("    Reason: {}".format("\n".join(d_BANS[domain]['reason'])))

            pg_cur.execute(
                sql_insert_domain_block,
                (
                    domain,  # domain
                    # created_at is done by now(),
                    # updated_at is done by now(),
                    1,
                    'f',  # reject_media
                    'f',  # reject_reports
                    "\n".join(d_BANS[domain]['reason']),  # private_comment,
                    _IMPORTED_FLAG, # public_comment,
                    'f'  # obfuscate,
                )
            )
        else:
            # ok ban does exist, lets add some additional commentary

            dbRowIndex = next((index for (index, d) in enumerate(rows) if d["domain"] == domain), None)

            #pprint( dbRowIndex )

            dbRow = rows[ dbRowIndex ]

            #pprint( dbRow )
            
            updatedComment = dbRow['private_comment'].splitlines()

            updateComment = []
            [ updateComment.append(x) for x in updatedComment if x not in updateComment ]

            updatedComment = updateComment

            #pprint( updatedComment )
            
            # ok make sure we don't already have this reason in the comment
            for reason_line in d_BANS[domain]['reason']:
                if reason_line in updatedComment:
                    continue
                updatedComment.append( reason_line )

            if d_BANS[domain]['reason'][0] != "\n".join(updatedComment):
                #print("Updating ban with new reason: {}".format( "\n".join(updatedComment) ) )
                #print( ( d_BANS[domain]['reason'][0] != "\n".join(updatedComment) ) )
                #print( "old:" )
                #pprint( d_BANS[domain]['reason'] )
                #print( "new:" )
                #pprint( "\n".join(updatedComment) )
                #print( domain )

                try:
                    pg_cur.execute(
                        sql_update_comment_domain_block,
                        (
                            "\n".join(updatedComment),  # private_comment,
                            domain,  # domain
                        )
                    )
                except Exception as e:
                    print( "Well something went wrong updating {}".format( e ) )
                    sys.exit(-1)

                try:
                    pg_conn.commit()
                except Exception as e:
                    print( "Well something went wrong trying to commit the changes..." )
                    sys.exit(-1)

    pg_conn.commit()
