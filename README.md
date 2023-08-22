# KiCad 7 configuration checker

This is a CLI Python3 program to check a user's configuration and emit diagnostics

Requires Python3 module sexpdata. If you do not have it, install with

```sh
pip3 install sexpdata
```

Takes an optional argument to specify the configuration directory which overrides the default for the platform.

## Usage

```
python3 kicad7cfgchk.py [-h] [-a] [-v] [directory]

Check a user's KiCad7 configuration and emit diagnostics

positional arguments:
  directory      Configuration directory

optional arguments:
  -h, --help     show this help message and exit
  -a, --all      show all diagnostics for tables (default: errors only)
  -v, --version  show version
```

## To do

Check if it works on OS/X and Windows with the paths in code

## Author

* **Ken Yap**

## License

See the [LICENSE](LICENSE.md) file for license rights and limitations (MIT).
