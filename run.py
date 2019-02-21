import os
import argparse

from express import ExPrESS

from utils import find_file, write_json
from logger import configure_logger, logger
from settings import PROPERTIES, ESPRESSO_XML_FILE, VASP_XML_FILE


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action="store_true", help="enable debugging")
    parser.add_argument('-w', '--work-dir', dest="work_dir", help='full path to working directory')
    parser.add_argument('-s', '--stdout-file', dest="stdout_file", help='full path to standard output file')
    return parser.parse_args()


def get_parser_name(work_dir):
    if find_file(VASP_XML_FILE, work_dir): return "vasp"
    if find_file(ESPRESSO_XML_FILE, work_dir): return "espresso"


def get_express(work_dir, stdout_file):
    kwargs = {
        "work_dir": work_dir,
        "stdout_file": stdout_file
    }
    parser_name = get_parser_name(work_dir)
    if not parser_name: raise Exception('unable to parse directory!')
    return ExPrESS(parser_name, **kwargs)


def safely_extract_property(express_, property_, *args, **kwargs):
    try:
        return express_.property(property_, *args, **kwargs)
    except:
        logger.error("unable to extract {}".format(property_))


def extract_properties(express_):
    exabyte_dir = os.path.join(args.work_dir, "exabyte")
    if not os.path.exists(exabyte_dir): os.makedirs(exabyte_dir)

    # extract initial structure
    initial_structure = safely_extract_property(express_, "initial_structure", is_initial_structure=True)
    initial_structure_path = os.path.join(exabyte_dir, ".".join(("initial_structure", "json")))
    if initial_structure: write_json(initial_structure_path, initial_structure)

    # extract final structure
    final_structure = safely_extract_property(express_, "final_structure", is_final_structure=True)
    final_structure_path = os.path.join(exabyte_dir, ".".join(("final_structure", "json")))
    if final_structure: write_json(final_structure_path, final_structure)

    # extract other properties
    for property_name in PROPERTIES:
        property_path = os.path.join(exabyte_dir, ".".join((property_name, "json")))
        property_ = express_.property(property_name)
        if property_: write_json(property_path, property_)


if __name__ == '__main__':
    args = parse_arguments()
    configure_logger(args.debug)
    extract_properties(get_express(args.work_dir, args.stdout_file))
