# onsub.py
[onsub.py v0.9](https://bitbucket.org/sawolford/onsub.git)
## Summary
The onsub.py command iterates over subfolders to execute arbitrary commands as dictated by command line arguments and a Python configuration file. The main code consists of two (2) Python files: an example Python-configuration file that is meant to be user configurable and the onsub.py script that executes commands as dictated by command line arguments and the configuration file.

All provided files, with a short description, are:

	- onsub.py            -- the main execution code (~400 lines)
	- onsub               -- very short python script that calls onsub.py
	- pushd.py            -- implements shell-like pushd capability (borrowed)
	- example,onsub.py    -- config file that implements hg, git, svn behavior
	- guestrepo2onsub.py  -- converter from guestrepo to onsub syntax
	- onsub2file.py       -- prints to stdout a file listing of prioritized folders 
	- README.md           -- this file
The configuration file is described later but it is organized into sections and provides rules for operation. The `onsub` command can be run in two main modes: file mode and recurse mode.

The first mode of operation is file mode, where a special file is provided indicating which subfolders are to be visited and, optionally, information about how to create them if they are missing. If a command is provided and this triggers folder creation because an expected folder is not present, then the folder creation is run serially to ensure that the expected `onsub` command has a folder to execute in. If no command is provided (i.e., noop) and an expected folder is not present, then the folder creations will be run in parallel if possible. If the creation operations cannot be run in parallel, then the creation operations can be mutually dependent if necessary and if specified in the proper order.

File mode is indicated by the `--file FILE` command line argument. The `FILE` parameter indicates the input file of expected folders, grouped by section (described below)) and, optionally, additional arguments for each expected folder. If the `--noop` command line argument is provided, then this mode can be used to construct all of the folders described by `FILE` in parallel according to rules for the corresponding section in the configuration file.  Example:

	git = [
		("./onsub", "https://bitbucket.org/sawolford/onsub.git"),
	]

The second mode of operation is recurse mode, where the filesystem is recursively searched, infinitely or up to a given depth. The configuration code is then queried for each folder in order to see if the `onsub` command should execute a command in that folder and how to do so. If the provided command indicates that variable substitution is necessary, the configuration file can also specify rules for how the command is constructed.

Recurse mode is indicated by the lack of a `--file FILE` command line argument. Instead of iterating over provided folder names, `onsub` instead recurses through the file system to generate folders. Example:

	$ onsub pwd
Both modes will execute commands according to the provided command line arguments. Extensive examples are provided at the end but some simple examples capture the main ways that commands are provided on the `onsub` command line. Examples:

	$ onsub --file input.py --noop   # constructs folders from input.py in parallel
	$ onsub --file input.py {remote} # constructs folders from input.py serially, then executes "{remote}" command in each
	$ onsub {cmd} status             # recurses to all subfolders and runs "{cmd} status"
	$ onsub pwd                      # recurses to all subfolders and runs "pwd"
## Configuration
The configuration file for `onsub` is nothing but a Python script, so it follows normal Python syntax rules. The code is interpreted by `onsub` as a color configuration list (`colors`), a default argument list (`arguments`), and a set of Python dictionaries, each of which is known as a section. The `colors` list instructs `onsub` how to colorize output. The `arguments` list contains arguments that are always passed to `onsub`. Each section is just a normal Python dictionary with keys and values. Sections are optional but, in the absence of extensive command line arguments, essentially required for onsub to do useful work.

The section names and most of the contents are arbitrary but are interpreted by `onsub` in such a way that work may be performed on file folders. Most dictionary keys in a section entry are completely arbitrary and will be passed to the Python `string.format()` function in order to construct shell commands. This formatting process is repeated a set number of times or until the string no longer changes. If a key is prefixed by `py:`, then the value is instead interpreted as a Python function whose arguments are prescribed for certain keys (described below) or just a list of remaining command line arguments.

Dictionary entry keys are interpreted specially by `onsub`:
#### - `py:enable`
Must evaluate directly to `True` or `False` (default: `False`). Indicates that the section is to be interpreted directly by `onsub`. Setting this to `False` can be used to construct  a composite section that is then enabled by itself. Example:

	git["py:enable"] = True
#### - `py:priority`
Python function taking three (3) arguments: `verbose`, `debug`, `path`. The first two are flags that can be used to control output. The last is the path that should be checked to see if the section applies. The current working directory context for this function call is also set to `path`. The function should return zero if the section does not apply and return a non-zero priority if the section applies. Required for any enabled section. Example:

	def gitpriority(verbose, debug, path): return 4 if os.path.exists(".git") else 0
#### - `py:makecommand`
Python function taking four (4) arguments: `verbose`, `debug`, `path`, `*rest`. The first two are flags that can be used to control output. The third is the path that does not exist and needs to be created. The last is a list for accepting a variable number of arguments. These variable arguments are taken from an input file (described later) and should typically contain additional instructions for constructing a missing folder. The function should return a string that evaluates to a shell command. This shell command may be executed in parallel if there is no other command provided to `onsub` (i.e., noop). Required if construction is requested and `py:makefunction` is not set (`py:makecommand` takes precedence over `py:makefunction`). Exanple:

	def gitmakecommand(verbose, debug, path, *rest):
		assert len(rest) >= 1
		url = rest[0]
		cmd = "git clone {url} {path}".format(url=url, path=path)
		if debug: print(cmd)
		return cmd
#### - `py:makefunction` 
Python function taking five (5) arguments: `verbose`, `debug`, `path`, `noexec`, `*rest`. The first two are flags that can be used to control output. The third is the path that does not exist and needs to be created. The fourth is a flag indicating that the function should not actually execute. The last is a list for accepting a variable number of arguments. These variable arguments are taken from an input file (described later) and should typically contain additional instructions for constructing a missing folder. The function should actually perform the necessary operation to construct a missing folder and should return a tuple consisting of an error code and an output string. This command will not be executed in parallel due to limitations of Python multiprocessing. Required if construction is requested and `py:makecommand` is not set. Example:

	def allmakefunction(verbose, debug, path, noexec, *rest):
		if verbose >=4: print("os.makedirs({path})".format(path=path))
		if noexec: return 0, "[noexec] os.makedirs({path})".format(path=path)
		os.makedirs(path)
		return 0, "os.makedirs({path})".format(path=path)
#### - string.format() strings
Other dictionary entries are strings that can contain Python variable substitution specifiers compatible with the Python `string.format()` standard method. Variables are substituted from the same section dictionary. This variable substitution is performed iteratively a set number of times or until the string no longer changes. Example:

	"cmd": "git"
	"-v": "-v"
	"remote": "{cmd} remote {-v}"
### Final configuration
Since the configuration file is just normal Python code, complex configurations can be constructed. Python allows a dictionary to be updated from another dictionary, where only keys in the other dictionary are replaced in the original. Checks against operating system type can be performed to alter behavior depending on the underlying OS. The resultant dictionary, if enabled, is the only one that will be interpreted by `onsub`. Example:

	git = {}
	git.update(default)
	git.update(gitdefault)
	if os.name == "nt": git.update(gitwindows)
	else: git.update(gitlinux)
	git["py:enable"] = True
The default configuration file is located at `${HOME}/.onsub.py`. A partially functional [example configuration file](https://bitbucket.org/sawolford/onsub/src/master/example,onsub.py) provides sample commands for [Git](https://git-scm.com/), [Mercurial](https://www.mercurial-scm.org/) and [Subversion](https://subversion.apache.org/). It also contains a section (named "all") that will allow operations on all subfolders regardless of type.

### Details
#### - Pseudo-section `colors`
Colors to use in colorized output. Commented lines indicate default values for each type of output.

Value:

	colors = {
	#     "path": "blue",
	#     "command": "cyan",
	#     "good": "green",
	#     "bad": "magenta",
	#     "error": "red",
	#     "partition": "yellow",
	}
Explanation:

	path       -- Folder where command is executed
	command    -- Command that is executed
	good       -- Output, if error code of command is zero
	bad        -- Output, if error code of command is non-zero
	error      -- Final output repeated for those commands with non-zero error code
	partition  -- Separator between normal output and repeated error output
#### - Pseudo-section `arguments`
Allows the same arguments to be passed to all invocations of `onsub`.

Value:

	arguments = [
		# "--count", "10",
		# "--debug",
		# "--disable", "all",
		# "--enable", "all",
		# "--file", "subs.py",
		# "--ignore", ".hg", "--ignore", ".git", "--ignore", ".svn",
		# "--nocolor",
		# "--noenable",
		# "--noexec",
		# "--nofile",
		# "--noignore",
		# "--noop",
		# "--py:closebrace", "%]",
		# "--py:enable", "py:enable",
		# "--py:makecommand", "py:makecommand",
		# "--py:makefunction", "py:makefunction",
		# "--py:openbrace", "%[",
		# "--py:priority", "py:priority",
		# "--sleepmake", ".1",
		# "--sleepcommand", "0",
		# "--suppress",
		# "--verbose", "5",
		# "--workers", "8",
	]
#### - Pseudo-section `default`
The example `default` section provides some sample Linux commands and a sample Python operation function.
##### `default` summary
	fileCheck   -- Python helper function that checks if a file exists in a folder
	defdefault  -- Pseudo-section used by default for all OSs
	deflinux    -- Pseudo-section used by default for Linux
	defwindows  -- Pseudo-section used by default for Windows
	default     -- Pseudo-section used by later sections
##### `default` Linux
Composite:

	default = {
        py:fileCheck = <function fileCheck at 0x108c0f710>
        echo = /bin/echo
        lswcl = ls | wc -l
        cwd = <current working directory>
	}
Explanation:

	py:fileCheck  -- Python helper function that checks if a file exists in a folder
	echo          -- Path to echo command
	lswcl         -- Executes ls and counts the number of lines
	cwd           -- Python f-string that evaluates to the current working directory
##### `default` details
	def fileCheck(verbose, debug, path, noexec, *args):
		if len(args) != 1: return 1, "fileCheck: wrong number of arguments"
		fname = args[0]
		if verbose >= 4: print("os.path.exists({fname})".format(fname=fname))
		if noexec: return 0, "[noexec] py:fileCheck"
		exists = os.path.exists(fname)
		fpath = "{path}/{fname}".format(path=path, fname=fname)
		if exists: return 0, "{fpath} exists".format(fpath=fpath)
		return 1, "{fpath} does not exist".format(fpath=fpath)
	
	defdefault = {
		"py:fileCheck": fileCheck,
		"cwd": f"{os.getcwd()}",
	}
	
	deflinux = {
		"sep": ";",
		"echo": "/bin/echo",
		"lswcl": "ls | wc -l",
	}
	
	defwindows = {
		"sep": "&",
	}
	
	default = {}
	default.update(defdefault)
	if os.name =="nt": default.update(defwindows)
	else: default.update(deflinux)
#### - Section `git`
The example `git` section provides sample `git` commands.
##### `git` summary
	gitmakecommand  -- Python helper function that makes a git clone
	gitpriority     -- Python helper function checks if folder is a git folder
	gitdefault      -- Pseudo-section for all OSs for git
	gitlinux        -- Pseudo-section for all Linux for git
	gitwindows      -- Pseudo-section for all Windows for git
	git             -- Configuration section for git
##### `git` Linux
Composite:

	git = {
		py:fileCheck = <function fileCheck at 0x107f2d710>
		cwd = <cwd>
		sep = ;
		echo = /bin/echo
		lswcl = ls | wc -l
		py:priority = <function gitpriority at 0x107f2d830>
		py:makecommand = <function gitmakecommand at 0x107f2d7a0>
		cmd = git
		write = {cmd} ci -a
		get = {cmd} pull
		put = {cmd} push
		remote = {cmd} remote -v
		allremote = {remote}
		py:enable = True
	}
Explanation:

	py:fileCheck    -- Inherited from default pseudo-section
	cwd             -- Inherited from default pseudo-section
	sep             -- Inherited from default pseudo-section
	echo            -- Inherited from default pseudo-section
	lswcl           -- Inherited from default pseudo-section
	py:priority     -- Python function that establishes a folder applies to this section
	py:makecommand  -- Python function that returns a shell command for cloning git folder
	cmd             -- String that tells how to execute git
	write           -- Command alias
	get             -- Command alias
	put             -- Command alias
	remote          -- Command alias
	allremote       -- Command alias
	py:enable       -- Python flag indicating that this section is enabled by default
##### `git` details
	def gitmakecommand(verbose, debug, path, *rest):
		assert len(rest) >= 1
		url = rest[0]
		cmd = "git clone {url} {path}".format(url=url, path=path)
		if debug: print(cmd)
		return cmd
	
	def gitpriority(verbose, debug, path): return 4 if os.path.exists(".git") else 0
	
	gitdefault = {
		"py:priority": gitpriority, 
		"py:makecommand": gitmakecommand,
		"cmd": "git",
		"write": "{cmd} ci -a",
		"get": "{cmd} pull",
		"put": "{cmd} push",
		"remote": "{cmd} remote -v",
		"allremote": "{remote}",
	}
	
	gitlinux = {}
	gitwindows = {}
	
	git = {}
	git.update(default)
	git.update(gitdefault)
	if os.name == "nt": git.update(gitwindows)
	else: git.update(gitlinux)
	git["py:enable"] = True
#### - Section `hg`
The example `hg` section provides sample `hg` commands.
##### `hg` summary
	hgmakecommand  -- Python helper function that makes a hg clone
	hgpriority     -- Python helper function checks if folder is a hg folder
	hgdefault      -- Pseudo-section for all OSs for hg
	hglinux        -- Pseudo-section for all Linux for hg
	hgwindows      -- Pseudo-section for all Windows for hg
	hg             -- Configuration section for hg
##### `hg` Linux
Composite:

	hg = {
		py:fileCheck = <function fileCheck at 0x108cba710>
		cwd = <cwd>
		sep = ;
		echo = /bin/echo
		lswcl = ls | wc -l
		py:priority = <function hgpriority at 0x108cba9e0>
		py:makecommand = <function hgmakecommand at 0x108cba8c0>
		cmd = hg
		write = {cmd} ci
		get = {cmd} pull --update
		put = {cmd} push
		remote = {echo} -n "default = "; {cmd} paths default
		allremote = {remote}; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull
		py:enable = True
	}
Explanation:

	py:fileCheck    -- Inherited from default pseudo-section
	cwd             -- Inherited from default pseudo-section
	sep             -- Inherited from default pseudo-section
	echo            -- Inherited from default pseudo-section
	lswcl           -- Inherited from default pseudo-section
	py:priority     -- Python function that establishes a folder applies to this section
	py:makecommand  -- Python function that returns a shell command for cloning hg folder
	cmd             -- String that tells how to execute hg
	write           -- Command alias
	get             -- Command alias
	put             -- Command alias
	remote          -- Command alias
	allremote       -- Command alias
	py:enable       -- Python flag indicating that this section is enabled by default
##### `hg` details
	def hgmakecommand(verbose, debug, path, *rest):
		assert len(rest) >= 1
		rrev = ""
		if len(rest) >= 2: rrev = "-r {rev}".format(rev=rest[1])
		url = rest[0]
		cmd = "hg clone {url} {path} {rrev}".format(url=url, path=path, rrev=rrev)
		if debug: print(cmd)
		return cmd
	
	def hgpriority(verbose, debug, path): return 3 if os.path.exists(".hg") else 0
	
	hgdefault =  {
		"py:priority": hgpriority,
		"py:makecommand": hgmakecommand,
		"cmd": "hg",
		"py:write": hgwrite,
		"write": "{cmd} ci",
		"get": "{cmd} pull --update",
		"put": "{cmd} push",
	}
	
	hglinux = {
		"remote": '{echo} -n "default = "; {cmd} paths default',
		"allremote": '{remote}; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull',
	}
	
	hgwindows = {
		"remote": '{cmd} paths default',
		"allremote": '{remote}; {cmd} paths default-push; {cmd} paths default-pull',
	}
	
	hg = {}
	hg.update(default)
	hg.update(hgdefault)
	if os.name == "nt": hg.update(hgwindows)
	else: hg.update(hglinux)
	hg["py:enable"] = True
#### - Section `svn`
The example `svn` section provides some sample Linux commands and a sample Python operation function.
##### `svn` summary
	svnmakecommand  -- Python helper function that makes a svn checkout
	svnpriority     -- Python helper function checks if folder is a svn folder
	svndefault      -- Pseudo-section for all OSs for svn
	svnlinux        -- Pseudo-section for all Linux for svn
	svnwindows      -- Pseudo-section for all Windows for svn
	svn             -- Configuration section for svn
##### `svn` Linux
Composite:

	svn = {
		py:fileCheck = <function fileCheck at 0x108b47710>
		cwd = <cwd>
		sep = ;
		echo = /bin/echo
		lswcl = ls | wc -l
		py:priority = <function svnpriority at 0x108b47b00>
		py:makecommand = <function svnmakecommand at 0x108b47a70>
		cmd = svn
		write = {cmd} [noop]
		get = {cmd} up
		put = {cmd} ci
		remote = {cmd} info --show-item url
		allremote = {remote}
		py:enable = True
	}
Explanation:

	py:fileCheck    -- Inherited from default pseudo-section
	cwd             -- Inherited from default pseudo-section
	sep             -- Inherited from default pseudo-section
	echo            -- Inherited from default pseudo-section
	lswcl           -- Inherited from default pseudo-section
	py:priority     -- Python function that establishes a folder applies to this section
	py:makecommand  -- Python function that returns a shell command for checking out svn folder
	cmd             -- String that tells how to execute svn
	write           -- Command alias
	get             -- Command alias
	put             -- Command alias
	remote          -- Command alias
	allremote       -- Command alias
	py:enable       -- Python flag indicating that this section is enabled by default
##### `svn` details
	def svnmakecommand(verbose, debug, path, *rest):
		assert len(rest) >= 1
		rev = "head"
		if len(rest) >= 2: rev = rest[1]
		url = rest[0]
		cmd = "svn checkout {url}@{rev} {path}".format(url=url, path=path, rev=rev)
		if debug: print(cmd)
		return cmd
	
	def svnpriority(verbose, debug, path): return 2 if os.path.exists(".svn") else 0
	
	svndefault = {
		"py:priority": svnpriority,
		"py:makecommand": svnmakecommand,
		"cmd": "svn",
		"write": "{cmd} [noop]",
		"get": "{cmd} up",
		"put": "{cmd} ci",
		"remote": "{cmd} info --show-item url",
		"allremote": "{remote}",
	}
	
	svnlinux = {}
	svnwindows = {}
	
	svn = {}
	svn.update(default)
	svn.update(svndefault)
	if os.name == "nt": svn.update(svnwindows)
	else: svn.update(svnlinux)
	svn["py:enable"] = True
#### - Section `all`
The example `all ` section provides some sample Linux commands and a sample Python operation function.
##### `all ` summary
	allmakecommand  -- Python helper function that makes a folder
	allpriority     -- Python helper function that returns True
	alldefault      -- Pseudo-section for all OSs 
	alllinux        -- Pseudo-section for all Linux
	allwindows      -- Pseudo-section for all Windows
	all             -- Configuration section for all folders
##### `all ` Linux
Composite:

	all = {
		py:fileCheck = <function fileCheck at 0x10507c710>
		cwd = <cwd>
		sep = ;
		echo = /bin/echo
		lswcl = ls | wc -l
		py:priority = <function allpriority at 0x10507cc20>
		py:makefunction = <function allmakefunction at 0x10507cb90>
	}
Explanation:

	py:fileCheck     -- Inherited from default pseudo-section
	cwd              -- Inherited from default pseudo-section
	sep              -- Inherited from default pseudo-section
	echo             -- Inherited from default pseudo-section
	lswcl            -- Inherited from default pseudo-section
	cwd              -- Inherited from default pseudo-section
	py:priority      -- Python function that establishes a folder applies to this section
	py:makefunction  -- Python function that makes a folder
##### `all ` details
	def allmakefunction(verbose, debug, path, noexec, *rest):
		if verbose >=4: print("os.makedirs({path})".format(path=path))
		if noexec: return 0, "[noexec] os.makedirs({path})".format(path=path)
		os.makedirs(path)
		return 0, "os.makedirs({path})".format(path=path)
	
	def allpriority(verbose, debug, path): return 1
	
	alldefault = {
		"py:priority": allpriority,
		"py:makefunction": allmakefunction,
	}
	
	alllinux = {}
	allwindows = {}
	
	all = {}
	all.update(default)
	all.update(alldefault)
	if os.name == "nt": all.update(allwindows)
	else: all.update(alllinux)
## Command line options
The basic command line options, with variable outputs specified by <>, are:

	usage: onsub [-h] [--chdir CHDIR] [--config CONFIG] [--configfile CONFIGFILE] [--count COUNT] [--debug] [--depth DEPTH]
				 [--disable DISABLE] [--dump DUMP] [--dumpall] [--enable ENABLE] [--file FILE] [--ignore IGNORE] [--invert]
				 [--nocolor] [--noenable] [--noexec] [--nofile] [--noignore] [--noop] [--py:closebrace PYCLOSEBRACE]
				 [--py:enable PYENABLE] [--py:makecommand PYMAKECOMMAND] [--py:makefunction PYMAKEFUNCTION]
				 [--py:openbrace PYOPENBRACE] [--py:priority PYPRIORITY] [--sleepmake SLEEPMAKE]
				 [--sleepcommand SLEEPCOMMAND] [--suppress] [--verbose VERBOSE] [--workers WORKERS]
				 ...
	
	walks filesystem executing arbitrary commands
	
	positional arguments:
  		rest
	
	optional arguments:
	  -h, --help                        show this help message and exit
	  --chdir CHDIR                     chdir first
	  --config CONFIG                   config option
	  --configfile CONFIGFILE           config file
	  --count COUNT                     count for substitutions
	  --debug                           debug flag
	  --depth DEPTH                     walk depth
	  --disable DISABLE                 disable section
	  --dump DUMP                       dump section
	  --dumpall                         dump all sections
	  --enable ENABLE                   enable section
	  --file FILE                       file with folder names
	  --ignore IGNORE                   ignore folder names
	  --invert                          invert error codes
	  --nocolor                         disables colorized output
	  --noenable                        no longer enable any sections
	  --noexec                          do not actually execute
	  --nofile                          ignore file options
	  --noignore                        ignore ignore options
	  --noop                            no command execution
	  --py:closebrace PYCLOSEBRACE      key for py:closebrace
	  --py:enable PYENABLE              key for py:enable
	  --py:makecommand PYMAKECOMMAND    key for py:makecommand
	  --py:makefunction PYMAKEFUNCTION  key for py:makefunction
	  --py:openbrace PYOPENBRACE        key for py:openbrace
	  --py:priority PYPRIORITY          key for py:priority
	  --sleepmake SLEEPMAKE             sleep between make calls
	  --sleepcommand SLEEPCOMMAND       sleep between command calls
	  --suppress                        suppress repeated error output
	  --verbose VERBOSE                 verbose level
	  --workers WORKERS                 number of workers
### -h, --help
	-h, --help                        show this help message and exit
Type: Flag<br>
Default: \<none><br>
Option: \<none><br>
Repeat: No<br><br>
Outputs command line options (see above).
### --chdir CHDIR
	--chdir CHDIR                     chdir first
Type: Option<br>
Default: \<none><br>
Option `CHDIR`<br>
Repeat: No<br><br>
Changes directory before execution.
### --config CONFIG
	--config CONFIG                   config option
Type: Option<br>
Default: None<br>
Option: `CONFIG`<br>
Repeat: Yes<br><br>
Appends `CONFIG` lines to configuration, one at a time. Can be used to alter configuration for a single command execution.
### --configfile CONFIGFILE
	--configfile CONFIGFILE           config file
Type: Option<br>
Default: \<home folder>/.onsub.py<br>
Option: `CONFIGFILE`<br>
Repeat: No<br><br>
Names `CONFIGFILE` to be the configuration file to be loaded.
### --count COUNT
	--count COUNT                     count for substitutions
Type: Option<br>
Default: 10<br>
Option: `COUNT`<br>
Repeat: No<br><br>
Indicates that `COUNT` is the maximum number of times to recursively substitute configuration entries to prevent infinite recursion.
### --debug
	--debug                           debug flag
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Causes `onsub` to output more diagnostic information. Is also passed to `py:` functions where they occur in configuration entries.
### --depth DEPTH
	--depth DEPTH                     walk depth
Type: Option<br>
Default: -1<br>
Option: `DEPTH`<br>
Repeat: No<br><br>
If greater than zero, limits the filesystem depth that is walked by `onsub` to folder entries with up to `DEPTH`-many subdirectories.
### --disable DISABLE
	--disable DISABLE                 disable section
Type: Option<br>
Default: None<br>
Option: `DISABLE`<br>
Repeat: Yes<br><br>
Disables section `DISABLE` that would otherwise be enabled by configuration file or command line option. Takes precedence over all other means of enabling sections.
### --dump DUMP
	--dump DUMP                       dump section
Type: Option<br>
Default: None<br>
Option: `DUMP`<br>
Repeat: Yes<br><br>
Outputs configuration section `DUMP`. Can dump multiple configuration sections. Can be used to remember how command substitutions will be generated.
### --dumpall
	--dumpall                         dump all sections
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Dumps all configuration sections.
### --enable ENABLE
	--enable ENABLE                   enabled sections
Type: Option<br>
Default: None<br>
Option: `ENABLE`<br>
Repeat: Yes<br><br>
Enables section `ENABLE` that would otherwise be disabled by configuration file or command line option. Takes precedence over default disable and configuration file.
### --file FILE
	--file FILE                       file with folder names
Type: Option<br>
Default: None<br>
Option: `FILE`<br>
Repeat: Yes<br><br>
Reads `FILE` as list of folders to be operated on instead of recursively scanning filesystem. Missing folders will be generated by `py:makecommand` or `py:makefunction` if available and in that order.
### --ignore IGNORE
	--ignore IGNORE                   ignore folder names
Type: Option<br>
Default: None<br>
Option: `IGNORE`<br>
Repeat: Yes<br><br>
Sets folder names that will not be visited when recursively searching file system.
### --invert
	--invert                          invert error codes
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Whether to invert error codes.
### --nocolor
	--nocolor                         disables colorized output
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Turns off color in output.
### --noenable
	--noenable                        no longer enable any sections
Type: Option<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Defaults all configuration sections to not be enabled. This can be changed later for each configuration section with other command line options.
### --noexec
	--noexec                          do not actually execute
Type: Flag<br>
Default: False<br>
Option: \<none>
Repeat: No<br><br>
Causes commands to be printed to the console but not actually executed.
### --noop
	--noop                            no command execution
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Indicates that no command should be run in any folder. This can be useful when folders will be generated because of `--file FILE` command line option. Since no command is run, the folder generation can be run in parallel.
### --py:closebrace PYCLOSEBRACE
		  --py:closebrace PYCLOSEBRACE      key for py:closebrace
Type: Option<br>
Default: %]<br>
Option: `PYCLOSEBRACE`
Repeat: No<br><br>
Sets the substitution string for a literal close brace.
### --py:enable PYENABLE
	--py:enable PYENABLE            key for py:enable
Type: Option<br>
Default: py:enable<br>
Option: `PYENABLE `<br>
Repeat: No<br><br>
Names `PYENABLE ` as the key to look up in each configuration section for determining if the section is enabled by default.
### --py:makecommand PYMAKECOMMAND
	--py:makecommand PYMAKECOMMAND    key for py:makecommand
Type: Option<br>
Default: py:makecommand<br>
Option: `PYMAKECOMMAND`<br>
Repeat: No<br><br>
Names `PYMAKECOMMAND` as the key to look up in each configuration section for generating commands to make folders.
### --py:makefunction PYMAKEFUNCTION
	--py:makefunction PYMAKEFUNCTION  key for py:makefunction
Type: Option<br>
Default: py:makefunction<br>
Option: `PYMAKEFUNCTION`<br>
Repeat: No<br><br>
Names `PYMAKEFUNCTION` as the key to look up in each configuration section for executing python commands to make folders.
### --py:openbrace PYOPENBRACE
		  --py:openbrace PYOPENBRACE      key for py:openbrace
Type: Option<br>
Default: %[<br>
Option: `PYOPENBRACE`
Repeat: No<br><br>
Sets the substitution string for a literal open brace.
### --py:pypriority PYPRIORITY
	--py:pypriority PYPRIORITY              key for py:priority
Type: Option<br>
Default: py:priority<br>
Option: `PYPRIORITY`<br>
Repeat: No<br><br>
Names `PYPRIORITY` as the key to look up in each configuration section for checking to see if a section applies to a folder.
### --sleepmake SLEEPMAKE
	  --sleepmake SLEEPMAKE             sleep between make calls
Type: Option<br>
Default: 0.1<br>
Option: `SLEEPMAKE`<br>
Repeat: No<br><br>
Sets the sleep value to issue between make folder commands. Can be used to throttle server connections.
### --sleepcommand SLEEPCOMMAND
	--sleepcommand SLEEPCOMMAND       sleep between command calls
Type: Option<br>
Default: 0<br>
Option: `SLEEPCOMMAND `<br>
Repeat: No<br><br>
Sets the sleep value to issue between recursive commands. Can be used to throttle server connections.
### --suppress
	--suppress                        suppress repeated error output
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Indicates that summary information for errors should not be output at end of execution. Output will otherwise be included depending on `--verbose` flag.
### --verbose VERBOSE
	--verbose VERBOSE                 verbose level
Type: Option<br>
Default: 4<br>
Option: `VERBOSE`<br>
Repeat: No<br><br>
Sets the level of output to be included in command execution where higher numbers include output of lower numbers:<br>
0. No output<br>
1. Only errors, at end of parallel execution<br>
2. Output of commands<br>
3. Output path, applicable section, and command<br>
4. Output one line for each command (at point of execution)<br>
5. Output of commands as execution finishes<br>
6. Output of make commands as make execution finishes<br>
### --workers WORKERS
	--workers WORKERS                 number of workers
Type: Option<br>
Default: \<number of cores><br>
Option: `WORKERS`<br>
Repeat: No<br><br>
Sets the number of simultaneous worker processes to use.
## Simple Examples
Simple examples of using `onsub` are below. The configuration file is assumed to be [example,onsub.py](https://bitbucket.org/sawolford/onsub/src/master/example,onsub.py) and it is executed on a Mac. The directory structure is assumed to be the following:

	git/
	git/.git
	hg/
	hg/.hg
	normal/
	svn/
	svn/.svn
Due to the limited quoting ability of the Windows `CMD.EXE` command shell, some of these examples are too sophisticated to run correctly in that environment.
### No command line options
With ` `:

	$ onsub pwd
	./svn (svn) pwd
	./hg (hg) pwd
	./git (git) pwd
	<<< RESULTS >>>
	./svn (svn) pwd
	/private/tmp/sample/svn
	
	./hg (hg) pwd
	/private/tmp/sample/hg
	
	./git (git) pwd
	/private/tmp/sample/git

Identifies `svn` as a `Subversion` folder, `hg` as a `Mercurial`, and `git` as a `Git` folder and executes `pwd` in those folders.
### Do not enable by default (--noenable)
With `--noenable`:

	$ onsub --noenable pwd

No sections are enabled so no commands are executed.
### Enable section (--enable ENABLE)
With `--noenable --enable git`:

	$ onsub --noenable --enable git pwd
	./git (git) pwd
	<<< RESULTS >>>
	./git (git) pwd
	/private/tmp/sample/git

Identifies `git` as `Git` folder and executes command. Only `git` section is applied.
### Disable section (--disable DISABLE)
With `--disable svn --disable hg`:

	$ onsub --disable svn --disable hg pwd
		./git (git) pwd
	<<< RESULTS >>>
	./git (git) pwd
	/private/tmp/sample/git

Identifies `git` as `Git` folder and executes command. Only `git` section is applied.
### Ignore folders (---ignore IGNORE [--ignore IGNORE ...])
With `--noenable --enable all --ignore .git --ignore .hg --ignore .svn`:

	$ onsub --noenable --enable all --ignore .git --ignore .hg --ignore pwd
	. (all) pwd
	./svn (all) pwd
	./normal (all) pwd
	./hg (all) pwd
	./git (all) pwd
	<<< RESULTS >>>
	. (all) pwd
	/tmp/sample
	
	./svn (all) pwd
	/private/tmp/sample/svn
	
	./normal (all) pwd
	/private/tmp/sample/normal
	
	./hg (all) pwd
	/private/tmp/sample/hg
	
	./git (all) pwd
	/private/tmp/sample/git

Visits all folder without traversing into ignored folders to execute command. 
### Dump config (--dump DUMP [--dump DUMP ...])
With `--dump default`:

	$ onsub --dump default
	default = {
			py:fileCheck = <function fileCheck at 0x103f3d680>
			cwd = /private/tmp
			sep = ;
			echo = /bin/echo
			lswcl = ls | wc -l
	}
With `--dump git`:

	$ onsub --dump git
	git = {
			py:fileCheck = <function fileCheck at 0x10359e680>
			cwd = /private/tmp
			sep = ;
			echo = /bin/echo
			lswcl = ls | wc -l
			py:priority = <function gitpriority at 0x10359e7a0>
			py:makecommand = <function gitmakecommand at 0x10359e710>
			cmd = git
			write = {cmd} ci -a
			get = {cmd} pull
			put = {cmd} push
			remote = {cmd} remote -v
			allremote = {remote}
			py:enable = True
	}
With `--dump hg`:

	$ onsub --dump hg
	hg = {
			py:fileCheck = <function fileCheck at 0x10eaa4680>
			cwd = /private/tmp
			sep = ;
			echo = /bin/echo
			lswcl = ls | wc -l
			py:priority = <function hgpriority at 0x10eaa4950>
			py:makecommand = <function hgmakecommand at 0x10eaa4830>
			cmd = hg
			py:write = <function hgwrite at 0x10eaa48c0>
			write = {cmd} ci
			get = {cmd} pull --update
			put = {cmd} push
			remote = {echo} -n "default = "; {cmd} paths default
			allremote = {remote}; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull
			py:enable = True
	}
With `--dump svn`:

	$ onsub --dump svn
	svn = {
			py:fileCheck = <function fileCheck at 0x109025680>
			cwd = /private/tmp
			sep = ;
			echo = /bin/echo
			lswcl = ls | wc -l
			py:priority = <function svnpriority at 0x109025a70>
			py:makecommand = <function svnmakecommand at 0x1090259e0>
			cmd = svn
			write = {cmd} [noop]
			get = {cmd} up
			put = {cmd} ci
			remote = {cmd} info --show-item url
			allremote = {remote}
			py:enable = True
	}
With `--dump all`:

	$ onsub --dump all
	all = {
			py:fileCheck = <function fileCheck at 0x102dbc680>
			cwd = /private/tmp
			sep = ;
			echo = /bin/echo
			lswcl = ls | wc -l
			py:priority = <function allpriority at 0x102dbcb90>
			py:makefunction = <function allmakefunction at 0x102dbcb00>
	}
### Limit recursion depth (--depth)
With `--enable all --depth 1`:

	$ onsub --enable all --depth 1 pwd
	. (all) pwd
	<<< RESULTS >>>
	. (all) pwd
	/tmp/sample
Only recurses one level deep.

With `--enable all --depth 2`:

	$ onsub --enable all --depth 2 pwd
	. (all) pwd
	./svn (svn) pwd
	./normal (all) pwd
	./hg (hg) pwd
	./git (git) pwd
	<<< RESULTS >>>
	. (all) pwd
	/tmp/sample
	
	./svn (svn) pwd
	/private/tmp/sample/svn
	
	./normal (all) pwd
	/private/tmp/sample/normal
	
	./hg (hg) pwd
	/private/tmp/sample/hg
	
	./git (git) pwd
	/private/tmp/sample/git
Recurses an additional level into working copies.

With `--enable all --depth 3`:

	$ onsub --enable all --depth 3 pwd
	. (all) pwd
	./svn (svn) pwd
	./svn/.svn (all) pwd
	./normal (all) pwd
	./hg (hg) pwd
	./hg/.hg (all) pwd
	./git (git) pwd
	./git/.git (all) pwd
	<<< RESULTS >>>
	. (all) pwd
	/tmp/sample
	
	./svn (svn) pwd
	/private/tmp/sample/svn
	
	./svn/.svn (all) pwd
	/private/tmp/sample/svn/.svn
	
	./normal (all) pwd
	/private/tmp/sample/normal
	
	./hg (hg) pwd
	/private/tmp/sample/hg
	
	./hg/.hg (all) pwd
	/private/tmp/sample/hg/.hg
	
	./git (git) pwd
	/private/tmp/sample/git
	
	./git/.git (all) pwd
	/private/tmp/sample/git/.git
Recurses an additional level into working copy version control folders.
### No execution (--noexec)
With `--noexec pwd`:

	$ onsub --noexec pwd
	./svn (svn) pwd
	./hg (hg) pwd
	./git (git) pwd
	<<< RESULTS >>>
	./svn (svn) pwd
	[noexec] pwd
	./hg (hg) pwd
	[noexec] pwd
	./git (git) pwd
	[noexec] pwd
Identifies `svn` as a `Subversion` folder, `hg` as a `Mercurial`, and `git` as a `Git` folder but only outputs the command that would have been executed.
### Noop (--noop)
With `--noop`:

	$ onsub --noop
	./svn (svn)
	./hg (hg)
	./git (git)
	<<< RESULTS >>>
	./svn (svn)
	
	./hg (hg)
	
	./git (git)
Identifies `svn` as a `Subversion` folder, `hg` as a `Mercurial`, and `git` as a `Git` folder but doesn't execute any command in those folders.
## Git examples
Complex Git examples of using `onsub` are below. The configuration file is assumed to be [example,onsub.py](https://bitbucket.org/sawolford/onsub/src/master/example,onsub.py) and it is executed on a Mac. The file `input.py` is assumed to contain the following:

	git = [
		("./onsub1", "https://bitbucket.org/sawolford/onsub.git"),
		("./onsub2", "https://bitbucket.org/sawolford/onsub.git"),	]
### Input file (--file FILE)
With `--file input.py --noop`:

	$ onsub --file input.py --noop
	./onsub1 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub1
	./onsub2 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub2
	./onsub1 (git)
	./onsub2 (git)
	<<< RESULTS >>>
	./onsub1 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub1
	Cloning into './onsub1'...
	
	./onsub2 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub2
	Cloning into './onsub2'...
	
	./onsub1 (git)
	
	./onsub2 (git)
Clones `onsub` `git` repository locally.
### Git fetch
With `--file input.py {cmd} fetch -v`

	$ onsub --file input.py {cmd} fetch -v
	./onsub1 (git) git fetch -v
	./onsub2 (git) git fetch -v
	<<< RESULTS >>>
	./onsub2 (git) git fetch -v
	From https://bitbucket.org/sawolford/onsub
	 = [up to date]      master     -> origin/master
	
	./onsub1 (git) git fetch -v
	From https://bitbucket.org/sawolford/onsub
	 = [up to date]      master     -> origin/master
Fetches changesets and outputs current local branch and upstream branch.
### Git pull
With `--file input.py {cmd} pull`

	$ onsub --file input.py {cmd} pull
	./onsub1 (git) git pull
	./onsub2 (git) git pull
	<<< RESULTS >>>
	./onsub2 (git) git pull
	Already up to date.
	
	./onsub1 (git) git pull
	Already up to date.
### Selective folder git pull
With `--chdir onsub1 {cmd} pull`:

	$ onsub --chdir onsub1 {cmd} pull
	. (git) git pull
	<<< RESULTS >>>
	. (git) git pull
	Already up to date.
Changes directory to `onsub1` and executes `pull` command.
## Mercurial Examples
Complex Mercurial examples of using `onsub` are below. The configuration file is assumed to be [example,onsub.py](https://bitbucket.org/sawolford/onsub/src/master/example,onsub.py) and it is executed on a Mac.

Assume a program, `hgcheck`, is in the shell command search path and contains the following Python code:

	#!/usr/bin/env python3
	import os, sys
	import subprocess as sp
	
	def mycheck_output(cmd, stderr=sp.STDOUT):
		try:
		out = sp.check_output(cmd, shell=True, stderr=stderr).decode()
		ec = 0
		pass
	except sp.CalledProcessError as exc:
		out = exc.output.strip().decode()
		ec = exc.returncode
		pass
	return ec, out
	
	def outcount(cmd):
		ec, out = mycheck_output(cmd, stderr=sp.DEVNULL)
		return out.count("\n")
	
	def hgcheck(verbose, debug, path, noexec, *rest):
		if noexec: return 0, "[noexec] hgcheck"
		if not os.path.exists(".hg"): return 0, "[not an hg clone]"
		nheads = outcount("hg heads -q .")
		nparents = outcount("hg parents -q")
		if nheads == 2 and nparents == 2: return 1, 'onsub --chdir {path} --workers 1 --depth 1 {{continue}}'.format(path=path)
		elif nheads == 2 and nparents == 1: return 2, 'onsub --chdir {path} --workers 1 --depth 1 {{finish}}'.format(path=path)
		nst = outcount("hg st -q")
		if nst > 0: return 3, 'onsub --chdir {path} --workers 1 --depth 1 {{write}}'.format(path=path)
		if len(rest) and rest[0] == "--local": return 0, "[no local mods]"
		nout = outcount("hg out -q")
		nin = outcount("hg in -q")
		if nout > 0 and nin == 0: return 4, 'onsub --chdir {path} --workers 1 --depth 1 {{put}}'.format(path=path)
		if nin > 0 and nout == 0: return 5, 'onsub --chdir {path} --workers 1 --depth 1 {{get}}'.format(path=path)
		if nin > 0 and nout > 0: return 6, 'onsub --chdir {path} --workers 1 --depth 1 {{mix}}'.format(path=path)
		return 0, "[no local mods, no repository changes]"
	
	def myhgcheck(*args): return hgcheck(5, False, os.getcwd(), False, *args)
	
	if __name__ == "__main__":
		ec, out = myhgcheck(sys.argv)
		print(out)
		sys.exit(ec)
		pass
Also, assume the `hg` configuration section includes the following commands:

	check = hgcheck
	rebasefail = {cmd} pull --rebase -t internal:fail
	pullupdate = {cmd} pull --update
	sync = {rebasefail} {sep} {pullupdate}
	continue = {cmd} resolve --re-merge --all {sep} hg rebase --continue
	finish = {cmd} shelve {sep} hg rebase {sep} hg unshelve
	mix = {cmd} pull --rebase
And the `arguments` list contains (at least):

	arguments = [
		"--ignore", "hgsrc",
	]
Prepare the sample folder with the following commands:

	$ hg init hgsrc
	$ cd hgsrc
	$ echo hgsrc > file.txt
	$ hg add file.txt
	$ hg ci -m "added file.txt"
	$ cd ..
	$ hg clone hgsrc hgwc
	updating to branch default
	1 files updated, 0 files merged, 0 files removed, 0 files unresolved
	$ hg clone hgsrc hgout
	updating to branch default
	1 files updated, 0 files merged, 0 files removed, 0 files unresolved
	$ cd hgwc
	$ echo hgwc > file.txt
	$ cd ..
	$ cd hgout
	$ echo hgout > file.txt
	$ hg ci -m "changed file.txt"
	$ cd ..
At this point, there's a "remote" repository (`hgsrc`), a local clone with working copy changes (`hgwc`), and a local clone with local commits (`hgout`). For the following steps, the `hgsrc` folder will be ignored for easier understanding, as specified by the `arguments` configuration.

Determine current state of clones with `{check}`:

	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
	<<< ERRORS >>>
	(3) ./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
	(4) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
Error `3` indicates that the `hgwc` folder has local changes to commit. Error `4` indicates that the `hgout` folder has a changeset to push. The output command for each error instructs how those folders might be brought to a clean working copy and synced local clone.

Since the only commands recommended for execution are `write` and `put`, we can execute either of the suggested commands immediately. For a better example, we'll issue the `write` command followed by `check` first:

	$ onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
	. (hg) hg ci
	<<< RESULTS >>>
	. (hg) hg ci
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {put}
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
	<<< ERRORS >>>
	(4) ./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {put}
	(4) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
Now, we can execute a `put` command followed by a `check`:

	$ onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {put} 
	. (hg) hg push
	<<< RESULTS >>>
	. (hg) hg push
	pushing to /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {mix}
	<<< ERRORS >>>
	(6) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {mix}
Error `6` indicates that the `hgout` folder has both incoming and outgoing changesets. We now need to issue a `sync` command followed by a `check` to prepare that folder for rebasing:

	$ onsub {sync}
	./hgwc (hg) hg pull --rebase -t internal:fail ; hg pull --update
	./hgout (hg) hg pull --rebase -t internal:fail ; hg pull --update
	<<< RESULTS >>>
	./hgwc (hg) hg pull --rebase -t internal:fail ; hg pull --update
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	no changes found
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	no changes found
	
	./hgout (hg) hg pull --rebase -t internal:fail ; hg pull --update
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files (+1 heads)
	new changesets b7a77527113e
	rebasing 1:288098ad71dd "changed file.txt"
	unresolved conflicts (see hg resolve, then hg rebase --continue)
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	no changes found
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {continue}
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	<<< ERRORS >>>
	(1) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {continue}

Error `1` indicates that folder has a rebase to to continue. Executing the `continue` command followed by a `check`:

	$ onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {continue}
	. (hg) hg resolve --re-merge --all ; hg rebase --continue
	<<< RESULTS >>>
	. (hg) hg resolve --re-merge --all ; hg rebase --continue
	merging file.txt
	running merge tool kdiff3 for file file.txt
	(no more unresolved files)
	continue: hg rebase --continue
	rebasing 1:288098ad71dd "changed file.txt"
	saved backup bundle to /private/tmp/sample/hgout/.hg/strip-backup/288098ad71dd-2f436550-rebase.hg
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
	<<< ERRORS >>>
	(4) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
We now have error `4` again. We'll issue that command again but, first, we'll create a conflict in `hgwc`:

	$ echo conflict > hgwc/file.txt
Pushing our changeset with `put` followed by `check`:

	$ . (hg) hg push
	<<< RESULTS >>>
	. (hg) hg push
	pushing to /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
	./hgout (hg) hgcheck
	[no local mods, no repository changes]
	
	<<< ERRORS >>>
	(3) ./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
In this case, we don't actually want to commit that change but we would rather keep it as a working copy change. We'll issue a `sync` command followed by `check` instead:

	$ onsub {sync}
	./hgwc (hg) hg pull --rebase -t internal:fail ; hg pull --update
	./hgout (hg) hg pull --rebase -t internal:fail ; hg pull --update
	<<< RESULTS >>>
	./hgout (hg) hg pull --rebase -t internal:fail ; hg pull --update
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	no changes found
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	no changes found
	
	./hgwc (hg) hg pull --rebase -t internal:fail ; hg pull --update
	abort: uncommitted changes
	(cannot pull with rebase: please commit or shelve your changes first)
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files
	new changesets 0a5c470752a3
	merging file.txt
	running merge tool kdiff3 for file file.txt
	0 files updated, 1 files merged, 0 files removed, 0 files unresolved
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
	./hgout (hg) hgcheck
	[no local mods, no repository changes]
	
	<<< ERRORS >>>
	(3) ./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
Following the conflict merge to update the working copy, we can see that we have one dirty working copy. We'll commit that change now with the `write` command followed by `check`:

	$ onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {write}
	. (hg) hg ci
	<<< RESULTS >>>
	. (hg) hg ci
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgout (hg) hgcheck
	[no local mods, no repository changes]
	
	./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {put}
	<<< ERRORS >>>
	(4) ./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {put}
We can now push that changeset with the `put` command followed by `check`:

	$ onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {put}
	. (hg) hg push
	<<< RESULTS >>>
	. (hg) hg push
	pushing to /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {get}
	<<< ERRORS >>>
	(5) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {get}
At this point, we could issue a `get` command and bring all working copies up-to-date. Instead, we'll muck things up a bit in order to illustrate more commands. To create some conflicts, issue the following commands:

	$ cd hgout
	$ echo hgout hgwc hgout > file.txt
	$ hg ci -m "added hgout"
	$ echo hgout hgwc hgout hgwc > file.txt
	$ cd ..
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {write}
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	<<< ERRORS >>>
	(3) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {write}
We now have a local change to commit but we'd rather not commit that change now. Instead, we'll issue another `sync` command followed by `check`:

	$ onsub {sync}
	./hgwc (hg) hg pull --rebase -t internal:fail ; hg pull --update
	./hgout (hg) hg pull --rebase -t internal:fail ; hg pull --update
	<<< RESULTS >>>
	./hgout (hg) hg pull --rebase -t internal:fail ; hg pull --update
	abort: uncommitted changes
	(cannot pull with rebase: please commit or shelve your changes first)
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files (+1 heads)
	new changesets 2c8d827f7740
	0 files updated, 0 files merged, 0 files removed, 0 files unresolved
	updated to "dfa662e51616: added hgout"
	1 other heads for branch "default"
	
	./hgwc (hg) hg pull --rebase -t internal:fail ; hg pull --update
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	no changes found
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	no changes found
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {finish}
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	<<< ERRORS >>>
	(2) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {finish}
Error `2` indicates that we have a rebase to finish. Executing `finish` followed by `check`:

	$ onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {finish}
	. (hg) hg shelve ; hg rebase ; hg unshelve
	<<< RESULTS >>>
	. (hg) hg shelve ; hg rebase ; hg unshelve
	shelved as default
	1 files updated, 0 files merged, 0 files removed, 0 files unresolved
	rebasing 3:dfa662e51616 "added hgout"
	merging file.txt
	running merge tool kdiff3 for file file.txt
	saved backup bundle to /private/tmp/sample/hgout/.hg/strip-backup/dfa662e51616-8c710714-rebase.hg
	unshelving change 'default'
	rebasing shelved changes
	merging file.txt
	running merge tool kdiff3 for file file.txt
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {write}
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	<<< ERRORS >>>
	(3) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {write}
We now have a dirty working copy. Executing the `write` command followed by `check`:

	$ onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {write}
	. (hg) hg ci
	<<< RESULTS >>>
	. (hg) hg ci
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
	<<< ERRORS >>>
	(4) ./hgout (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
We now have a changeset to push. Executing the `put` command followed by `check`:

	$ onsub --chdir /private/tmp/sample/hgout --workers 1 --depth 1 {put}
	. (hg) hg push
	<<< RESULTS >>>
	. (hg) hg push
	pushing to /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 2 changesets with 2 changes to 1 files
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {get}
	./hgout (hg) hgcheck
	[no local mods, no repository changes]
	
	<<< ERRORS >>>
	(5) ./hgwc (hg) hgcheck
	onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {get}
Finally, we have an incoming changeset to pull. Executing the `get` command followed by `check`:

	$ onsub --chdir /private/tmp/sample/hgwc --workers 1 --depth 1 {get}
	. (hg) hg pull --update
	<<< RESULTS >>>
	. (hg) hg pull --update
	pulling from /private/tmp/sample/hgsrc
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 2 changesets with 2 changes to 1 files
	new changesets 270ca80b054a:8e21673a6413
	1 files updated, 0 files merged, 0 files removed, 0 files unresolved
	
	$ onsub {check}
	./hgwc (hg) hgcheck
	./hgout (hg) hgcheck
	<<< RESULTS >>>
	./hgwc (hg) hgcheck
	[no local mods, no repository changes]
	
	./hgout (hg) hgcheck
	[no local mods, no repository changes]
And now all working copies are up-to-date and synced.
## Notes
The code is completely undocumented right now but it's pretty short and leverages a bunch of Python magic to provide a ton of flexibility. It can be compiled into executables as well but we can provide those later if this approach gains traction.
