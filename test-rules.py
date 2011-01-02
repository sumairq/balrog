import os, glob
try:
    import json
except:
    import simplejson as json
from AUS import *

def populateDB(AUS):
    # assuming we're already in the right directory with a db connection
    # read any rules we already have
    if os.path.exists('rules.sql'):
        f = open('rules.sql','r')
        for line in f:
            if line.startswith('#'):
                continue
            AUS.db.execute(line.strip())
    # and add any json blobs we created painstakingly, converting to compact json
    for f in glob.glob('*.json'):
        data = json.load(open(f,'r'))
        product,version = data['name'].split('-')[0:2]
        AUS.db.execute("INSERT INTO releases VALUES ('%s', '%s', '%s','%s')" %
                   (data['name'], product, version, json.dumps(data)))
    AUS.db.commit()
    # TODO - create a proper importer that walks the snippet store to find hashes ?

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults(
        db='update.db'
    )
    parser.add_option("-c", "--clobber", dest="clobber", action="store_true", help="clobber existing db")
    parser.add_option("-i", "--inputdir", dest="inputdir", help="aus datastore to read")
    parser.add_option("-d", "--db", dest="db", help="database to use, relative to inputdir")
    parser.add_option("", "--dump-rules", dest="dumprules", action="store_true", help="dump rules to stdout")
    parser.add_option("", "--dump-releases", dest="dumpreleases", action="store_true", help="dump release data to stdout")

    options, args = parser.parse_args()
    if not options.inputdir or not os.path.isdir(options.inputdir):
        parser.error('Must specify a directory to read with -i/--inputdir')
    os.chdir(options.inputdir)

    if options.clobber and os.path.exists(options.db):
        os.remove(options.db)
    AUS = AUS3(dbname = options.db)
    if options.clobber:
        populateDB(AUS)

    # "pretty" printing
    if options.dumprules:
        AUS.dumpRules()
    if options.dumpreleases:
        AUS.dumpReleases()


    # version 3 update + UA arch
    testUpdate = {'product': 'Firefox',
                  'version': '3.6.12',
                  'buildID': '20101026210630',
                  'buildTarget': 'WINNT_x86-msvc',
                  'locale': 'en-US',
                  'channel': 'releasetest',
                  'osVersion': 'foo',
                  'distribution': 'foo',
                  'distVersion': 'foo',
                  'headerArchitecture': 'Intel',
                  'name': ''
                 }
    
    testUpdate['name'] = AUS.identifyRequest(testUpdate)
    print "\nThe request is from %s" % testUpdate['name']
    
    rule = AUS.evaluateRules(testUpdate)
    print "\nthe one rule to rule them all is:"
    print rule
    
    snippets = AUS.createSnippet(testUpdate,rule)
    if snippets:
        for type in snippets.keys():
            print "\n%s snippet:" % type
            print snippets[type]
    else:
        print "\nno snippets"
        
    xml = AUS.createXML(testUpdate,rule)
    print "\nxml is:\n%s" % xml

    # once this is working, walk tree of snippets and calculate snippet
    # compare to data on disk
    # use this to fill out rules (ignore locales for now ? lots of hashes/sizes)
    # create a way to programaticaly generate the json