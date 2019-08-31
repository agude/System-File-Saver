#!/usr/bin/env python3

import argparse
from os import devnull
from os.path import isfile, isdir, expanduser, normpath, split
from socket import gethostname
from subprocess import call
import logging


class FileList:
    """ A class to handle the input list of files """

    def __init__(self, input_file, verbosity):
        """ Read the input_file for files to backup, check that they exist, and
        add them to a list """
        self.input_file = input_file
        self.files = set()  # Doesn't allow duplicates
        self.verbosity = verbosity

        # Check the input file
        if not isfile(input_file):
            if self.verbosity >= 1:
                exit("Input file list not found!")
            else:
                exit(1)

        # Collect filenames to backup, but only if they are existent files
        with open(input_file, "r") as f:
            for line in f:
                l = line.strip()  # Strip newlines
                # Skip comments and blank lines
                if line.startswith("#") or not line or line == "\n":
                    continue
                if isfile(l):
                    self.files.add(line)
                else:
                    if self.verbosity >= 1:
                        print(line, " is not a valid file!")

        # Split files
        self.__split()

    def __split(self):
        """
        Split the files in self.files such that "/etc/ssh/sshd_config" becomes
        three entries:

        "/etc", "/etc/ssh", "/etc/ssh/sshd_config"
        """
        tmpset = set()
        for f in self.files:
            # Add all subpaths leading to the file
            newpath = split(f)[0]
            while newpath != "/":
                tmpset.add(newpath)
                newpath = split(newpath)[0]

        # Take the union of our sets
        self.files = self.files.union(tmpset)

    def __iter__(self):
        """ Returns the iterator from self.files """
        return self.files.__iter__()


class Rsyncer:
    """ A class to handle running rsync """

    def __init__(
        self, rsync_loc, file_list, target_directory, hostname, verbosity, flags=set()
    ):
        self.rsync_loc = rsync_loc
        self.file_list = file_list
        self.target_directory = target_directory
        self.hostname = hostname
        self.verbosity = verbosity
        self.flags = " ".join(flags)

        # Check output directory
        if not isdir(self.target_directory):
            if verbosity >= 1:
                exit("Target directory not found!")
            else:
                exit(1)

        # Build command
        self.__buildCommand()

    def __buildCommand(self):
        """ Build the rsync command that will be called. """
        # Set verbosity
        verb = ""
        if self.verbosity >= 2:
            verb = "--verbose"
        elif self.verbosity == 0:
            verb = "--quiet"

        # Build command
        self.command = [self.rsync_loc, verb, "--archive"]

        # Add in the extra flags
        self.command.append(self.flags)

        # Get files
        for f in self.file_list:
            self.command.append("--include={file_name}".format(file_name=f.strip()))

        # Exclude all files not specifically included
        self.command.append("--exclude='*'")

        # Set the source to root
        self.command.append("/")

        # Set up target directory
        full_target = normpath(self.target_directory + "/" + self.hostname)
        self.command.append(full_target)
        com = " ".join(self.command)
        # print(com)
        if verbosity >= 1:
            call(com, shell=True)
        else:
            call(com, stdout=open(devnull, "wb"), shell=True)


def main():
    parser = argparse.ArgumentParser(
        prog="System File Saver", description="Backup files in Linux"
    )
    parser.add_argument(
        "-f",
        "--input-file",
        type="str",
        dest="input_file",
        default="~/.systemfiles/systemfile_list.txt",
        help="input file containing a list of files to backup, one per line [~/.systemfiles/systemfile_list.txt]",
    )
    parser.add_argument(
        "-t",
        "--target-directory",
        type="str",
        dest="target_directory",
        default="~/.systemfiles/",
        help="target folder for saving systemfiles [~/.systemfiles/]",
    )
    parser.add_argument(
        "-o",
        "--hostname",
        type="str",
        dest="hostname",
        default=None,
        help="files are saved in target_directory/hostname/ [$HOSTNAME]",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        default=False,
        help="print some extra status messages to stdout [false]",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        dest="quiet",
        default=False,
        help="do not print any messages to stdout [false]",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        default=False,
        help="run rsync with --dry-run [false]",
    )
    parser.add_argument(
        "--itemize-changes",
        action="store_true",
        dest="itemize_changes",
        default=False,
        help="run rsync with --itemize-changes [false]",
    )
    parser.add_argument(
        "--checksum",
        action="store_true",
        dest="checksum",
        default=False,
        help="run rsync with --checksum [false]",
    )
    parser.add_argument(
        "--delete-after",
        action="store_true",
        dest="delete_after",
        default=False,
        help="run rsync with --delete-after [false]",
    )

    args = parser.parse_args()

    # Set verbosity
    verbosity = 1
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2

    # Check if rsync exists
    from distutils.spawn import find_executable

    rsync_loc = find_executable("rsync")
    if rsync_loc is None:
        if verbosity >= 1:
            exit("Can not find rsync.")
        else:
            exit(1)

    # Set up the hostname
    if args.hostname is None:
        args.hostname = gethostname()

    # Set up extra flags
    flags = []
    if args.dry_run:
        flags.append("--dry-run")
    if args.itemize_changes:
        flags.append("--itemize-changes")
    if args.checksum:
        flags.append("--checksum")
    if args.delete_after:
        flags.append("--delete-after")

    # Expand the input directory and file
    args.target_directory = expanduser(args.target_directory)
    args.input_file = expanduser(args.input_file)

    # Set up and run rsync
    fl = FileList(args.input_file, verbosity)
    rs = Rsyncer(rsync_loc, fl, args.target_directory, args.hostname, verbosity, flags)


if __name__ == "__main__":
    main()
