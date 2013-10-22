# System File Saver

System File Saver (SFS) is a python3 script that backs up designated system files on
your computer. It preserves the directory structure of the backup, making it
easy to put the files back in the right place when restoring them.

## Usage

If the program is called as follows:

    systemfilesaver.py -h

It will provide the following usage guide:

    Usage: systemfilesaver.py [Options]

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -f INPUT_FILE, --input-file=INPUT_FILE
                            input file containing a list of files to backup, one
                            per line [~/.systemfiles/systemfile_list.txt]
      -t TARGET_DIRECTORY, --target-directory=TARGET_DIRECTORY
                            target folder for saving systemfiles [~/.systemfiles/]
      -o HOSTNAME, --hostname=HOSTNAME
                            files are saved in target_directory/hostname/
                            [$HOSTNAME]
      -v, --verbose         print some extra status messages to stdout [false]
      -q, --quiet           do not print any messages to stdout [false]
      --dry-run             run rsync with --dry-run [false]
      --itemize-changes     run rsync with --itemize-changes [false]
      --checksum            run rsync with --checksum [false]
      --delete-after        run rsync with --delete-after [false]

The simplest usage case is:

    systemfilesaver.py

This will backup all files listed in `~/.systemfiles/systemfile_list.txt` to `~/.systemfiles/$HOSTNAME`.

## systemfile_list.txt

SFS reads a file list to determine what system files to backup. Here is an example list:

    # Backup /etc/fstab
    /etc/fstab

    # Backup sshd_config
    /etc/ssh/sshd_config

Blank lines, and lines that begin with a # are ignored. # symbols are *only*
allowed at the beginning of a line; they are not treated as comments if placed
after a file. For example: `/etc/fstab # Backup harddrive mount locations` is
*illegal*.

Currently SFS only supports backing up files, not whole directories. If you
want multiple files in a directory backed up, list each one separately.

## Example Directory Structure

Running `systemfilesaver.py` with the example `systemfile_list.txt` listed
above on a machine with the hostname `desktop` would generate the following
directory structure in `~/.systemfiles`:

    .systemfiles/
    ├── desktop/
    │   └── etc/
    │       ├── fstab
    │       └── ssh
    │           └── sshd_config
    └── systemfile_list.txt

