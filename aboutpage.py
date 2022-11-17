#!/usr/bin/python3
# coding: UTF-8

"""Pulls down a set of bans and reasons for all systems with which we're
federated."""

import sys
import json
from pprint import pprint

import requests

from bs4 import BeautifulSoup
from BanListParser import BanListParser

from packaging import version

class Bans(BanListParser):
    """Pulls down a set of bans and reasons for all systems with which we're
    federated."""

    def __init__(self, config=None):
        self.config_section = "aboutpage"
        self.ban_prefix = "about_undefined"
        self.config_section_list = "domains"

        if self.config_section in config:
            self.config = config
        else:
            print("config.ini [about] is missing — fatal")
            # rjh -- should fail with an error condition, not an EXIT_SUCCESS.
            sys.exit(-1)

        # rjh -- let's make the next few lines a little more legible.
        # jah -- thingy is the technical term, please also see whatsit, and stuff
        thingy = self.config[self.config_section][self.config_section_list]
        #pprint(thingy)
        try:
            self.domains = json.loads(thingy)
            #print( "Loaded domains list..." )
            #pprint( self.domains )
        except Exception as exc:
            print(f"config file section parsers item '{self.config_section}'" +
                  f" doesn't parse as valid json, please fix - {exc}")
            # rjh -- again, this is not an EXIT_SUCCESS condition
            sys.exit(-1)

    def getVersion(self, server):
        # /api/v1/instance - will get us a json of what the instance is
        # including the current running version, so that should help
        # figure out if we should parse the page, or parse the json.

        ver = "0.0.0"

        page = requests.get( "http://{}/api/v1/instance".format( server) ).content
        #pprint( page )
        try:
            instance_data = json.loads( page )
        except Exception as e:
            exception_str = "Received invalid json from remote - {} | {}".format( e, page )
            print( exception_str )
            raise Exception( exception_str )
        #print( "Ok got a good instance!" )

        #pprint( instance_data )

        if "version" in instance_data:
            ver = instance_data['version']
        else:
            exception_str = "No version returned - {}".format( instance_data )
            print( exception_str )
            raise Exception( exception_str )

        #print( "Found version: {}".format( ver ) )
        return ver

    def getV3(self, domain):
        bans = []

        url = f"https://{domain}/about/more"

        try:
            page = requests.get( url )
        except Exception as e:
            exception_str = "Problem getting {} - {}".format( url, e )
            print( exception_str )
            raise( exception_str )

        tables = BeautifulSoup(page.content, 'html5lib').find_all('table')
        accept_set = set(["<th>Server</th>", "<th>Reason</th>"])

        for table in tables:
            table_headers = [str(X) for X in table.find_all('th')]
            if all(X in accept_set for X in table_headers):
                for tablerow in table.find_all('tr'):
                    if "<th>" in str(tablerow):
                        continue
                    cols = tablerow.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    bans.append({
                        "domain": cols[0],
                        "reason": "{} (automated-aboutpage): {}".format( domain, cols[1] )
                    })
        return bans

    def getV4(self, domain):
        bans = []

        url = f"https://{domain}/api/v1/instance/domain_blocks"

        try:
            page = requests.get( url ).content.decode("utf-8")
        except Exception as e:
            exception_str = "Problem getting {} - {}".format( url, e )
            print( exception_str )
            raise( exception_str )

        #pprint( page )

        try:
            bans_json = json.loads( page )
        except Exception as e:
            exception_str = "Received invalid json from remote - {} | {}".format( e, page )
            print( exception_str )
            raise Exception( exception_str )

        #pprint( bans_json )
        for ban in bans_json:
            reason = ban['comment']
            if reason is None:
                reason = ""
            bans.append({
                "domain": ban['domain'],
                "reason": ban['comment']
                })
        return bans

    def getbans(self):
        bans = []

        for domain in self.domains:
            print( "aboutpage - {}".format( domain ) )
            # on v3 it's /about/home to snag the list, table in html
            # on v4 it's /api/v1/instance/domain_blocks, json response via api
            try:
                ver = self.getVersion( domain )
            except Exception as e:
                print( "Caught an exception from getVersions() - skipping {} | {}".format( domain, e )  )
                continue

            if version.parse( ver ) >= version.parse( "3.0.0" ) and version.parse( ver ) < version.parse( "4.0.0" ):
                bans += self.getV3( domain )
            elif version.parse( ver ) >= version.parse( "4.0.0" ):
                bans += self.getV4( domain )
            else:
                print( "Unknown version from {}: {} - skipping ".format( domain, ver ) )
                continue

        return bans
