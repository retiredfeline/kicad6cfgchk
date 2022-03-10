#!/usr/bin/env python3

"""Check a user's KiCad6 configuration and emit diagnostics"""

import sys
import argparse
import pathlib
import re
import json
import sexpdata


VERSION = '2022-03-11'  # today's date
SYM_LIB_TABLE = {'name': 'sym_lib_table', 'file': 'sym-lib-table',
                 'var': 'KICAD6_SYMBOL_DIR', 'path': ''}
FP_LIB_TABLE = {'name': 'fp_lib_table', 'file': 'fp-lib-table',
                'var': 'KICAD6_FOOTPRINT_DIR', 'path': ''}
ENVVAR_RE = re.compile(r'(\$\{(\w+)\})', re.A)
ARGS = None


def platform_defaults():
    """Set table paths and return configuration directory for current platform"""
    home = pathlib.Path.home()
    if sys.platform == 'linux':
        cfgdir = home / '.config' / 'kicad' / '6.0'
        SYM_LIB_TABLE['path'] = '/usr/share/kicad/symbols'
        FP_LIB_TABLE['path'] = '/usr/share/kicad/footprints'
    else:
        # To do: platforms other than Linux
        sys.exit('Other platforms coming soon')
    return str(cfgdir)


def chk_kicad_common(cfgdir):
    """Read in kicad_common.json and check it"""
    kicad_common = str(pathlib.Path(cfgdir) / 'kicad_common.json')
    print(f'Checking {kicad_common}\n')
    envvars = {}
    try:
        with open(kicad_common) as filehandle:
            try:
                objects = json.load(filehandle)
            except json.JSONDecodeError:
                print(f'Cannot parse {kicad_common}')
    except IOError:
        print(f'Cannot open {kicad_common}')
        return envvars
    environment = objects['environment']
    envvars = environment['vars']
    for key in envvars:
        value = envvars[key]
        print(f'{key}={value}')
    print(f'')
    return envvars


def todict(lib):
    """Convert S-exprs to dictionary for easier processing"""
    if sexpdata.car(lib).value() != 'lib':
        return {}
    libi = {}
    tail = sexpdata.cdr(lib)
    while tail:
        pair = sexpdata.car(tail)
        libi[pair[0].value()] = pair[1]
        tail = sexpdata.cdr(tail)
    return libi


def sub_env_var(uri, envvars):
    """Substitute any environment variables found"""
    match = ENVVAR_RE.search(uri)
    if not match:  # no environment variable in uri
        return uri
    old = match.group(1)
    envvar = match.group(2)
    if not envvar in envvars:
        print(f'Undefined environment variable {old} in {uri}')
    else:
        new = envvars[envvar]
        uri = uri.replace(old, new)
    return uri


def chk_one_sym_lib(lib, envvars):
    """Check one symbol library"""
    libi = todict(lib)
    if not libi or not 'name' in libi:
        print(f'{libi} is not a lib')
    if not 'uri' in libi:
        print(f'No uri for {libi["name"]}')
        return
    uri = sub_env_var(libi['uri'], envvars)
    path = pathlib.Path(uri)
    if not path.is_file():
        print(
            f'{libi["name"]} ({libi["type"]}) {libi["uri"]} not found')
    elif ARGS.allmsgs:
        print(f'{libi["name"]} ({libi["type"]}) {libi["uri"]} found')


def chk_one_fp_lib(lib, envvars):
    """Check one footprint library"""
    libi = todict(lib)
    if not libi or not 'name' in libi:
        print(f'{libi} is not a lib')
    if not 'uri' in libi:
        print(f'No uri for {libi["name"]}')
        return
    uri = sub_env_var(libi['uri'], envvars)
    path = pathlib.Path(uri)
    if not path.is_dir():
        print(
            f'{libi["name"]} ({libi["type"]}) {libi["uri"]} not found')
    elif ARGS.allmsgs:
        files = path.glob('*.kicad_mod')
        length = len(list(files))
        print(f'{libi["name"]} ({libi["type"]}) {libi["uri"]} found with {length} footprints')


def chk_lib_table(cfgdir, table_info, envvars):
    """Read in S-expr lib_table and check it"""
    lib_path = str(pathlib.Path(cfgdir) / table_info['file'])
    print(f'Checking {lib_path}\n')
    try:
        with open(lib_path) as filehandle:
            sexpr = sexpdata.load(filehandle, nil=None,
                                  true=None, false=None, line_comment=None)
    except IOError:
        print(f'Cannot open {lib_path}')
        return False
    table_name = sexpdata.car(sexpr)
    if table_name.value() != table_info['name']:
        print(f'{lib_path} is not a {table_info["name"]}')
        return False
    tail = sexpdata.cdr(sexpr)
    while tail:
        table_info['check_fn'](sexpdata.car(tail), envvars)
        tail = sexpdata.cdr(tail)
    print(f'')
    return True


def chk_cfg(cfgdir):
    """Check configuration in directory cfgdir"""
    envvars = chk_kicad_common(cfgdir)
    # add KiCad built-in envvars
    envvars.update({SYM_LIB_TABLE['var']: SYM_LIB_TABLE['path']})
    envvars.update({FP_LIB_TABLE['var']: FP_LIB_TABLE['path']})
    # Python has no function prototypes otherwise we could initialise at top
    SYM_LIB_TABLE['check_fn'] = chk_one_sym_lib
    FP_LIB_TABLE['check_fn'] = chk_one_fp_lib
    chk_lib_table(cfgdir, SYM_LIB_TABLE, envvars)
    chk_lib_table(cfgdir, FP_LIB_TABLE, envvars)


def main():
    """Main routine"""
    # pylint: disable=global-statement
    global ARGS
    cfgdir = platform_defaults()
    parser = argparse.ArgumentParser(
        description='Check a user\'s KiCad6 configuration and emit diagnostics')
    parser.add_argument('directory', nargs='?',
                        default=cfgdir, help='Configuration directory')
    parser.add_argument('-a', '--all', dest='allmsgs', action='store_true',
                        help='show all diagnostics for tables (default: errors only)')
    parser.add_argument('-v', '--version', dest='version', action='store_true',
                        help='show version')
    ARGS = parser.parse_args()
    if ARGS.version:
        print(f'{VERSION}')
        return
    try:
        chk_cfg(ARGS.directory)
    except IOError:
        print(f"Cannot process {ARGS.directory}")


if __name__ == '__main__':
    main()
