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
        thingy = self.config[self.config_section][self.config_section_list]
        pprint(thingy)
        try:
            self.domains = json.loads(thingy)
        except Exception as exc:
            print(f"config file section parsers item '{self.config_section}'" +
                  f" doesn't parse as valid json, please fix - {exc}")
            # rjh -- again, this is not an EXIT_SUCCESS condition
            sys.exit(-1)

    def getbans(self):
        for domain in self.domains:
            page = requests.get(f"https://{domain}/about/more")
            print(page)
            tables = BeautifulSoup(page.content, 'html5lib').find_all('table')
            bans = []
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
