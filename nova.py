from BanListParser import BanListParser

import requests
import re

import sys

from pprint import pprint

class Bans( BanListParser ):

    def __init__( self, config=None ):
        self.config = config
        self.url = "https://raw.githubusercontent.com/hachyderm/hack/main/blocklist"

    def getbans(self):
        page = requests.get(self.url).content.splitlines()
        #pprint( page )

        bans = []
        for line in page:
            bans.append( {
                    "domain": line.decode("utf-8"),
                    "reason": "Nova (automated-nova): Does not publish reasons"
                    } )
        return bans


