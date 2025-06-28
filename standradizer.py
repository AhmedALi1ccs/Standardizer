import requests
import streamlit as st
import pandas as pd
import re
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import chardet
import os
import concurrent.futures
import io

def parallel_process(df, func, column_name, new_column_name):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        df[new_column_name] = list(executor.map(func, df[column_name]))


# Compile the regex patterns beforehand
address_patterns = [(re.compile(pattern, re.IGNORECASE), replacement) for pattern, replacement in {
    r'\bavenue\b\.?': 'Ave', r'\bav\b\.?': 'Ave', r'\bave\b\.?': 'Ave',
    r'\bstreet\b\.?': 'St', r'\bstr\b\.?': 'St', r'\bst\b\.?': 'St',
    r'\bboulevard\b\.?': 'Blvd', r'\bblv\b\.?': 'Blvd', r'\bblvd\b\.?': 'Blvd',
    r'\banex\b\.?': 'Anx', r'\bannex\b\.?': 'Anx', r'\bannx\b\.?': 'Anx',r'\banx\b\.?': 'Anx',
    r'\balley\b\.?': 'Aly', r'\ballee\b\.?': 'Aly', r'\bally\b\.?': 'Aly',r'\baly\b\.?': 'Aly',
    r'\bcamp\b\.?': 'Cp', r'\bcmp\b\.?': 'Cp',r'\bcp\b\.?': 'Cp',
    r'\bcanyn\b\.?': 'Cyn', r'\bcanyon\b\.?': 'Cyn', r'\bcnyn\b\.?': 'Cyn',r'\bcyn\b\.?': 'Cyn',
    r'\bcen\b\.?': 'Ctr', r'\bcent\b\.?': 'Ctr', r'\bcenter\b\.?': 'Ctr',r'\bctr\b\.?': 'Ctr',
    r'\bcentr\b\.?': 'Ctr', r'\bcentre\b\.?': 'Ctr', r'\bcnter\b\.?': 'Ctr',
    r'\bclif\b\.?': 'Clf', r'\bclf\b\.?': 'Clf',
    r'\bclifs\b\.?': 'Clfs', r'\bclfs\b\.?': 'Clfs',
    r'\bclub\b\.?': 'Clb', r'\bclb\b\.?': 'Clb',
    r'\bcommon\b\.?': 'Cmn',r'\bcmn\b\.?': 'Cmn',
    r'\btrafficway\b\.?': 'Trfy',r'\btrfy\b\.?': 'Trfy',
    r'\bcommons\b\.?': 'Cmns',r'\bcmns\b\.?': 'Cmns',
    r'\btrack\b\.?': 'Trak',r'\btracks\b\.?': 'Trak',r'\btrak\b\.?': 'Trak',r'\btrk\b\.?': 'Trak',r'\btrks\b\.?': 'Trak',
    r'\bmill\b\.?': 'Ml',r'\bml\b\.?': 'Ml',
    r'\bmills\b\.?': 'Mls',r'\bmls\b\.?': 'Mls',
    r'\bvill\b\.?': 'Vlg',r'\bvillag\b\.?': 'Vlg',r'\bvillage\b\.?': 'Vlg',r'\bvillg\b\.?': 'Vlg',r'\bvilliage\b\.?': 'Vlg',r'\bvlg\b\.?': 'Vlg',
    r'\bvills\b\.?': 'Vlgs',r'\bvillags\b\.?': 'Vlgs',r'\bvillages\b\.?': 'Vlgs',r'\bvlgs\b\.?': 'Vlgs',
    r'\bville\b\.?': 'Vl',r'\bvl\b\.?': 'Vl',
    r'\bwell\b\.?': 'Wl',r'\bwells\b\.?': 'Wls',r'\bwls\b\.?': 'Wls',
    r'\bhllw\b\.?': 'Holw',r'\bhollow\b\.?': 'Holw',r'\bhollows\b\.?': 'Holw',r'\bholw\b\.?': 'Holw',
    r'\bholws\b\.?': 'Holw',
    r'\bis\b\.?': 'IS',r'\bisland\b\.?': 'IS',r'\bislnd\b\.?': 'IS',
    r'\biss\b\.?': 'ISS',r'\bislands\b\.?': 'ISS',r'\bislnds\b\.?': 'ISS',
    r'\bisle\b\.?': 'Isle',r'\bisles\b\.?': 'Isle',
    r'\bmissn\b\.?': 'Msn',r'\bmssn\b\.?': 'Msn',r'\bmsn\b\.?': 'Msn',
    r'\bmotorway\b\.?': 'Mtwy',r'\bmtwy\b\.?': 'Mtwy',
    r'\bthroughway\b\.?': 'Trwy',r'\btrwy\b\.?': 'Trwy',
    r'\bcorner\b\.?': 'Cor',r'\bcor\b\.?': 'Cor',
    r'\bcorners\b\.?': 'Cors',r'\bcors\b\.?': 'Cors',
    r'\bcourse\b\.?': 'Crse',r'\bcrse\b\.?': 'Crse',
    r'\bdam\b\.?': 'Dm',r'\bdm\b\.?': 'Dm',
    r'\bestate\b\.?': 'Est',r'\best\b\.?': 'Est',
    r'\bestates\b\.?': 'Ests',r'\bests\b\.?': 'Ests',
    r'\bfall\b\.?': 'Fall',
    r'\bfalls\b\.?': 'Fls',r'\bfls\b\.?': 'Fls',
    r'\bfreeway\b\.?': 'Fwy',r'\bfreewy\b\.?': 'Fwy',r'\bfrway\b\.?': 'Fwy',r'\bfwy\b\.?': 'Fwy',
    r'\bht\b\.?': 'Hts',r'\bhts\b\.?': 'Hts',
    r'\bmnrs\b\.?': 'Mnrs', r'\bmanors\b\.?': 'Mnrs',
    r'\bgrove\b\.?': 'Grv',r'\bgrov\b\.?': 'Grv',r'\bgrv\b\.?': 'Grv',
    r'\bgroves\b\.?': 'Grvs',r'\bgrovs\b\.?': 'Grvs',r'\bgrvs\b\.?': 'Grvs',
    r'\bharb\b\.?': 'Hbr',r'\bharbor\b\.?': 'Hbr',r'\bharbr\b\.?': 'Hbr',r'\bhbr\b\.?': 'Hbr',
    r'\bharbors\b\.?': 'Hbrs',r'\bhbrs\b\.?': 'Hbrs',
    r'\bmdw\b\.?': 'Mdws', r'\bmdws\b\.?': 'Mdws',r'\bmeadows\b\.?': 'Mdws', r'\bmedows\b\.?': 'Mdws',
    r'\bhill\b\.?': 'Hl',r'\bhl\b\.?': 'Hl',
    r'\bhills\b\.?': 'Hls',r'\bhls\b\.?': 'Hls',
    r'\bmnr\b\.?': 'Mnr', r'\bmanor\b\.?': 'Mnr',
    r'\bflat\b\.?': 'Flt',r'\bflt\b\.?': 'Flt',
    r'\bflats\b\.?': 'Flts',r'\bflts\b\.?': 'Flts',
    r'\bglen\b\.?': 'Gln',r'\bgln\b\.?': 'Gln',
    r'\bglens\b\.?': 'Glns',r'\bglns\b\.?': 'Glns',
    r'\bferry\b\.?': 'Fry',r'\bfrry\b\.?': 'Fry',r'\bfry\b\.?': 'Fry',
    r'\bgreen\b\.?': 'Grn',r'\bgrn\b\.?': 'Grn',
    r'\bgreens\b\.?': 'Grns',r'\bgrns\b\.?': 'Grns',
    r'\blck\b\.?': 'Lck', r'\block\b\.?': 'Lck',
    r'\bfield\b\.?': 'Fld',r'\bfld\b\.?': 'Fld',
    r'\blcks\b\.?': 'Lcks', r'\blocks\b\.?': 'Lcks',
    r'\bfields\b\.?': 'Flds',r'\bflds\b\.?': 'Flds',
    r'\bloaf\b\.?': 'Lf', r'\blf\b\.?': 'Lf',
    r'\bcenters\b\.?': 'Ctrs',r'\bctrs\b\.?': 'Ctrs',
    r'\barcade\b\.?': 'arc',
    r'\bbayou\b\.?': 'Byu', r'\bbayoo\b\.?': 'Byu',r'\bbyu\b\.?': 'Byu',
    r'\bbeach\b\.?': 'Bch',r'\bbch\b\.?': 'Bch',
    r'\bbend\b\.?': 'Bnd',r'\bbnd\b\.?': 'Bnd',
    r'\bhaven\b\.?': 'Hvn',r'\bhvn\b\.?': 'Hvn',
    r'\bldg\b\.?': 'Ldg', r'\bldge\b\.?': 'Ldg', r'\blodg\b\.?': 'Ldg', r'\blodge\b\.?': 'Ldg',
    r'\bbluf\b\.?': 'Blf', r'\bbluff\b\.?': 'Blf', r'\bblf\b\.?': 'Blf',
    r'\bbluffs\b\.?': 'Blfs',r'\bblfs\b\.?': 'Blfs',
    r'\bbot\b\.?': 'Btm', r'\bbottm\b\.?': 'Btm', r'\bbottom\b\.?': 'Btm',r'\bbtm\b\.?': 'Btm',
    r'\bbr\b\.?': 'Br', r'\bbrnch\b\.?': 'Br', r'\bbranch\b\.?': 'Br',
    r'\bridge\b\.?': 'Rdg',r'\brdg\b\.?': 'Rdg',
    r'\bbrook\b\.?': 'Brk',r'\bbrk\b\.?': 'Brk',
    r'\bbrooks\b\.?': 'Brks',r'\bbrks\b\.?': 'Brks',
    r'\bburg\b\.?': 'Bg',r'\bbg\b\.?': 'Bg',
    r'\bburgs\b\.?': 'Bgs',r'\bbgs\b\.?': 'Bgs',
    r'\bunion\b\.?': 'Un',r'\bunions\b\.?': 'Uns',r'\buns\b\.?': 'Uns',
    r'\bbypa\b\.?': 'Byp', r'\bbypas\b\.?': 'Byp', r'\bbyps\b\.?': 'Byp', r'\bbyp\b\.?': 'Byp',
    r'\broute\b\.?': 'Rte', r'\brt\b\.?': 'Rte',r'\brte\b\.?': 'Rte',
    r'\bbl\b\.?': 'Blvd', r'\broad\b\.?': 'Rd', r'\brd\b\.?': 'Rd',
    r'\bcourt\b\.?': 'Ct', r'\bct\b\.?': 'Ct',
    r'\bcourts\b\.?': 'Cts', r'\bcts\b\.?': 'Cts',
    r'\bcove\b\.?': 'Cv', r'\bcv\b\.?': 'Cv',
    r'\bcoves\b\.?': 'Cvs', r'\bcvs\b\.?': 'Cvs',
    r'\bcrescent\b\.?': 'Cres', r'\bcres\b\.?': 'Cres',r'\bcrsent\b\.?': 'Cres', r'\bcrsnt\b\.?': 'Cres',
    r'\blgts\b\.?': 'Lgts', r'\blights\b\.?': 'Lgts',
    r'\bcrest\b\.?': 'Crst',r'\bcrst\b\.?': 'Crst',
    r'\brest\b\.?': 'Rst',r'\brst\b\.?': 'Rst',
    r'\briv\b\.?': 'Riv',r'\briver\b\.?': 'Riv',r'\brvr\b\.?': 'Riv',r'\brivr\b\.?': 'Riv',
    r'\bcrossroad\b\.?': 'Xrd',r'\bxrd\b\.?': 'Xrd',
    r'\bcrossroads\b\.?': 'Xrds',r'\bxrds\b\.?': 'Xrds',
    r'\bcurve\b\.?': 'Curv',r'\bcurv\b\.?': 'Curv',
    r'\bdale\b\.?': 'Dl',r'\bdl\b\.?': 'Dl',
    r'\bdiv\b\.?': 'Dv',r'\bdivide\b\.?': 'Dv',r'\bdvd\b\.?': 'Dv',r'\bdv\b\.?': 'Dv',
    r'\blgt\b\.?': 'Lgt', r'\blight\b\.?': 'Lgt',
    r'\bforest\b\.?': 'Frst',r'\bforests\b\.?': 'Frst',r'\bfrst\b\.?': 'Frst',
    r'\bforges\b\.?': 'Frgs',r'\bfrgs\b\.?': 'Frgs',
    r'\bforge\b\.?': 'Frg',r'\bfrg\b\.?': 'Frg',r'\bforg\b\.?': 'Frg',
    r'\blakes\b\.?': 'Lks', r'\blks\b\.?': 'Lks',
    r'\blake\b\.?': 'Lk', r'\blk\b\.?': 'Lk',
    r'\blanding\b\.?': 'Lang', r'\blndg\b\.?': 'Lang',r'\blndng\b\.?': 'Lang',r'\blang\b\.?': 'Lang',
    r'\bknls\b\.?': 'Knls', r'\bknols\b\.?': 'knls',
    r'\bdrive\b\.?': 'Dr', r'\bdr\b\.?': 'Dr',
    r'\blane\b\.?': 'Ln', r'\bln\b\.?': 'Ln',
    r'\bterrace\b\.?': 'Ter', r'\bter\b\.?': 'Ter',r'\bte\b\.?': 'Ter',
    
    r'\bplace\b\.?': 'Pl', r'\bpl\b\.?': 'Pl',
    r'\bcircle\b\.?': 'Cir', r'\bcir\b\.?': 'Cir',r'\bcirc\b\.?': 'Cir', r'\bcircl\b\.?': 'Cir',r'\bcrcle\b\.?': 'Cir',r'\bcr\b\.?': 'Cir',
    r'\bsquare\b\.?': 'Sq', r'\bsq\b\.?': 'Sq',
    r'\bhighway\b\.?': 'Hwy', r'\bhwy\b\.?': 'Hwy',
    r'\bplaza\b\.?': 'Plz', r'\bplz\b\.?': 'Plz',
    r'\borch\b\.?': 'Orch', r'\borchard\b\.?': 'Orch',r'\borchrd\b\.?': 'Orch',
    r'\bmnt\b\.?': 'Mt', r'\bmt\b\.?': 'Mt',r'\bmount\b\.?': 'Mt',
    r'\bnck\b\.?': 'Nck', r'\bneck\b\.?': 'Nck',
    r'\bjunction\b\.?': 'Jct', r'\bjct\b\.?': 'Jct',r'\bjction\b\.?': 'Jct', r'\bjctn\b\.?': 'Jct',r'\bjuncton\b\.?': 'Jct', r'\bjunctn\b\.?': 'Jct',
    r'\bjunctions\b\.?': 'Jcts', r'\bjcts\b\.?': 'Jcts',
    r'\bknl\b\.?': 'Knl', r'\bknol\b\.?': 'knl',
    r'\bmountain\b\.?': 'Mtn', r'\bmtn\b\.?': 'Mtn',r'\bmntain\b\.?': 'Mtn', r'\bmntn\b\.?': 'Mtn',r'\bmountin\b\.?': 'Mtn', r'\bmtin\b\.?': 'Mtn',
    r'\bexpressway\b\.?': 'Expy', r'\bexpy\b\.?': 'Expy',
    r'\bextension\b\.?': 'Ext', r'\bext\b\.?': 'Ext',
    r'\bextensions\b\.?': 'Exts', r'\bexts\b\.?': 'Exts',
    r'\bford\b\.?': 'Frd',r'\bfrd\b\.?': 'Frd',
    r'\bfords\b\.?': 'Frds',r'\bfrds\b\.?': 'Frds',
    r'\bfork\b\.?': 'Frk',r'\bfrk\b\.?': 'Frk',
    r'\bforks\b\.?': 'Frks',r'\bfrks\b\.?': 'Frks',
    r'\bgarden\b\.?': 'Gdn',r'\bgardn\b\.?': 'Gdn',r'\bgrden\b\.?': 'Gdn',r'\bgrdn\b\.?': 'Gdn',r'\bgdn\b\.?': 'Gdn',
    r'\bgardens\b\.?': 'Gdns',r'\bgardns\b\.?': 'Gdns',r'\bgrdens\b\.?': 'Gdns',r'\bgrdns\b\.?': 'Gdns',r'\bgdns\b\.?': 'Gdns',
    r'\bkey\b\.?': 'Ky', r'\bky\b\.?': 'Ky',
    r'\bkeys\b\.?': 'Kys', r'\bkys\b\.?': 'Kys',
    r'\btrail\b\.?': 'Trl', r'\btrl\b\.?': 'Trl',
    r'\btrailer\b\.?': 'Trlr', r'\btrlr\b\.?': 'Trlr',r'\btrlrs\b\.?': 'Trlr',
    r'\btrnpk\b\.?': 'Tpke',r'\bturnpike\b\.?': 'Tpke',r'\bturnpk\b\.?': 'Tpke',r'\btpke\b\.?': 'Tpke',
    r'\btunel\b\.?': 'Tunl',r'\btunl\b\.?': 'Tunl',r'\btunls\b\.?': 'Tunl',r'\btunnul\b\.?': 'Tunl',
    r'\bgateway\b\.?': 'Gtwy', r'\bgtwy\b\.?': 'Gtwy',
    r'\bcrossing\b\.?': 'Xing', r'\bxing\b\.?': 'Xing',r'\bcrssng\b\.?': 'Xing',
    r'\bfort\b\.?': 'Ft', r'\bft\b\.?': 'Ft', r'\brow\b\.?': 'Row',
   
    r'\bvalley\b\.?': 'Vly',r'\bvally\b\.?': 'Vly',r'\bvlly\b\.?': 'Vly',r'\bvly\b\.?': 'Vly',
    r'\bvalleys\b\.?': 'Vlys',r'\bvallys\b\.?': 'Vlys',r'\bvllys\b\.?': 'Vlys',r'\bvlys\b\.?': 'Vlys',
    r'\bview\b\.?': 'Vw',r'\bvw\b\.?': 'Vw',r'\bviews\b\.?': 'Vws',r'\bvws\b\.?': 'Vws',
    r'\bcreek\b\.?': 'Crk', r'\bcrk\b\.?': 'Crk',
    r'\boval\b\.?': 'Oval', r'\bovl\b\.?': 'Oval',
    r'\boverpass\b\.?': 'Opas', r'\bopas\b\.?': 'Opas',
    r'\btrace\b\.?': 'Trce',r'\btraces\b\.?': 'Trce',r'\btrce\b\.?': 'Trce',
    r'\bpark\b\.?': 'Park', r'\bprk\b\.?': 'Park',
    r'\bparks\b\.?': 'Parks',
    r'\bpassage\b\.?': 'Psge',r'\bpsge\b\.?': 'Psge',
    r'\bpath\b\.?': 'Path',
    r'\bparkway\b\.?': 'Pkwy', r'\bparkwy\b\.?': 'Pkwy',r'\bpkway\b\.?': 'Pkwy', r'\bpkwy\b\.?': 'Pkwy',
    r'\bway\b\.?': 'Way', r'\bwy\b\.?': 'Way',
    r'\bplain\b\.?': 'Pln',r'\bpln\b\.?': 'Pln',
    r'\bpoint\b\.?': 'Pt',r'\bpoints\b\.?': 'Pts',r'\bpts\b\.?': 'Pts',r'\bpt\b\.?': 'Pt',
    r'\bport\b\.?': 'Prt',r'\bports\b\.?': 'Prts',r'\bprts\b\.?': 'Prts',r'\bprt\b\.?': 'Prt',
    r'\bprairie\b\.?': 'Pr',r'\bprr\b\.?': 'Pr',r'\bpr\b\.?': 'Pr',
    r'\brapid\b\.?': 'Rpd',r'\brpd\b\.?': 'Rpd',
    r'\brun\b\.?': 'Run',
    r'\brapids\b\.?': 'Rpds',r'\brpds\b\.?': 'Rpds',
    r'\bsta\b\.?': 'Sta',r'\bstation\b\.?': 'Sta',r'\bstatn\b\.?': 'Sta',r'\bstn\b\.?': 'Sta',
    r'\bstra\b\.?': 'Stra',r'\bstrav\b\.?': 'Stra',r'\bstraven\b\.?': 'Stra',r'\bstravenue\b\.?': 'Stra',r'\bstravn\b\.?': 'Stra',r'\bstrvn\b\.?': 'Stra',
    r'\bstream\b\.?': 'Strm',r'\bstreme\b\.?': 'Strm',r'\bstrm\b\.?': 'Strm',
    r'\bsmt\b\.?': 'Smt',r'\bsumit\b\.?': 'Smt',r'\bsumitt\b\.?': 'Smt',r'\bsummit\b\.?': 'Smt',
    r'\brad\b\.?': 'Radl',r'\bradial\b\.?': 'Radl',r'\bradiel\b\.?': 'Radl',r'\bradl\b\.?': 'Radl',
    r'\bshl\b\.?': 'Shl',r'\bshoal\b\.?': 'Shl',r'\bshls\b\.?': 'Shls',r'\bshoals\b\.?': 'Shls',
    r'\bshr\b\.?': 'Shr',r'\bshoar\b\.?': 'Shr',r'\bshore\b\.?': 'Shr',r'\bshrs\b\.?': 'Shrs',r'\bshoars\b\.?': 'Shrs',r'\bshores\b\.?': 'Shrs',
    r'\bspg\b\.?': 'Spg',r'\bspng\b\.?': 'Spg',r'\bspring\b\.?': 'Spg',r'\bsprng\b\.?': 'Spg',r'\bspgs\b\.?': 'Spgs',r'\bspngs\b\.?': 'Spgs',r'\bsprings\b\.?': 'Spgs',r'\bsprngs\b\.?': 'Spgs',
}.items()]

directional_patterns = {re.compile(pattern, re.IGNORECASE): replacement for pattern, replacement in {
    r'\bnorth\b\.?': 'N', r'\bnorthern\b\.?': 'N', r'\bn\b\.?': 'N',
    r'\bwest\b\.?': 'W', r'\bwestern\b\.?': 'W', r'\bw\b\.?': 'W',
    r'\beast\b\.?': 'E', r'\beastern\b\.?': 'E', r'\be\b\.?': 'E',
    r'\bsouth\b\.?': 'S', r'\bsouthern\b\.?': 'S', r'\bs\b\.?': 'S',r'\bsouthwest\b\.?': 'SW',r'\bnorthwest\b\.?': 'NW',r'\bnortheast\b\.?': 'SE',r'\bsoutheast\b\.?': 'SE'
}.items()}

ordinal_mapping = {
    'first': '1st', 'second': '2nd', 'third': '3rd', 'fourth': '4th', 'fifth': '5th',
    'sixth': '6th', 'seventh': '7th', 'eighth': '8th', 'ninth': '9th', 'tenth': '10th',
    'eleventh': '11th', 'twelfth': '12th', 'thirteenth': '13th', 'fourteenth': '14th',
    'fifteenth': '15th', 'sixteenth': '16th', 'seventeenth': '17th', 'eighteenth': '18th',
    'nineteenth': '19th', 'twentieth': '20th', 'twenty-first': '21st', 'twenty first': '21st', 'twentyfirst': '21st',
    'twenty-second': '22nd', 'twenty second': '22nd', 'twentysecond': '22nd', 'twenty-third': '23rd',
    'twenty third': '23rd', 'twentythird': '23rd',
    'twenty-fourth': '24th', 'twenty fourth': '24th', 'twentyfourth': '24th', 'twenty-fifth': '25th',
    'twenty fifth': '25th', 'twentyfifth': '25th',
    'twenty-sixth': '26th', 'twenty sixth': '26th', 'twentysixth': '26th', 'twenty-seventh': '27th',
    'twenty seventh': '27th', 'twentyseventh': '27th',
    'twenty-eighth': '28th', 'twenty eighth': '28th', 'twentyeighth': '28th', 'twenty-ninth': '29th',
    'twenty ninth': '29th', 'twentyninth': '29th',
    'thirtieth': '30th', 'thirty-first': '31st', 'thirty first': '31st', 'thirtyfirst': '31st', 'thirty-second': '32nd',
    'thirty second': '32nd', 'thirtysecond': '32nd',
    'thirty-third': '33rd', 'thirty third': '33rd', 'thirtythird': '33rd', 'thirty-fourth': '34th',
    'thirty fourth': '34th', 'thirtyfourth': '34th',
    'thirty-fifth': '35th', 'thirty fifth': '35th', 'thirtyfifth': '35th', 'thirty-sixth': '36th',
    'thirty sixth': '36th', 'thirtysixth': '36th',
    'thirty-seventh': '37th', 'thirty seventh': '37th', 'thirtyseventh': '37th', 'thirty-eighth': '38th',
    'thirty eighth': '38th', 'thirtyeighth': '38th',
    'thirty-ninth': '39th', 'thirty ninth': '39th', 'thirtyninth': '39th', 'fortieth': '40th', 'forty-first': '41st',
    'forty first': '41st', 'fortyfirst': '41st',
    'forty-second': '42nd', 'forty second': '42nd', 'fortysecond': '42nd', 'forty-third': '43rd', 'forty third': '43rd',
    'fortythird': '43rd',
    'forty-fourth': '44th', 'forty fourth': '44th', 'fortyfourth': '44th', 'forty-fifth': '45th', 'forty fifth': '45th',
    'fortyfifth': '45th',
    'forty-sixth': '46th', 'forty sixth': '46th', 'fortysixth': '46th', 'forty-seventh': '47th',
    'forty seventh': '47th', 'fortyseventh': '47th',
    'forty-eighth': '48th', 'forty eighth': '48th', 'fortyeighth': '48th', 'forty-ninth': '49th', 'forty ninth': '49th',
    'fortyninth': '49th',
    'fiftieth': '50th', 'fifty-first': '51st', 'fifty first': '51st', 'fiftyfirst': '51st', 'fifty-second': '52nd',
    'fifty second': '52nd', 'fiftysecond': '52nd',
    'fifty-third': '53rd', 'fifty third': '53rd', 'fiftythird': '53rd', 'fifty-fourth': '54th', 'fifty fourth': '54th',
    'fiftyfourth': '54th',
    'fifty-fifth': '55th', 'fifty fifth': '55th', 'fiftyfifth': '55th', 'fifty-sixth': '56th', 'fifty sixth': '56th',
    'fiftysixth': '56th',
    'fifty-seventh': '57th', 'fifty seventh': '57th', 'fiftyseventh': '57th', 'fifty-eighth': '58th',
    'fifty eighth': '58th', 'fiftyeighth': '58th',
    'fifty-ninth': '59th', 'fifty ninth': '59th', 'fiftyninth': '59th', 'sixtieth': '60th', 'sixty-first': '61st',
    'sixty first': '61st', 'sixtyfirst': '61st',
    'sixty-second': '62nd', 'sixty second': '62nd', 'sixtysecond': '62nd', 'sixty-third': '63rd', 'sixty third': '63rd',
    'sixtythird': '63rd',
    'sixty-fourth': '64th', 'sixty fourth': '64th', 'sixtyfourth': '64th', 'sixty-fifth': '65th', 'sixty fifth': '65th',
    'sixtyfifth': '65th',
    'sixty-sixth': '66th', 'sixty sixth': '66th', 'sixtysixth': '66th', 'sixty-seventh': '67th',
    'sixty seventh': '67th', 'sixtyseventh': '67th',
    'sixty-eighth': '68th', 'sixty eighth': '68th', 'sixtyeighth': '68th', 'sixty-ninth': '69th', 'sixty ninth': '69th',
    'sixtyninth': '69th',
    'seventieth': '70th', 'seventy-first': '71st', 'seventy first': '71st', 'seventyfirst': '71st',
    'seventy-second': '72nd', 'seventy second': '72nd', 'seventysecond': '72nd',
    'seventy-third': '73rd', 'seventy third': '73rd', 'seventythird': '73rd', 'seventy-fourth': '74th',
    'seventy fourth': '74th', 'seventyfourth': '74th',
    'seventy-fifth': '75th', 'seventy fifth': '75th', 'seventyfifth': '75th', 'seventy-sixth': '76th',
    'seventy sixth': '76th', 'seventysixth': '76th',
    'seventy-seventh': '77th', 'seventy seventh': '77th', 'seventyseventh': '77th', 'seventy-eighth': '78th',
    'seventy eighth': '78th', 'seventyeighth': '78th',
    'seventy-ninth': '79th', 'seventy ninth': '79th', 'seventyninth': '79th', 'eightieth': '80th',
    'eighty-first': '81st', 'eighty first': '81st', 'eightyfirst': '81st',
    'eighty-second': '82nd', 'eighty second': '82nd', 'eightysecond': '82nd', 'eighty-third': '83rd',
    'eighty third': '83rd', 'eightythird': '83rd',
    'eighty-fourth': '84th', 'eighty fourth': '84th', 'eightyfourth': '84th', 'eighty-fifth': '85th',
    'eighty fifth': '85th', 'eightyfifth': '85th',
    'eighty-sixth': '86th', 'eighty sixth': '86th', 'eightysixth': '86th', 'eighty-seventh': '87th',
    'eighty seventh': '87th', 'eightyseventh': '87th',
    'eighty-eighth': '88th', 'eighty eighth': '88th', 'eightyeighth': '88th', 'eighty-ninth': '89th',
    'eighty ninth': '89th', 'eightyninth': '89th',
    'ninetieth': '90th', 'ninety-first': '91st', 'ninety first': '91st', 'ninetyfirst': '91st', 'ninety-second': '92nd',
    'ninety second': '92nd', 'ninetysecond': '92nd',
    'ninety-third': '93rd', 'ninety third': '93rd', 'ninetythird': '93rd', 'ninety-fourth': '94th',
    'ninety fourth': '94th', 'ninetyfourth': '94th',
    'ninety-fifth': '95th', 'ninety fifth': '95th', 'ninetyfifth': '95th', 'ninety-sixth': '96th',
    'ninety sixth': '96th', 'ninetysixth': '96th',
    'ninety-seventh': '97th', 'ninety seventh': '97th', 'ninetyseventh': '97th', 'ninety-eighth': '98th',
    'ninety eighth': '98th', 'ninetyeighth': '98th',
    'ninety-ninth': '99th', 'ninety ninth': '99th', 'ninetyninth': '99th', 'hundredth': '100th'
}


def clean_full_zip(zip_code):
    zip_code = str(zip_code).replace(',', '').replace('.0', '')
    return zip_code[:5]  # Only keep the first 5 digits

def preprocess_address(address):
    # Standardize unit labels
    def standardize_unit_label(unit_label):
        unit_label = unit_label.strip().lower()
        if unit_label in ['apt', 'unit', '#', 'suite', 'bldg', 'building']:
            return 'Unit'
        return unit_label

    # 3. Remove the # symbol and dash before numbers (e.g., "Apt #-123" -> "Apt 123")
    address = re.sub(r'#-?\s*(\d+)', r'\1', address)

    # Convert the address to lowercase for consistent processing
    address = address.lower().strip()

    # Handle duplex/triplex/quadruplex pattern: "5800 Hunting Hollow Ct 5802" -> "5800-5802 Hunting Hollow Ct"
    duplex_pattern = re.compile(r'^(\d+)\s+([\w\s]+)\s+(\d+)$', re.IGNORECASE)
    duplex_match = duplex_pattern.match(address)
    if duplex_match:
        num1 = int(duplex_match.group(1))
        num2 = int(duplex_match.group(3))
        street_name = duplex_match.group(2).strip()
        if abs(num1 - num2) in [2, 4,6, 8]:
            print(f"Transforming {address} to {num1}-{num2} {street_name}")
            return f"{num1}-{num2} {street_name}"
        else:
            print(f"Numbers {num1} and {num2} do not differ by 2, 4,6, or 8. Keeping original format.")
    else:
        print(f"No duplex match found for address: {address}")

    # Handle state route pattern: "1230 - 123 N state Rte" -> "1230 N state Rte 123"
    state_route_pattern = re.compile(r'^(\d+)\s*-\s*(\d+)\s*([NSEW]?)\s*(state\s+rte|state\s+route|state\s+rt)', re.IGNORECASE)
    state_route_match = state_route_pattern.match(address)
    if state_route_match:
        num1 = state_route_match.group(1)
        num2 = state_route_match.group(2)
        direction = state_route_match.group(3).strip()
        route_type = state_route_match.group(4).strip()
        if direction:
            new_address = f"{num1} {direction} {route_type} {num2}"
        else:
            new_address = f"{num1} {route_type} {num2}"
        print(f"Transforming {address} to {new_address}")
        return new_address
    address = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1-\2', address)
    # 4. Convert "456 Maple Ave 34-Unit" to "456 Maple Ave Unit 34"
    address = re.sub(r'(\d+)-unit', r'unit \1', address)

    # 5. State-route adjusting for addresses without direction (already covered above)
    address = re.sub(r'(\d+)-(\d+)\s+(state\s+rte|state\s+route|state\s+rt)', r'\1 \3 \2', address)

    # 7. Remove dash in "123 Main St 12-A" -> "123 Main St 12A"
    address = re.sub(r'(\d+)-([a-zA-Z])$', r'\1\2', address)

    # 8. Remove "Complex A" or "Building B" from any part of the address
    address = re.sub(r',?\s*(complex|building)\s+[a-z]', '', address, flags=re.IGNORECASE)

    # Return the address unchanged if no patterns matched
    return address



@lru_cache(maxsize=128)
def get_city_and_state_from_zip(zip_code):
    url = f"http://api.zippopotam.us/us/{zip_code}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'places' in data and len(data['places']) > 0:
            city = data['places'][0]['place name']
            state = data['places'][0]['state abbreviation']
            return city, state
    return None, None

async def fetch_city_and_state(session, zip_code):
    url = f"http://api.zippopotam.us/us/{zip_code}"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            if 'places' in data and len(data['places']) > 0:
                city = data['places'][0]['place name']
                state = data['places'][0]['state abbreviation']
                return zip_code, city, state
    return zip_code, None, None
async def fetch_city_state_map_async(zip_codes, max_concurrent_tasks=100):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        async def fetch_with_sem(zip_code):
            async with semaphore:
                return await fetch_city_and_state(session, zip_code)

        tasks = [fetch_with_sem(zip_code) for zip_code in zip_codes]
        results = await asyncio.gather(*tasks)
        city_map = {zip_code: city for zip_code, city, _ in results}
        state_map = {zip_code: state for zip_code, _, state in results}
        return city_map, state_map
def fetch_city_state_map(zip_codes):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    city_map, state_map = loop.run_until_complete(fetch_city_state_map_async(zip_codes))
    return city_map, state_map

def adjust_cities_and_states(df, mapped_columns):
    def clean_zip(zip_code):
        return str(zip_code).replace(',', '').replace('.0', '')

    if mapped_columns['property_zip'] != 'none':
        property_zip_col = mapped_columns['property_zip']
        
        # Clean and convert the property ZIP codes to strings
        df[property_zip_col] = df[property_zip_col].apply(clean_zip)
        df[property_zip_col] = df[property_zip_col].apply(clean_full_zip)
        zip_codes = df[property_zip_col].unique()
        city_map, state_map = fetch_city_state_map(zip_codes)
        
        if mapped_columns['property_city'] != 'none':
            property_city_col = mapped_columns['property_city']
            df[property_city_col] = df[property_zip_col].map(city_map).fillna(df[property_city_col])
        
        if mapped_columns['property_state'] != 'none':
            property_state_col = mapped_columns['property_state']
            df[property_state_col] = df[property_zip_col].map(state_map).fillna(df[property_state_col])

    if mapped_columns['mailing_zip'] != 'none':
        mailing_zip_col = mapped_columns['mailing_zip']
        
        # Clean and convert the mailing ZIP codes to strings
        df[mailing_zip_col] = df[mailing_zip_col].apply(clean_zip)
        df[mailing_zip_col] = df[mailing_zip_col].apply(clean_full_zip)
        zip_codes = df[mailing_zip_col].unique()
        city_map, state_map = fetch_city_state_map(zip_codes)
        
        if mapped_columns['mailing_city'] != 'none':
            mailing_city_col = mapped_columns['mailing_city']
            df[mailing_city_col] = df[mailing_zip_col].map(city_map).fillna(df[mailing_city_col])
            
        if mapped_columns['mailing_state'] != 'none':
            mailing_state_col = mapped_columns['mailing_state']
            df[mailing_state_col] = df[mailing_zip_col].map(state_map).fillna(df[mailing_state_col])

    return df
@lru_cache(maxsize=128)
def get_city_from_zip(zip_code):
    url = f"http://api.zippopotam.us/us/{zip_code}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'places' in data and len(data['places']) > 0:
            return data['places'][0]['place name']
    return None


async def fetch_city(session, zip_code):
    url = f"http://api.zippopotam.us/us/{zip_code}"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            if 'places' in data and len(data['places']) > 0:
                return zip_code, data['places'][0]['place name']
    return zip_code, None


async def fetch_city_map_async(zip_codes, max_concurrent_tasks=100):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        async def fetch_with_sem(zip_code):
            async with semaphore:
                return await fetch_city(session, zip_code)

        tasks = [fetch_with_sem(zip_code) for zip_code in zip_codes]
        results = await asyncio.gather(*tasks)
        return {zip_code: city for zip_code, city in results}


def fetch_city_map(zip_codes):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    city_map = loop.run_until_complete(fetch_city_map_async(zip_codes))
    return city_map


# Column mapping configuration with variations
column_mapping_config = {
    'property_address': ['property address', 'address', 'property_address', 'site address', "Street", 'street_address'],
    'property_city': ['property city', 'city', 'property_city'],
    'property_state': ['property state', 'state', 'property_state', "region"],
    'property_zip': ['property zip', 'property zipcode', 'zip', 'zipcode', 'property_zip', 'property_zipcode',
                     'zip code', "PostalCode", "postal_code"],
    'mailing_address': ['mailing address', 'owner address', 'mailing_address', 'owner_address'],
    'mailing_city': ['mailing city', 'owner city', 'mailing_city', 'owner_city'],
    'mailing_state': ['mailing state', 'owner state', 'mailing_state', 'owner_state'],
    'mailing_zip': ['mailing zip', 'mailing zipcode', 'owner zip', 'owner zipcode', 'mailing_zip', 'mailing_zipcode',
                    'owner_zip', 'owner_zipcode'],
    'full_name': ['full name', 'owner full name', 'first owner full name', 'full_name', 'owner_full_name',
                  'first_owner_full_name', 'owner contact name'],
    'first_name': ['first name', 'owner first name', 'first owner first name', 'first_name', 'owner_first_name',
                   'first_owner_first_name'],
    'last_name': ['last name', 'owner last name', 'first owner last name', 'last_name', 'owner_last_name',
                  'first_owner_last_name']
}


# Function to standardize column names for easier matching
def standardize_column_name(name):
    return re.sub(r'[\s_]+', ' ', name.strip().lower())




# Function to convert text to title case
def to_title_case(text):
    if isinstance(text, str):
        # Split the text into words and capitalize the first letter of each word
        return ' '.join(word.capitalize() for word in text.split())
    return text


# Function to map columns automatically

# Function to adjust cities based on ZIP codes
def adjust_cities(df, mapped_columns):
    def clean_zip(zip_code):
        return str(zip_code).replace(',', '').replace('.0', '')

    if mapped_columns['property_zip'] != 'none' and mapped_columns['property_city'] != 'none':
        property_zip_col = mapped_columns['property_zip']
        property_city_col = mapped_columns['property_city']

        # Clean and convert the property ZIP codes to strings
        df[property_zip_col] = df[property_zip_col].apply(clean_zip)
        df[property_zip_col] = df[property_zip_col].apply(clean_full_zip)
        zip_codes = df[property_zip_col].unique()
        city_map = fetch_city_map(zip_codes)

        df[property_city_col] = df[property_zip_col].map(city_map).fillna(df[property_city_col])

    if mapped_columns['mailing_zip'] != 'none' and mapped_columns['mailing_city'] != 'none':
        mailing_zip_col = mapped_columns['mailing_zip']
        mailing_city_col = mapped_columns['mailing_city']

        # Clean and convert the mailing ZIP codes to strings
        df[mailing_zip_col] = df[mailing_zip_col].apply(clean_zip)
        df[mailing_zip_col] = df[mailing_zip_col].apply(clean_full_zip)
        zip_codes = df[mailing_zip_col].unique()
        city_map = fetch_city_map(zip_codes)

        df[mailing_city_col] = df[mailing_zip_col].map(city_map).fillna(df[mailing_city_col])

    return df


# Function to standardize and normalize address, ensuring the second suffix is replaced

def standardize_and_normalize_address(address):
    if isinstance(address, str):
        # Remove '#' symbols followed by numbers
        address = re.sub(r'\s*#\s*(?=\d*\s|$)', ' ', address)
        # Convert to lower case
        address = address.lower()
        # Split into words
        words = address.split()

        # Replace multi-word ordinal phrases
        i = 0
        while i < len(words) - 1:
            two_word = f"{words[i]} {words[i + 1]}"
            if two_word in ordinal_mapping:
                words[i] = ordinal_mapping[two_word]
                del words[i + 1]
            else:
                i += 1

        # Replace single-word ordinals
        words = [ordinal_mapping.get(word, word) for word in words]

        # Reconstruct the address after ordinal replacement
        address = ' '.join(words)

        # Replace address patterns
        words = address.split()
        last_index_to_replace = None

        # Track the last index of an address pattern match
        for i, word in enumerate(words):
            for pattern, replacement in address_patterns:
                if pattern.match(word):
                    last_index_to_replace = i

        # Replace the last occurrence of the address pattern
        if last_index_to_replace is not None:
            for pattern, replacement in address_patterns:
                if pattern.match(words[last_index_to_replace]):
                    words[last_index_to_replace] = pattern.sub(replacement, words[last_index_to_replace])
                    break

        # Replace directional patterns unless followed by an address pattern
        for i, word in enumerate(words):
            for pattern, replacement in directional_patterns.items():
                if pattern.match(word):
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        if any(addr_pattern.match(next_word) for addr_pattern, _ in address_patterns):
                            continue
                    words[i] = pattern.sub(replacement, words[i])
                    break

        # Reconstruct the address
        address = ' '.join(words)

    return address



import dask.dataframe as dd


# Column mapping configuration with variations
column_mapping_config = {
    'property_address': ['property address', 'address', 'property_address', 'site address', "Street", 'street_address'],
    'property_city': ['property city', 'city', 'property_city'],
    'property_state': ['property state', 'state', 'property_state', "region"],
    'property_zip': ['property zip', 'property zipcode', 'zip', 'zipcode', 'property_zip', 'property_zipcode',
                     'zip code', "PostalCode", "postal_code"],
    'mailing_address': ['mailing address', 'owner address', 'mailing_address', 'owner_address'],
    'mailing_city': ['mailing city', 'owner city', 'mailing_city', 'owner_city'],
    'mailing_state': ['mailing state', 'owner state', 'mailing_state', 'owner_state'],
    'mailing_zip': ['mailing zip', 'mailing zipcode', 'owner zip', 'owner zipcode', 'mailing_zip', 'mailing_zipcode',
                    'owner_zip', 'owner_zipcode'],
    'full_name': ['full name', 'owner full name', 'first owner full name', 'full_name', 'owner_full_name',
                  'first_owner_full_name', 'owner contact name'],
    'first_name': ['first name', 'owner first name', 'first owner first name', 'first_name', 'owner_first_name',
                   'first_owner_first_name'],
    'last_name': ['last name', 'owner last name', 'first owner last name', 'last_name', 'owner_last_name',
                  'first_owner_last_name']
}

def create_standardized_column_map(df_columns):
    return {re.sub(r'[\s_]+', ' ', col.strip().lower()): col for col in df_columns}

def map_columns(df, config, standardized_columns_map):
    mapped_columns = {}
    for key, possible_names in config.items():
        for name in possible_names:
            standardized_name = re.sub(r'[\s_]+', ' ', name.strip().lower())
            if standardized_name in standardized_columns_map:
                mapped_columns[key] = standardized_columns_map[standardized_name]
                break
        else:
            mapped_columns[key] = 'none'
    return mapped_columns

# Streamlit app starts here
st.title("Address Normalization and ZIP Code Adjustment")

# File upload and reading
uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # Convert the uploaded file to a format that can be used by pandas
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()), encoding='utf-8')
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()))

        st.write("File Uploaded Successfully")

       
        # Create the standardized column map after df is defined
        standardized_columns_map = create_standardized_column_map(df.columns)

        # Map columns automatically using the standardized map
        mapped_columns = map_columns(df, column_mapping_config, standardized_columns_map)

        

        # Filter the DataFrame to keep only the relevant columns
        df_filtered = df[[mapped_columns[key] for key in mapped_columns if mapped_columns[key] != 'none']]

        if df_filtered.empty:
            st.error("No relevant columns found after mapping.")
        else:
            st.write("Filtered DataFrame:", df_filtered.head())

    except Exception as e:
        st.error(f"Failed to process file: {e}")

    # Ensure df is defined before proceeding
    if 'df' in locals():
        # Create standardized column map after df is defined
        standardized_columns_map = create_standardized_column_map(df.columns)

        # Use the standardized map to map columns
        mapped_columns = map_columns(df, column_mapping_config, standardized_columns_map)

        # Continue with further processing...
        st.write("Mapped Columns: ", mapped_columns)


        # Allow the user to adjust the mappings
        st.write("Please confirm or adjust the column mappings:")
        for key in column_mapping_config.keys():
            options = ['none'] + list(df.columns)
            default_index = options.index(mapped_columns.get(key)) if mapped_columns.get(key) in options else 0
            mapped_columns[key] = st.selectbox(f"Select column for {key.replace('_', ' ').title()}:", options,
                                               index=default_index)

        # Standardize button
        if st.button("Standardize"):
            # Apply the functions to the addresses
            if mapped_columns.get('property_address') != 'none':
                property_address_col = mapped_columns['property_address']
                df[property_address_col].fillna('', inplace=True)
                df[property_address_col]=df[property_address_col].apply(preprocess_address)
                df[property_address_col] = df[property_address_col].apply(standardize_and_normalize_address)

            if mapped_columns.get('mailing_address') != 'none':
                mailing_address_col = mapped_columns['mailing_address']
                df[mailing_address_col].fillna('', inplace=True)

                df[mailing_address_col] = df[mailing_address_col].apply(standardize_and_normalize_address)

            # Adjust cities
            df = adjust_cities_and_states(df, mapped_columns)

            # Convert relevant columns to title case if they exist
            for key in ['full_name', 'first_name', 'last_name']:
                if key in mapped_columns and mapped_columns[key] != 'none':
                    df[mapped_columns[key]] = df[mapped_columns[key]].apply(to_title_case)

            st.write("Addresses Normalized and Names Converted to Name Case Successfully")
            st.write(df.head())

            # Provide a text input for the user to specify the file name
            file_name, file_extension = os.path.splitext(uploaded_file.name)
            output_file_name = f"{file_name}_standardized.csv"

            # Provide download link for the updated file
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Updated File", data=csv, file_name=output_file_name, mime="text/csv")

            # Instruction for moving the file
            st.markdown("""
                **Instructions:**
                - After downloading, you can manually move the file to your desired location.
                - To move the file, use your file explorer and drag the downloaded file to the preferred folder.
            """)
    else:
        st.error("Required columns are missing in the uploaded file.")
