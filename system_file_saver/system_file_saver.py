#!/usr/bin/env python3

from sys import exit  # Cleanly exit program
from subprocess import call  # Access external programs
from socket import gethostname  # Get the computer's name
from os import devnull  # Allow piping to /dev/null
# Check that files and directories exist, expand ~ in names, normalize a path,
# and split paths into components
from os.path import isfile, isdir, expanduser, normpath, split


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
        with open(input_file, 'r') as f:
            for line in f:
                l = line.strip()  # Strip newlines
                # Skip comments and blank lines
                if line.startswith('#') or not line or line == '\n':
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
            while newpath != '/':
                tmpset.add(newpath)
                newpath = split(newpath)[0]

        # Take the union of our sets
        self.files = self.files.union(tmpset)

    def __iter__(self):
        """ Returns the iterator from self.files """
        return self.files.__iter__()


class Rsyncer:
    """ A class to handle running rsync """
    def __init__(self, rsync_loc, file_list, target_directory, hostname, verbosity, flags=set()):
        self.rsync_loc = rsync_loc
        self.file_list = file_list
        self.target_directory = target_directory
        self.hostname = hostname
        self.verbosity = verbosity
        self.flags = ' '.join(flags)

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
        verb = ''
        if self.verbosity >= 2:
            verb = "--verbose"
        elif self.verbosity == 0:
            verb = "--quiet"

        # Build command
        self.command = [
            self.rsync_loc,
            verb,
            "--archive",
            ]

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
        full_target = normpath(self.target_directory + '/' + self.hostname)
        self.command.append(full_target)
        com = ' '.join(self.command)
        #print(com)
        if verbosity >= 1:
            call(com, shell=True)
        else:
            call(com, stdout=open(devnull, 'wb'), shell=True)


##### START OF CODE
if __name__ == '__main__':

    # Allows command line options to be parsed.
    from optparse import OptionParser  # Command line parsing

    usage = "usage: %prog [Options]"
    version = "%prog Version 1.0\n\nCopyright (C) 2013 Alexander Gude - alex.public.account+systemfilesaver@gmail.com\nThis is free software.  You may redistribute copies of it under the terms of\nthe GNU General Public License <http://www.gnu.org/licenses/gpl.html>.\nThere is NO WARRANTY, to the extent permitted by law.\n\nWritten by Alexander Gude."
    parser = OptionParser(usage=usage, version=version)
    parser.add_option("-f", "--input-file", action="store", type="str", dest="input_file", default="~/.systemfiles/systemfile_list.txt", help="input file containing a list of files to backup, one per line [~/.systemfiles/systemfile_list.txt]")
    parser.add_option("-t", "--target-directory", action="store", type="str", dest="target_directory", default="~/.systemfiles/", help="target folder for saving systemfiles [~/.systemfiles/]")
    parser.add_option("-o", "--hostname", action="store", type="str", dest="hostname", default=None, help="files are saved in target_directory/hostname/ [$HOSTNAME]")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="print some extra status messages to stdout [false]")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="do not print any messages to stdout [false]")
    parser.add_option("--dry-run", action="store_true", dest="dry_run", default=False, help="run rsync with --dry-run [false]")
    parser.add_option("--itemize-changes", action="store_true", dest="itemize_changes", default=False, help="run rsync with --itemize-changes [false]")
    parser.add_option("--checksum", action="store_true", dest="checksum", default=False, help="run rsync with --checksum [false]")
    parser.add_option("--delete-after", action="store_true", dest="delete_after", default=False, help="run rsync with --delete-after [false]")

    (options, args) = parser.parse_args()

    # Set verbosity
    verbosity = 1
    if options.quiet:
        verbosity = 0
    elif options.verbose:
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
    if options.hostname is None:
        options.hostname = gethostname()

    # Set up extra flags
    flags = []
    if options.dry_run:
        flags.append("--dry-run")
    if options.itemize_changes:
        flags.append("--itemize-changes")
    if options.checksum:
        flags.append("--checksum")
    if options.delete_after:
        flags.append("--delete-after")

    # Expand the input directory and file
    options.target_directory = expanduser(options.target_directory)
    options.input_file = expanduser(options.input_file)

    # Set up and run rsync
    fl = FileList(options.input_file, verbosity)
    rs = Rsyncer(rsync_loc, fl, options.target_directory, options.hostname, verbosity, flags)
