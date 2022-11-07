from ban_list_parser import ban_list_parser

from bs4 import BeautifulSoup

import requests
import re

import sys
import json

from pprint import pprint

class bans( ban_list_parser ):

    def __init__( self, config=None ):
        self.config_section = "aboutpage"
        self.ban_prefix = "about_undefined"
        self.config_section_list = "domains"

        if self.config_section in config:
            self.config = config
        else:
            print( "config.ini [about] is missing - fatal" )
            sys.exit()

        pprint( self.config[self.config_section][self.config_section_list] )

        try:
            self.domains = json.loads( self.config[self.config_section][self.config_section_list] )
        except Exception as e:
            print( "config file section prasers item '{}' does not parse as valid json, please fix - {}".format( self.config_section, e ) )
            sys.exit()

    def getbans(self):
        for domain in self.domains:
            page = requests.get( "https://{}/about/more".format( domain ) )
            print( page )
            soup = BeautifulSoup(page.content, 'html5lib')


            tables = soup.find_all( 'table' )

            bans = []

            for table in tables:
                ths = table.find_all('th')
                if all(
                        str(x) in [
                            "<th>Server</th>",
                            "<th>Reason</th>"
                            ]
                        for x in ths
                        ):
                    for tr in table.find_all('tr'):
                        if "<th>" in str( tr ):
                            continue
                        cols = tr.find_all('td')
                        cols = [ele.text.strip() for ele in cols]
                        bans.append( {
                                "domain": cols[0],
                                "reason": cols[1]
                                } )
            return bans

