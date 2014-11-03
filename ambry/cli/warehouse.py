"""
Copyright (c) 2013 Clarinova. This file is licensed under the terms of the
Revised BSD License, included in this distribution as LICENSE.txt
"""

from . import prt, fatal, err, warn,  _print_info, _print_bundle_list
from ..dbexceptions import ConfigurationError

# If the devel module exists, this is a development system.
try: from ambry.support.devel import *
except ImportError as e: from ambry.support.production import *

def warehouse_command(args, rc):
    from ambry.warehouse import new_warehouse
    from ..library import new_library
    from . import global_logger
    from ambry.warehouse import database_config
    from ..dbexceptions import ConfigurationError


    l = new_library(rc.library(args.library_name))

    l.logger = global_logger

    config = None

    if args.database:

        try: # Its a name for the warehouse section of the config
            config = rc.warehouse(args.database)
        except ConfigurationError: # It is a database connection string.
            config = database_config(args.database)


    if not config and args.name:

        f  = l.files.query.ref(args.name).group(l.files.TYPE.STORE).one_maybe
        if f:
            config = database_config(f.path)

    if not config and args.subcommand == 'install':
        from ..warehouse.manifest import Manifest
        import os.path

        m = Manifest(args.term)

        base_dir = os.path.join(rc.filesystem('warehouse')['dir'], m.cache_path)

        config = database_config(m.database, base_dir=base_dir)

    if not config and  args.subcommand != 'list':
        raise ConfigurationError("Must set the name of the database somewhere. ")

    if config:
        w = new_warehouse(config, l, logger = global_logger)

        if not w.exists():
            w.create()

        if args.name:
            store_warehouse(l,w,args.name)
    else:
        w = None

    globals()['warehouse_'+args.subcommand](args, w,rc)

def store_warehouse(l,w, name):

    w.name = name

    if not l.files.query.ref(name).group(l.files.TYPE.STORE).one_maybe:
        l.files.install_data_store(w.database.dsn, w.__class__.__name__, ref = name,
                                   title = w.title, summary  = w.summary )

def warehouse_parser(cmd):
   
    whr_p = cmd.add_parser('warehouse', help='Manage a warehouse')
    whr_p.set_defaults(command='warehouse')
    whp = whr_p.add_subparsers(title='warehouse commands', help='command help')

    whr_p.add_argument('-d', '--database', help='Path or connection url for a database. ')
    whr_p.add_argument('-n','--name',  help='Select a different name for the warehouse')

    whsp = whp.add_parser('install', help='Install a bundle or partition to a warehouse')
    whsp.set_defaults(subcommand='install')
    whsp.add_argument('-C', '--clean', default=False, action='store_true', help='Remove all data from the database before installing')
    whsp.add_argument('-n', '--name-only', default=False, action='store_true', help='The only output will be the DSN of the warehouse')
    whsp.add_argument('-R', '--reset-config', default=False, action='store_true',
                      help='Reset all of the values, like title and about, that come from the manifest'),
    whsp.add_argument('-F', '--force', default=False, action='store_true',
                      help='Force re-creation of files that already exist')
    whsp.add_argument('-K', '--doc', default=False, action='store_true', help='Also generate documentation')

    # For extract, when called from install
    group = whsp.add_mutually_exclusive_group()
    group.add_argument('-l', '--local', dest='dest',  action='store_const', const='local')
    group.add_argument('-r', '--remote', dest='dest', action='store_const', const='remote')
    group.add_argument('-c', '--cache' )
    whsp.add_argument('-D', '--dir', default = '', help='Set directory, instead of configured Warehouse filesystem dir, for relative paths')


    whsp.add_argument('term', type=str,help='Name of bundle or partition')

    whsp = whp.add_parser('extract', help='Extract files or documentation to a cache')
    whsp.set_defaults(subcommand='extract')
    whsp.add_argument('-f', '--files-only', default=False, action='store_true', help='Only extract the extract files')
    whsp.add_argument('-d', '--doc-only', default=False, action='store_true', help='Only extract the documentation files')
    group = whsp.add_mutually_exclusive_group()
    group.add_argument('-l', '--local', dest='dest',  action='store_const', const='local', default='local')
    group.add_argument('-r', '--remote', dest='dest', action='store_const', const='remote')
    group.add_argument('-c', '--cache' )
    whsp.add_argument('-F', '--force', default=False, action='store_true',
                      help='Force re-creation of files that already exist')
    whsp.add_argument('-D', '--dir', default = '', help='Set directory, instead of configured Warehouse filesystem dir, for relative paths')

    whsp = whp.add_parser('config', help='Configure varibles')
    whsp.set_defaults(subcommand='config')
    whsp.add_argument('-v', '--var', help="Name of the variable. One of'local','remote','title','about' ")
    whsp.add_argument('term', type=str, nargs = '?', help='Value of the variable')

    whsp = whp.add_parser('doc', help='Build documentation')
    whsp.set_defaults(subcommand='doc')
    group = whsp.add_mutually_exclusive_group()
    group.add_argument('-l', '--local', dest='dest',  action='store_const', const='local', default='local')
    group.add_argument('-r', '--remote', dest='dest', action='store_const', const='remote')
    group.add_argument('-c', '--cache' )
    whsp.add_argument('-D', '--dir', default='',
                      help='Set directory, instead of configured Warehouse filesystem dir, for relative paths')
    whsp.add_argument('-F', '--force', default=False, action='store_true',
                      help='Force re-creation of files that already exist')

    whsp = whp.add_parser('remove', help='Remove a bundle or partition from a warehouse')
    whsp.set_defaults(subcommand='remove')
    whsp.add_argument('term', type=str,help='Name of bundle, partition, manifest or database')

    whsp = whp.add_parser('connect', help='Test connection to a warehouse')
    whsp.set_defaults(subcommand='connect')

    whsp = whp.add_parser('info', help='Configuration information')
    whsp.set_defaults(subcommand='info')   
 
    whsp = whp.add_parser('drop', help='Drop the warehouse database')
    whsp.set_defaults(subcommand='drop')   
 
    whsp = whp.add_parser('create', help='Create required tables')
    whsp.set_defaults(subcommand='create')

    whsp = whp.add_parser('index', help='Create an Index webpage for a warehouse')
    whsp.set_defaults(subcommand='index')
    whsp.add_argument('term', type=str, help="Cache's root URL must have a 'meta' subdirectory")

    whsp = whp.add_parser('users', help='Create and configure warehouse users')
    whsp.set_defaults(subcommand='users')  
    group = whsp.add_mutually_exclusive_group()
    group.add_argument('-L', '--list', dest='action',  action='store_const', const='list')
    group.add_argument('-a', '--add' )
    group.add_argument('-d', '--delete')

    whsp.add_argument('-p', '--password')

       
    whsp = whp.add_parser('list', help='List the datasets in the warehouse')
    whsp.set_defaults(subcommand='list')   
    whsp.add_argument('term', type=str, nargs='?', help='Name of bundle, to list partitions')
    group = whsp.add_mutually_exclusive_group()
    group.add_argument('-m', '--manifests',   action='store_true', help='List manifests')
    group.add_argument('-d', '--databases', action='store_true', help='List Databases')
    group.add_argument('-p', '--partitions',   action='store_true', help='List partitions')

    if IN_DEVELOPMENT:
        whsp = whp.add_parser('test', help='Run a test')
        whsp.set_defaults(subcommand='test')
        whsp.add_argument('term', type=str, nargs='?', help='A test argument')

def warehouse_info(args, w,config):



    prt("Warehouse Info")
    prt("Name:     {}",args.name)
    prt("Class:    {}",w.__class__)
    prt("Database: {}",w.database.dsn)
    prt("WLibrary: {}",w.wlibrary.database.dsn)
    prt("ELibrary: {}",w.elibrary.database.dsn)

def warehouse_remove(args, w,config):
    from functools import partial
    from ambry.util import init_log_rate

    #w.logger = Logger('Warehouse Remove',init_log_rate(prt,N=2000))
    
    w.remove(args.term )
      
def warehouse_drop(args, w,config):

    w.delete()
 
def warehouse_create(args, w,config):
    
    w.database.enable_delete = True
    try:
        w.library.clean()
        w.drop()
    except:
        pass # Can't clean or drop if doesn't exist
    
    w.create()
    w.library.database.create()
    
def warehouse_users(args, w,config):

    if args.action == 'list' or ( not bool(args.delete) and not bool(args.add)):
        for name, values in w.users().items():
            prt("{} id={} super={}".format(name, values['id'], values['superuser']))
    elif bool(args.delete):
        w.drop_user(args.delete)   
    elif bool(args.add):
        w.create_user(args.add, args.password)

    #w.configure_default_users()
    
def warehouse_list(args, w, config):    


    if not w:
        if args.databases:
            # List all of the warehouses referenced in the library
            from ..library import new_library

            l = new_library(config.library(args.library_name))

            for s in l.stores:
                print "{:10s} {:25s} {}".format(s.ref, s.data['title'], s.data['summary'] )


                print "{:10s} {:25s} dsn =    {}".format('','',s.path)

                if s.data['local_cache']:
                    print "{:10s} {:25s} local =  {}".format('', '', s.data['local_cache'])

                if s.data['remote_cache']:
                    print "{:10s} {:25s} remote = {}".format('', '', s.data['remote_cache'])



            return

        else:

            # List all of the manifests referenced in the library
            from ..library import new_library
            l = new_library(config.library(args.library_name))

            for f, m in l.manifests:
                print "{:10s} {:25s}| {}".format(m.uid, m.title, m.summary['text'])

            return


    l = w.library

    if not args.term:

        _print_bundle_list(w.list(),fields=['vid','vname'],show_partitions=False)
            
    else:
        raise NotImplementedError()
        d, p = l.get_ref(args.term)
                
        _print_info(l,d,p, list_partitions=True)

def warehouse_install(args, w ,config):
    from ambry.warehouse.manifest import Manifest

    m = Manifest(args.term)

    if args.clean:
        w.clean()
        w.create()

    if args.name_only:
        from ambry.warehouse import NullLogger
        w.logger = NullLogger()

    w.logger.info("Installing to {}".format(w.database.dsn))

    w.install_manifest(m, reset = args.reset_config)

    w.logger.info("Installed to {}".format(w.database.dsn))

    l = w.elibrary

    l.sync_warehouse(w)

    if args.name_only:
        print w.database.dsn

    if args.dest or args.cache:
        warehouse_extract(args, w, config)

    if args.doc:
        warehouse_doc(args, w, config)

def get_cache(w, args, rc):
    from ..dbexceptions import ConfigurationError
    from ambry.cache import new_cache, parse_cache_string
    import os.path

    if args.cache:
        c_string = args.cache

    elif args.dest == 'local':

        c_string = w.local_cache

        if not c_string:
            raise ConfigurationError(
                "For extracts, must set an extract location, either in the manifest or the warehouse")

        # Join will return c_string if c_string is an absolute path
        c_string = os.path.join(rc.filesystem('warehouse')['dir'], c_string).replace('//','/')

    elif args.dest == 'remote':
        c_string = w.remote_cache

    else:
        raise ConfigurationError("Must specify a cahce name, or local or remote. ")


    config = parse_cache_string(c_string, root_dir=args.dir)

    if not config:
        raise ConfigurationError("Failed to parse cache spec: '{}'".format(c_string))

    if args.dir and config['type'] == 'file' and not os.path.isabs(config['dir']):
        config['dir'] = os.path.join(args.dir, config['dir'])

    if config['type'] == 'file' and not os.path.exists(config['dir']):
        os.makedirs(config['dir'])

    cache = new_cache(config, run_config=rc)

    return cache

def warehouse_extract(args, w, config):


    cache = get_cache(w, args, config)

    w.logger.info("Extracting to: {}".format(cache))

    extracts = w.extract(cache, force=args.force)

    for extract in extracts:
        print extract

def warehouse_doc(args, w, config):

    from ..text import Renderer
    import os.path


    cache = get_cache(w, args, config)

    cache.prefix = os.path.join(cache.prefix, 'doc')

    w.logger.info("Extracting to: {}".format(cache))

    r = Renderer(cache, warehouse = w)

    path, extracts = r.write_library_doc(force=args.force)

    print path


def warehouse_config(args, w, config):
    from ..dbexceptions import ConfigurationError

    if not args.var in w.configurable:
        raise ConfigurationError("Value {} is not configurable. Must be one of: {}".format(args.var, w.configurable))

    if args.term:
        setattr(w, args.var, args.term)

    print getattr(w, args.var)

def warehouse_test(args, w, config):
    from ..dbexceptions import ConfigurationError
    from ..util import print_yaml




