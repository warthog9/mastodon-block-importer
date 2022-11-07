from ban_list_parser import ban_list_parser

from bs4 import BeautifulSoup

import requests
import re

import sys

class bans( ban_list_parser ):
    tf_list_url = "https://wiki.tenforward.social/doku.php?id=tenforward:suspensions&do=edit"

    ban_prefix = "tenforward"

    def __init__( self, config=None ):
        self.config = config

    def getbans(self):
        page = requests.get(self.tf_list_url)
        print( page )
        soup = BeautifulSoup(page.content, 'html5lib')
        editblock = soup.find_all( 'textarea',  class_="edit" )

        str_editblock = str( editblock[0] )

        #print( str_editblock )

        re_block_reason = re.compile( r"\[\[(.*)\|(.*)]]" )
        re_site = re.compile( r"\[\[(.*)\|(.*)]]" )
        match_pattern = "  * "
        x = 0

        bans = []
        for line in str_editblock.splitlines():
            #print( "{}: {}".format( x, line ) )
            x = x + 1
            if line.startswith( match_pattern ):
                print( "~ {}".format( line ) )
                # ok now that we have the line, lets figure out if it is a site or a site + reason
                if line.startswith( match_pattern +"[[" ):
                    # ok this has a pointer to a reason
                   found = re_block_reason.search( line )
                   reason = "{}: {}".format( self.ban_prefix, found.group(1) )
                   site = found.group(2)
                else:
                    reason = "{}: no reason given".format( self.ban_prefix )
                    site = line.removeprefix( match_pattern )
                print( "site: {}".format( site ) )
                print( "reason: {}".format( reason ) )
                if "/" in site:
                    for subsite in site.split('/'):
                        bans.append( {
                                "domain": subsite,
                                "reason": reason
                                } )
                else:
                    bans.append( { "domain": site, "reason": reason } )
        return bans


