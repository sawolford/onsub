# onsub.py
[onsub.py v0.9](https://bitbucket.org/sawolford/onsub.git)
## Summary
The onsub.py command iterates over subfolders to execute arbitrary commands as dictated by command line arguments and a Python configuration file. The main code consists of two (2) concepts implemented in Python: an example Python-configuration file that is meant to be user configurable and the onsub.py script that executes commands as dictated by command line arguments and the configuration file.

All provided files, with a short description, are:

	- onsub.py            -- the main execution code (<500 lines)
	- onsub               -- very short python script that calls onsub.py
	- pushd.py            -- implements shell-like pushd capability (borrowed)
	- onsubbuiltin.py     -- config file that implements very basic hg, git, svn behavior
	- onsubdefaults.py    -- sample configuration file that just loads ~/.onsublocal.py
	- onsubexample.py     -- sample configuration file 
	- onsubcheck.py       -- sample configuration file for complex examples
	- guestrepo2onsub.py  -- converter from guestrepo to onsub syntax
	- onsub2file.py       -- prints to stdout a file listing of prioritized folders
	- onsub2revs.py       -- prints to stdout a file listing of prioritized folders with 
	- gitcheck.py         -- checks status of git clone with recommended commands
	- hgcheck.py          -- checks status of hg clone with recommended commands
	- svncheck.py         -- checks status of svn clone with recommended commands
	- README.md           -- this file
The configuration file is described later but it is organized into sections and provides rules for operation. The `onsub` command can be run in two main modes: file mode and recurse mode.

The first mode of operation is file mode, where a special file is provided indicating which subfolders are to be visited and, optionally, information about how to create them if they are missing. File mode is indicated by the `--file FILE` command line argument. The `FILE` parameter indicates the input file of expected folders, grouped by section (described below)) and, optionally, additional arguments for each expected folder. If the `--make` command line argument is provided, then this mode can be used to construct all of the folders described by `FILE` in parallel according to rules for the corresponding section in the configuration file.  Example:

	git = [
		("./onsub", "https://bitbucket.org/sawolford/onsub.git"),
	]

The second mode of operation is recurse mode, where the filesystem is recursively searched, infinitely or up to a given depth. The configuration code is then queried for each folder in order to see if the `onsub` command should execute a command in that folder and how to do so. If the provided command indicates that variable substitution is necessary, the configuration file can also specify rules for how the command is constructed.

Recurse mode is indicated by the lack of a `--file FILE` command line argument. Instead of iterating over provided folder names, `onsub` instead recurses through the file system to visit folders. Example:

	$ onsub pwd
Both modes will execute commands according to the provided command line arguments. Extensive examples are provided at the end but some simple examples capture the main ways that commands are provided on the `onsub` command line. Examples:

	$ onsub --file input.py --make   # constructs folders from input.py in parallel
	$ onsub --file input.py {remote} # constructs folders from input.py in parallel, then executes "{remote}" command in each
	$ onsub {cmd} status             # recurses to all subfolders and runs "{cmd} status"
	$ onsub pwd                      # recurses to all subfolders and runs "pwd"
## Configuration
The configuration file for `onsub` is nothing but a Python script, so it follows normal Python syntax rules. The code is interpreted by `onsub` as a color configuration list (`colors`), a default argument list (`arguments`), and a set of Python dictionaries, each of which is known as a section. The `colors` list instructs `onsub` how to colorize output. The `arguments` list contains arguments that are always passed to `onsub`. Each section is just a normal Python dictionary with keys and values. Sections are optional but, in the absence of extensive command line arguments, essentially required for onsub to do much more than basic work.

The section names and most of the contents are arbitrary but are interpreted by `onsub` in such a way that work may be performed on file folders. Most dictionary keys in a section entry are completely arbitrary and will be passed to the Python `string.format()` function in order to construct shell commands. This formatting process is repeated a set number of times or until the string no longer changes. If the value is a Python function, then it is called to create the substitution string. If a key is prefixed by `py:`, then the value is instead interpreted as a Python function whose arguments are prescribed for certain keys (described below) or just a list of remaining command line arguments.

Dictionary entry keys that are interpreted specially by `onsub`:
#### - `py:enable`
Must evaluate directly to `True` or `False` (default: `False`). Indicates that the section is to be interpreted directly by `onsub`. Setting this to `False` can be used to construct  a composite section that is then enabled by itself. Example:

	git["py:enable"] = True
#### - `py:priority`
Python function taking three (3) arguments: `verbose`, `debug`, `path`. The first two are flags that can be used to control output. The last is the path that should be checked to see if the section applies. The current working directory context for this function call is also set to `path`. The function should return zero if the section does not apply and return a non-zero priority if the section applies. Required for any enabled section. Example:

	def gitpriority(verbose, debug, path): return 4 if os.path.exists(".git") else 0
#### - `py:makecommand`
Python function taking four (4) arguments: `verbose`, `debug`, `path`, `*rest`. The first two are flags that can be used to control output. The third is the path that does not exist or needs to be updated. The last is a list for accepting a variable number of arguments. These variable arguments are taken from an input file (described later) and should typically contain additional instructions for constructing a missing folder. The function should return a string that evaluates to a shell command. Required if construction is requested (`--make`) and `py:makefunction` is not set (`py:makecommand` takes precedence over `py:makefunction`). Example:

	def gitmakecommand(verbose, debug, path, *rest):
		if os.path.exists(path): return None
		assert len(rest) >= 1
		url = rest[0]
		cmd = "{{cmd}} clone {url} {path}".format(url=url, path=path)
		if debug: print(cmd)
		return cmd
#### - `py:makefunction` 
Python function taking five (5) arguments: `verbose`, `debug`, `path`, `noexec`, `*rest`. The first two are flags that can be used to control output. The third is the path that does not exist or needs to be updated. The fourth is a flag indicating that the function should not actually execute. The last is a list for accepting a variable number of arguments. These variable arguments are taken from an input file (described later) and should typically contain additional instructions for constructing a missing folder. The function should actually perform the necessary operation to construct a missing folder and should return a tuple consisting of an error code and an output string. This command will not be executed in parallel due to limitations of Python multiprocessing. Required if construction is requested and `py:makecommand` is not set. Example:

	def allmakefunction(verbose, debug, path, noexec, *rest):
		if os.path.exists(path): return 0, 'path "{path}" already exists'.format(path=path)
		if verbose >=4: print("os.makedirs({path})".format(path=path))
		if noexec: return 0, "[noexec] os.makedirs({path})".format(path=path)
		os.makedirs(path)
		return 0, "os.makedirs({path})".format(path=path)
#### - string.format() strings
Some dictionary entries are strings that can contain Python variable substitution specifiers compatible with the Python `string.format()` standard method. Variables are substituted from the same section dictionary. This variable substitution is performed iteratively a set number of times or until the string no longer changes. Example:

	"cmd": "git"
	"-v": "-v"
	"remote": "{cmd} remote {-v}"
#### - Python substitution generator
Some dictionary entries are Python functions that generate strings for variable substitution compatible with the Python `string.format()` standard method. Example:

	def getcwd(path):
		try:
			with pd.pushd(path): return os.getcwd()
			pass
		except FileNotFoundError: pass
		return ""
	
	defdefault = {
		"cwd": lambda v, d, path: getcwd(path),
	}
### Final configuration
Since the configuration file is just normal Python code, complex configurations can be constructed. Python allows a dictionary to be updated from another dictionary, where only keys in the other dictionary are replaced in the original. Checks against operating system type can be performed to alter behavior depending on the underlying OS. The resultant dictionary, if enabled, is the only one that will be interpreted by `onsub`. Example:

	git = {}
	git.update(default)
	git.update(gitdefault)
	if os.name == "nt": git.update(gitwindows)
	else: git.update(gitlinux)
	git["py:enable"] = True
The default configuration file is located at `${HOME}/.onsub.py`. Some very simple fallback configurations are loaded from the [builtin configuration file (onsubbuiltin.py)](https://bitbucket.org/sawolford/onsub/src/master/config/onsubbuiltin.py). An extremely simple example file is loaded from the [example configuration file (onsubexample.py)](https://bitbucket.org/sawolford/onsub/src/master/config/onsubexample.py). Finally, a sophisticated functional [example configuration file (onsubcheck.py)](https://bitbucket.org/sawolford/onsub/src/master/config/onsubcheck.py) provides sample commands for [Git](https://git-scm.com/), [Mercurial](https://www.mercurial-scm.org/) and [Subversion](https://subversion.apache.org/). 
### Details (using `onsubbuiltin.py`)
#### - Pseudo-section `colors`
Colors to use in colorized output. Commented lines indicate default values for each type of output.

Value:

	colors = {
		"path": Fore.BLUE + Back.RESET + Style.BRIGHT,
		"command": Fore.CYAN + Back.RESET + Style.BRIGHT,
		"errorcode": Fore.RED + Back.RESET + Style.BRIGHT,
		"partition": Fore.YELLOW + Back.RESET + Style.BRIGHT,
		# "good": Fore.GREEN + Back.RESET + Style.BRIGHT,
		# "bad": Fore.MAGENTA + Back.RESET + Style.BRIGHT,
		# "error": Fore.RED + Back.RESET + Style.BRIGHT,
	}
Explanation:

	path       -- Folder where command is executed
	command    -- Command that is executed
	errorcode  -- Command exit code
	partition  -- Separator between normal output and repeated error output
	good       -- Output, if error code of command is zero
	bad        -- Output, if error code of command is non-zero (default: not used)
	error      -- Final output repeated for those commands with non-zero error code (default: not used)
#### - Pseudo-section `arguments`
Allows the same arguments to be passed to all invocations of `onsub`. Value:

	arguments = [
		# "--chdir", ".",
		# "--color",
		# "--comment", "ignored",
		# "--count", "10",
		# "--debug",
		# "--depth", "1",
		# "--disable", "all",
		# "--discard",
		# "--dump",
		# "--dumpall",
		# "--enable", "all",
		# "--file", "subs.py",
		# "--hashed",
		# "--ignore", ".hg", "--ignore", ".git", "--ignore", ".svn",
		# "--invert",
		# "--make",
		# "--nocolor",
		# "--noenable",
		# "--noexec",
		# "--nofile",
		# "--nohashed",
		# "--noignore",
		# "--nomake",
		# "--preconfig", "",
		# "--postconfig", "",
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
	getcwd      -- Python helper function that returns the current working directory
	defdefault  -- Pseudo-section used by default for all OSs
	deflinux    -- Pseudo-section used by default for Linux
	defwindows  -- Pseudo-section used by default for Windows
	default     -- Pseudo-section used by later sections
##### `default` Linux
Composite:

	default = {
		onsub = onsub
		cwd = <function <lambda> at 0x1079d5c20>
		sep = ;
		echo = /bin/echo
	}
Explanation:

	onsub  -- Self-reference for onsub program
	cwd    -- Python function that returns the current working directory
	sep    -- Platform-specific separator to use between shell commands
	echo   -- Path to echo command
##### `default` details
	def getcwd(path):
		try:
			with pd.pushd(path): return os.getcwd()
			pass
		except FileNotFoundError: pass
		return ""
	
	defdefault = {
		"onsub": "onsub",
		"cwd": lambda v, d, path: getcwd(path),
	}
	deflinux = {
		"sep": ";",
		"echo": "/bin/echo",
	}
	defwindows = { "sep": "&", }
	
	default = {}
	default.update(defdefault)
	if os.name =="nt": default.update(defwindows)
	else: default.update(deflinux)
#### - Section `git`
The example `git` section provides sample `git` commands.
##### `git` summary
	gitmakecommand  -- Python helper function that makes or updates a git clone
	gitpriority     -- Python helper function that checks if folder is a git folder
	gitdefault      -- Pseudo-section for all OSs for git
	gitlinux        -- Pseudo-section for all Linux for git
	gitwindows      -- Pseudo-section for all Windows for git
	git             -- Configuration section for git
##### `git` Linux
Composite:

	git = {
		onsub = onsub
		cwd = <function <lambda> at 0x10db01c20>
		sep = ;
		echo = /bin/echo
		type = echo '(git)' {cwd}
		ctype = echo '(git)' {cwd}
		py:priority = <function gitpriority at 0x10db01d40>
		py:makecommand = <function gitsubsmakecommand at 0x10db30830>
		cmd = git
		remote = {cmd} remote get-url origin
		allremote = {cmd} remote -v
		wcrev = {cmd} rev-parse --verify --short HEAD
       py:enable = True
 	}
Explanation:

	onsub           -- Inherited from default pseudo-section
	cwd             -- Inherited from default pseudo-section
	sep             -- Inherited from default pseudo-section
	echo            -- Inherited from default pseudo-section
	type            -- Command alias
	ctype           -- Command alias
	py:priority     -- Python function that establishes a folder applies to this section
	py:makecommand  -- Python function that returns a shell command for cloning git folder
	cmd             -- Command alias
	wcrev           -- Command alias
	remote          -- Command alias
	allremote       -- Command alias
	py:enable       -- Python flag indicating that this section is enabled by default
##### `git` details
	def gitmakecommand(verbose, debug, path, *rest):
		if os.path.exists(path): return None
		assert len(rest) >= 1
		url = rest[0]
		cmd = "{{cmd}} clone {url} {path}".format(url=url, path=path)
		if debug: print(cmd)
		return cmd
	
	def gitpriority(verbose, debug, path): return 4 if os.path.exists(".git") else 0
	
	gitdefault = {
		"type": "echo '(git)' {cwd}",
		"ctype": "echo " + Fore.GREEN + Back.RESET + Style.BRIGHT + "'(git)'" + Fore.RESET + " {cwd}",
		"py:priority": gitpriority, 
		"py:makecommand": gitmakecommand,
		"cmd": "git",
		"remote": "{cmd} remote get-url origin",
		"allremote": "{cmd} remote -v",
		"wcrev": "{cmd} rev-parse --verify --short HEAD",
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
	hgmakecommand  -- Python helper function that makes an hg clone
	hgpriority     -- Python helper function checks if folder is a hg folder
	hgdefault      -- Pseudo-section for all OSs for hg
	hglinux        -- Pseudo-section for all Linux for hg
	hgwindows      -- Pseudo-section for all Windows for hg
	hg             -- Configuration section for hg
##### `hg` Linux
Composite:

	hg = {
		onsub = onsub
		cwd = <function <lambda> at 0x1025bfc20>
		sep = ;
		echo = /bin/echo
		type = echo '(hg)' {cwd}
		ctype = echo '(hg)' {cwd}
		py:priority = <function hgpriority at 0x1025bfe60>
		py:makecommand = <function hgsubsmakecommand at 0x1025ee8c0>
		cmd = hg
		wcrev = {cmd} id -i
		remote = {cmd} paths default
		allremote = {echo} -n "default = "; {cmd} paths default; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull
		py:enable = True
	}
Explanation:

	onsub           -- Inherited from default pseudo-section
	cwd             -- Inherited from default pseudo-section
	sep             -- Inherited from default pseudo-section
	echo            -- Inherited from default pseudo-section
	type            -- Command alias
	ctype           -- Command alias
	py:priority     -- Python function that establishes a folder applies to this section
	py:makecommand  -- Python function that returns a shell command for cloning hg folder
	cmd             -- Command alias
	wcrev           -- Command alias
	remote          -- Command alias
	allremote       -- Command alias
	py:enable       -- Python flag indicating that this section is enabled by default
##### `hg` details
	def hgmakecommand(verbose, debug, path, *rest):
		if os.path.exists(path): return None
		assert len(rest) >= 1
		rrev = ""
		if len(rest) >= 2: rrev = "-r {rev}".format(rev=rest[1])
		url = rest[0]
		cmd = "{{cmd}} clone {url} {path} {rrev}".format(url=url, path=path, rrev=rrev)
		if debug: print(cmd)
		return cmd
	
	def hgpriority(verbose, debug, path): return 3 if os.path.exists(".hg") else 0
	
	hgdefault =  {
		"type": "echo '(hg)' {cwd}",
		"ctype": "echo " + Fore.CYAN + Back.RESET + Style.BRIGHT + "'(hg)'" + Fore.RESET + " {cwd}",
		"py:priority": hgpriority,
		"py:makecommand": hgmakecommand,
		"cmd": "hg",
		"wcrev": "{cmd} id -i",
	}
	hglinux = {
		"remote": '{cmd} paths default',
		"allremote": '{echo} -n "default = "; {cmd} paths default; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull',
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
		onsub = onsub
		cwd = <function <lambda> at 0x10e7f7c20>
		sep = ;
		echo = /bin/echo
		type = echo '(svn)' {cwd}
		ctype = echo '(svn)' {cwd}
		py:priority = <function svnpriority at 0x10e7f7f80>
		py:makecommand = <function svnsubsmakecommand at 0x10e826950>
		cmd = svn
		remote = {cmd} info --show-item url
		allremote = {remote}
		wcrev = {cmd} info --show-item revision
		py:enable = True
	}
Explanation:

	onsub           -- Inherited from default pseudo-section
	cwd             -- Inherited from default pseudo-section
	sep             -- Inherited from default pseudo-section
	echo            -- Inherited from default pseudo-section
	type            -- Command alias
	ctype           -- Command alias
	py:priority     -- Python function that establishes a folder applies to this section
	py:makecommand  -- Python function that returns a shell command for checking out svn folder
	cmd             -- Command alias
	wcrev           -- Command alias
	remote          -- Command alias
	allremote       -- Command alias
	py:enable       -- Python flag indicating that this section is enabled by default
##### `svn` details
	def svnmakecommand(verbose, debug, path, *rest):
		if os.path.exists(path): return None
		assert len(rest) >= 1
		rev = "head"
		if len(rest) >= 2: rev = rest[1]
		url = rest[0]
		cmd = "{{cmd}} checkout {url}@{rev} {path}".format(url=url, path=path, rev=rev)
		if debug: print(cmd)
		return cmd
	
	def svnpriority(verbose, debug, path): return 2 if os.path.exists(".svn") else 0
	
	svndefault = {
		"type": "echo '(svn)' {cwd}",
		"ctype": "echo " + Fore.MAGENTA + Back.RESET + Style.BRIGHT + "'(svn)'" + Fore.RESET + " {cwd}",
		"py:priority": svnpriority,
		"py:makecommand": svnmakecommand,
		"cmd": "svn",
		"remote": "{cmd} info --show-item url",
		"allremote": "{remote}",
		"wcrev": "{cmd} info --show-item revision"
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
		onsub = onsub
		cwd = <function <lambda> at 0x109e36c20>
		sep = ;
		echo = /bin/echo
		type = echo '(all)' {cwd}
		ctype = {type}
		py:priority = <function allpriority at 0x109e3c0e0>
		py:makefunction = <function allmakefunction at 0x109e3c050>
	}
Explanation:

	onsub            -- Inherited from default pseudo-section
	cwd              -- Inherited from default pseudo-section
	sep              -- Inherited from default pseudo-section
	echo             -- Inherited from default pseudo-section
	cwd              -- Inherited from default pseudo-section
	type             -- Command alias
	ctype            -- Command alias
	py:priority      -- Python function that establishes a folder applies to this section
	py:makefunction  -- Python function that makes a folder
##### `all ` details
	def allmakefunction(verbose, debug, path, noexec, *rest):
		if os.path.exists(path): return 0, 'path "{path}" already exists'.format(path=path)
		if verbose >=4: print("os.makedirs({path})".format(path=path))
		if noexec: return 0, "[noexec] os.makedirs({path})".format(path=path)
		os.makedirs(path)
		return 0, "os.makedirs({path})".format(path=path)
	
	def allpriority(verbose, debug, path): return 1
	
	alldefault = {
		"type": "echo '(all)' {cwd}",
		"ctype": "{type}",
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

	usage: onsub [-h] [--chdir CHDIR] [--color] [--comment COMMENT] [--configfile CONFIGFILE] [--count COUNT] [--debug]
				 [--depth DEPTH] [--disable DISABLE] [--discard] [--dump DUMP] [--dumpall] [--enable ENABLE] [--file FILE]
				 [--hashed] [--ignore IGNORE] [--invert] [--make] [--nocolor] [--noenable] [--noexec] [--nofile]
				 [--nohashed] [--noignore] [--nomake] [--preconfig PRECONFIG] [--postconfig POSTCONFIG]
				 [--py:closebrace PYCLOSEBRACE] [--py:enable PYENABLE] [--py:makecommand PYMAKECOMMAND]
				 [--py:makefunction PYMAKEFUNCTION] [--py:openbrace PYOPENBRACE] [--py:priority PYPRIORITY]
				 [--sleepmake SLEEPMAKE] [--sleepcommand SLEEPCOMMAND] [--suppress] [--verbose VERBOSE] [--workers WORKERS]
				 ...
	
	walks filesystem executing arbitrary commands
	
	positional arguments:
	  rest

	optional arguments:
	  -h, --help                        show this help message and exit
	  --chdir CHDIR                     chdir first
	  --color                           enables colorized output
	  --comment COMMENT                 ignored
	  --configfile CONFIGFILE           config file
	  --count COUNT                     count for substitutions
	  --debug                           debug flag
	  --depth DEPTH                     walk depth
	  --disable DISABLE                 disable section
	  --discard                         discard error codes
	  --dump DUMP                       dump section
	  --dumpall                         dump all sections
	  --enable ENABLE                   enable section
	  --file FILE                       file with folder names
	  --hashed                          check hashes of unknown files
	  --ignore IGNORE                   ignore folder names
	  --invert                          invert error codes
	  --make                            make folders
	  --nocolor                         disables colorized output
	  --noenable                        no longer enable any sections
	  --noexec                          do not actually execute
	  --nofile                          ignore file options
	  --nohashed                        do not check hashes of unknown files
	  --noignore                        ignore ignore options
	  --nomake                          do not make folders
	  --preconfig PRECONFIG             preconfig option
	  --postconfig POSTCONFIG           postconfig option
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
Type: Flag<br />
Default: \<none><br />
Option: \<none><br />
Repeat: No<br /><br />
Outputs command line options (see above).
### --chdir CHDIR
	--chdir CHDIR                     chdir first
Type: Option<br />
Default: \<none><br />
Option `CHDIR`<br />
Repeat: Yes<br /><br />
Changes directory before execution.
### --color
	--color                           enables colorized output
Type: Flag<br />
Default: True<br />
Option: \<none><br />
Repeat: No<br /><br />
Enables colorized output.
### --comment COMMENT
	--comment COMMENT                 ignored
Type: Option<br />
Default: \<none><br />
Option: `COMMENT`<br />
Repeat: Yes<br /><br />
Ignored. Can be used to document scripted command lines.
### --configfile CONFIGFILE
	--configfile CONFIGFILE           config file
Type: Option<br />
Default: \<home folder>/.onsub.py<br />
Option: `CONFIGFILE`<br />
Repeat: No<br /><br />
Names `CONFIGFILE` to be the configuration file to be loaded.
### --count COUNT
	--count COUNT                     count for substitutions
Type: Option<br />
Default: 10<br />
Option: `COUNT`<br />
Repeat: No<br /><br />
Indicates that `COUNT` is the maximum number of times to recursively substitute configuration entries to prevent infinite recursion.
### --debug
	--debug                           debug flag
Type: Flag<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Causes `onsub` to output more diagnostic information. Is also passed to `py:` functions where they occur in configuration entries.
### --depth DEPTH
	--depth DEPTH                     walk depth
Type: Option<br />
Default: -1<br />
Option: `DEPTH`<br />
Repeat: No<br /><br />
If greater than zero, limits the filesystem depth that is walked by `onsub` to folder entries with up to `DEPTH`-many subdirectories.
### --disable DISABLE
	--disable DISABLE                 disable section
Type: Option<br />
Default: None<br />
Option: `DISABLE`<br />
Repeat: Yes<br /><br />
Disables section `DISABLE` that would otherwise be enabled by configuration file or command line option. Takes precedence over all other means of enabling sections.
### --discard
	--discard                         discard error codes
Type: Flag<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Whether to discard error codes.
### --dump DUMP
	--dump DUMP                       dump section
Type: Option<br />
Default: None<br />
Option: `DUMP`<br />
Repeat: Yes<br /><br />
Outputs configuration section `DUMP`. Can dump multiple configuration sections. Can be used to remember how command substitutions will be generated.
### --dumpall
	--dumpall                         dump all sections
Type: Flag<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Dumps all configuration sections.
### --enable ENABLE
	--enable ENABLE                   enabled sections
Type: Option<br />
Default: None<br />
Option: `ENABLE`<br />
Repeat: Yes<br /><br />
Enables section `ENABLE` that would otherwise be disabled by configuration file or command line option. Takes precedence over default disable and configuration file.
### --file FILE
	--file FILE                       file with folder names
Type: Option<br />
Default: None<br />
Option: `FILE`<br />
Repeat: Yes<br /><br />
Reads `FILE` as list of folders to be operated on instead of recursively scanning filesystem. Missing folders will be generated by `py:makecommand` or `py:makefunction` if available and in that order.
### --hashed
	--hashed                          check hashes of unknown files
Type: Flag<br />
Default: True<br />
Option: \<none><br />
Repeat: No<br /><br />
Whether to check hashes of `--file FILE` file parameters. Prevents untrusted code from executing by accident.
### --ignore IGNORE
	--ignore IGNORE                   ignore folder names
Type: Option<br />
Default: None<br />
Option: `IGNORE`<br />
Repeat: Yes<br /><br />
Sets folder names that will not be visited when recursively searching file system.
### --invert
	--invert                          invert error codes
Type: Flag<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Whether to invert error codes.
### --make
	--make                            make folders
Type: Flag<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Indicates that missing folders should be created. This can be useful when folders will need to be generated because of `--file FILE` command line option.
### --nocolor
	--nocolor                         disables colorized output
Type: Flag<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Turns off color in output.
### --noenable
	--noenable                        no longer enable any sections
Type: Option<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Defaults all configuration sections to not be enabled. This can be changed later for each configuration section with other command line options.
### --noexec
	--noexec                          do not actually execute
Type: Flag<br />
Default: False<br />
Option: \<none>
Repeat: No<br /><br />
Causes commands to be printed to the console but not actually executed.
### --nofile
	--nofile                          ignore file options
Type: Flag<br />
Default: False<br />
Option: \<none>
Repeat: No<br /><br />
Disables reading files passed to `--file FILE`. This can be useful if a default command line is used.
### --nohashed
	--nohashed                        do not check hashes of unknown files
Type: Flag<br />
Default: False<br />
Option: \<none>
Repeat: No<br /><br />
Disables checking of hashes of `--file FILE` files.
### --noignore
	--noignore                        ignore ignore options
Type: Flag<br />
Default: False<br />
Option: \<none>
Repeat: No<br /><br />
Disables `--ignore IGNORE` command line options. This can be useful if there's a default ignore in `arguments`.
### --nomake
	--nomake                          do not make folders
Type: Flag<br />
Default: False<br />
Option: \<none>
Repeat: No<br /><br />
Disables `--make` command line option. This can be useful if that arument is on by default in `arguments`.
### --postconfig POSTCONFIG
	--postconfig POSTCONFIG           postconfig option
Type: Option<br />
Default: None<br />
Option: `POSTCONFIG`<br />
Repeat: Yes<br /><br />
Appends `POSTCONFIG` lines to configuration, one at a time. Can be used to alter configuration for a single command execution.
### --preconfig PRECONFIG
	--preconfig PRECONFIG             preconfig option
Type: Option<br />
Default: None<br />
Option: `PRECONFIG`<br />
Repeat: Yes<br /><br />
Prepends `PRECONFIG` lines to configuration, one at a time. Can be used to alter configuration for a single command execution.
### --py:closebrace PYCLOSEBRACE
	--py:closebrace PYCLOSEBRACE      key for py:closebrace
Type: Option<br />
Default: %]<br />
Option: `PYCLOSEBRACE`
Repeat: No<br /><br />
Sets the substitution string for a literal close brace.
### --py:enable PYENABLE
	--py:enable PYENABLE              key for py:enable
Type: Option<br />
Default: py:enable<br />
Option: `PYENABLE `<br />
Repeat: No<br /><br />
Names `PYENABLE ` as the key to look up in each configuration section for determining if the section is enabled by default.
### --py:makecommand PYMAKECOMMAND
	--py:makecommand PYMAKECOMMAND    key for py:makecommand
Type: Option<br />
Default: py:makecommand<br />
Option: `PYMAKECOMMAND`<br />
Repeat: No<br /><br />
Names `PYMAKECOMMAND` as the key to look up in each configuration section for generating commands to make folders.
### --py:makefunction PYMAKEFUNCTION
	--py:makefunction PYMAKEFUNCTION  key for py:makefunction
Type: Option<br />
Default: py:makefunction<br />
Option: `PYMAKEFUNCTION`<br />
Repeat: No<br /><br />
Names `PYMAKEFUNCTION` as the key to look up in each configuration section for executing python commands to make folders.
### --py:openbrace PYOPENBRACE
	--py:openbrace PYOPENBRACE        key for py:openbrace
Type: Option<br />
Default: %[<br />
Option: `PYOPENBRACE`
Repeat: No<br /><br />
Sets the substitution string for a literal open brace.
### --py:pypriority PYPRIORITY
	--py:pypriority PYPRIORITY        key for py:priority
Type: Option<br />
Default: py:priority<br />
Option: `PYPRIORITY`<br />
Repeat: No<br /><br />
Names `PYPRIORITY` as the key to look up in each configuration section for checking to see if a section applies to a folder.
### --sleepmake SLEEPMAKE
	--sleepmake SLEEPMAKE             sleep between make calls
Type: Option<br />
Default: 0.1<br />
Option: `SLEEPMAKE`<br />
Repeat: No<br /><br />
Sets the sleep value to issue between make folder commands. Can be used to throttle server connections.
### --sleepcommand SLEEPCOMMAND
	--sleepcommand SLEEPCOMMAND       sleep between command calls
Type: Option<br />
Default: 0<br />
Option: `SLEEPCOMMAND `<br />
Repeat: No<br /><br />
Sets the sleep value to issue between recursive commands. Can be used to throttle server connections.
### --suppress
	--suppress                        suppress repeated error output
Type: Flag<br />
Default: False<br />
Option: \<none><br />
Repeat: No<br /><br />
Indicates that summary information for errors should not be output at end of execution. Output will otherwise be included depending on `--verbose` flag.
### --verbose VERBOSE
	--verbose VERBOSE                 verbose level
Type: Option<br />
Default: 4<br />
Option: `VERBOSE`<br />
Repeat: No<br /><br />
Sets the level of output to be included in command execution where higher numbers include output of lower numbers:<br />
0. No output<br />
1. Only errors, at end of parallel execution<br />
2. Output of commands<br />
3. Output path, applicable section, and command<br />
4. Output one line for each command (at point of execution)<br />
5. Output of commands as execution finishes<br />
6. Output of make commands as make execution finishes<br />
### --workers WORKERS
	--workers WORKERS                 number of workers
Type: Option<br />
Default: \<number of cores><br />
Option: `WORKERS`<br />
Repeat: No<br /><br />
Sets the number of simultaneous worker processes to use.
## Simple Examples
Simple examples of using `onsub` are below. It is executed on a Mac and the directory structure is assumed to be the following:

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
	svn (svn) pwd
	hg (hg) pwd
	git (git) pwd
	<<< RESULTS >>>
	svn (svn) pwd
	/private/tmp/sample/svn
	hg (hg) pwd
	/private/tmp/sample/hg
	git (git) pwd
	/private/tmp/sample/git
Identifies `svn` as a `Subversion` folder, `hg` as a `Mercurial`, and `git` as a `Git` folder and executes `pwd` in those folders.
### Do not enable by default (--noenable)
With `--noenable`:

	$ onsub --noenable pwd
No sections are enabled so no commands are executed.
### Enable section (--enable ENABLE)
With `--noenable --enable git`:

	$ onsub --noenable --enable git pwd
	git (git) pwd
	<<< RESULTS >>>
	git (git) pwd
	/private/tmp/sample/git
Identifies `git` as `Git` folder and executes command. Only `git` section is applied.
### Disable section (--disable DISABLE)
With `--disable svn --disable hg`:

	$ onsub --disable svn --disable hg pwd
	git (git) pwd
	<<< RESULTS >>>
	git (git) pwd
	/private/tmp/sample/git
Identifies `git` as `Git` folder and executes command. Only `git` section is applied.
### Ignore folders (---ignore IGNORE [--ignore IGNORE ...])
With `--noenable --enable all --ignore .git --ignore .hg --ignore .svn`:

	$ onsub --noenable --enable all --ignore .git --ignore .hg --ignore .svn pwd
	. (all) pwd
	svn (all) pwd
	normal (all) pwd
	hg (all) pwd
	git (all) pwd
	<<< RESULTS >>>
	. (all) pwd
	/tmp/sample
	svn (all) pwd
	/private/tmp/sample/svn
	hg (all) pwd
	/private/tmp/sample/hg
	git (all) pwd
	/private/tmp/sample/git
	normal (all) pwd
	/private/tmp/sample/normal
Visits all folder without traversing into ignored folders to execute command. 
### Dump config (--dump DUMP [--dump DUMP ...])
With `--dump default`:

	$ onsub --dump default
	default = {
		onsub = onsub
		cwd = <function <lambda> at 0x10bafec20>
		sep = ;
		echo = /bin/echo
	}
With `--dump git`:

	$ onsub --dump git
	git = {
		onsub = onsub
		cwd = <function <lambda> at 0x10f916c20>
		sep = ;
		echo = /bin/echo
		type = echo '(git)' {cwd}
		ctype = echo '(git)' {cwd}
		py:priority = <function gitpriority at 0x10f916d40>
		py:makecommand = <function gitmakecommand at 0x10f916cb0>
		cmd = git
		remote = {cmd} remote get-url origin
		allremote = {cmd} remote -v
		wcrev = {cmd} rev-parse --verify --short HEAD
		py:enable = True
	}
With `--dump hg`:

	$ onsub --dump hg
	hg = {
		onsub = onsub
		cwd = <function <lambda> at 0x10b0d7c20>
		sep = ;
		echo = /bin/echo
		type = echo '(hg)' {cwd}
		ctype = echo '(hg)' {cwd}
		py:priority = <function hgpriority at 0x10b0d7e60>
		py:makecommand = <function hgmakecommand at 0x10b0d7dd0>
		cmd = hg
		wcrev = {cmd} id -i
		remote = {cmd} paths default
		allremote = {echo} -n "default = "; {cmd} paths default; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull
		py:enable = True
	}
With `--dump svn`:

	$ onsub --dump svn
	svn = {
		onsub = onsub
		cwd = <function <lambda> at 0x10cba5c20>
		sep = ;
		echo = /bin/echo
		type = echo '(svn)' {cwd}
		ctype = echo '(svn)' {cwd}
		py:priority = <function svnpriority at 0x10cba5f80>
		py:makecommand = <function svnmakecommand at 0x10cba5ef0>
		cmd = svn
		remote = {cmd} info --show-item url
		allremote = {remote}
		wcrev = {cmd} info --show-item revision
		py:enable = True
	}
With `--dump all`:

	$ onsub --dump all
	all = {
		onsub = onsub
		cwd = <function <lambda> at 0x1013c8c20>
		sep = ;
		echo = /bin/echo
		type = echo '(all)' {cwd}
		ctype = {type}
		py:priority = <function allpriority at 0x1013cd0e0>
		py:makefunction = <function allmakefunction at 0x1013cd050>
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
	svn (svn) pwd
	normal (all) pwd
	hg (hg) pwd
	git (git) pwd
	<<< RESULTS >>>
	. (all) pwd
	/tmp/sample
	svn (svn) pwd
	/private/tmp/sample/svn
	git (git) pwd
	/private/tmp/sample/git
	normal (all) pwd
	/private/tmp/sample/normal
	hg (hg) pwd
	/private/tmp/sample/hg
Recurses an additional level into working copies.

With `--enable all --depth 3`:

	$ onsub --enable all --depth 3 pwd
	. (all) pwd
	svn (svn) pwd
	svn/.svn (all) pwd
	normal (all) pwd
	hg (hg) pwd
	hg/.hg (all) pwd
	git (git) pwd
	git/.git (all) pwd
	<<< RESULTS >>>
	. (all) pwd
	/tmp/sample
	svn (svn) pwd
	/private/tmp/sample/svn
	svn/.svn (all) pwd
	/private/tmp/sample/svn/.svn
	hg (hg) pwd
	/private/tmp/sample/hg
	normal (all) pwd
	/private/tmp/sample/normal
	hg/.hg (all) pwd
	/private/tmp/sample/hg/.hg
	git (git) pwd
	/private/tmp/sample/git
	git/.git (all) pwd
	/private/tmp/sample/git/.git
Recurses an additional level into working copy version control folders.
### No execution (--noexec)
With `--noexec pwd`:

	$ onsub --noexec pwd
	svn (svn) pwd
	hg (hg) pwd
	git (git) pwd
	<<< RESULTS >>>
	svn (svn) pwd
	[noexec] pwd
	hg (hg) pwd
	[noexec] pwd
	git (git) pwd
	[noexec] pwd
Identifies `svn` as a `Subversion` folder, `hg` as a `Mercurial`, and `git` as a `Git` folder but only outputs the command that would have been executed.
## Git examples
Complex Git examples of using `onsub` are below. It is executed on a Mac and the file `input.py` is assumed to contain the following:

	git = [
		("./onsub1", "https://bitbucket.org/sawolford/onsub.git"),
		("./onsub2", "https://bitbucket.org/sawolford/onsub.git"),	]
### Input file (--file FILE)
With `--file input.py --make`:

	$ onsub --file input.py --make
	./onsub1 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub1
	./onsub2 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub2
	<<< MAKE >>>
	./onsub2 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub2
	Cloning into './onsub2'...
	./onsub1 (git) git clone https://bitbucket.org/sawolford/onsub.git ./onsub1
	Cloning into './onsub1'...
Clones `onsub` `git` repository locally.
### Git fetch
With `--file input.py {cmd} fetch -v`

	$ onsub --file input.py {cmd} fetch -v
	onsub1 (git) git fetch -v
	onsub2 (git) git fetch -v
	<<< RESULTS >>>
	onsub1 (git) git fetch -v
	From https://bitbucket.org/sawolford/onsub
	 = [up to date]      master     -> origin/master
	onsub2 (git) git fetch -v
	From https://bitbucket.org/sawolford/onsub
	 = [up to date]      master     -> origin/master
Fetches changesets and outputs current local branch and upstream branch.
### Git pull
With `--file input.py {cmd} pull`

	$ onsub --file input.py {cmd} pull    
	onsub1 (git) git pull
	onsub2 (git) git pull
	<<< RESULTS >>>
	onsub2 (git) git pull
	Already up to date.
	onsub1 (git) git pull
Already up to date.
### Selective folder git pull
With `--chdir onsub1 {cmd} pull`:

	$ onsub --chdir onsub1 {cmd} pull
	. (git) git pull
	<<< RESULTS >>>
	. (git) git pull
	Already up to date.
Changes directory to `onsub1` and executes `pull` command.
## Complex Examples
Complex examples of using `onsub` are below. It is executed on a Mac and the configuration file is assumed to include [onsubcheck.py](https://bitbucket.org/sawolford/onsub/src/master/config/onsubcheck.py). Also, assume that the shell scripts [gitcheck](https://bitbucket.org/sawolford/onsub/src/master/scripts/gitcheck.py), [hgcheck](https://bitbucket.org/sawolford/onsub/src/master/scripts/hgcheck.py), [svncheck](https://bitbucket.org/sawolford/onsub/src/master/scripts/svncheck.py) are on the shell command search path.

Prepare the sample folder with the following shell script:

	#!/bin/sh
	mkdir repo
	mkdir wc
	cd repo
	svnadmin create svn
	git init --bare git
	hg init hg
	cd ../wc
	svn co file://$(realpath $(pwd)/../repo/svn) ./svn1
	svn co file://$(realpath $(pwd)/../repo/svn) ./svn2
	git clone ../repo/git ./git1
	git clone ../repo/git ./git2
	hg clone ../repo/hg ./hg1
	hg clone ../repo/hg ./hg2
	cd svn1
	echo "svn1" > file.txt
	svn add file.txt
	svn ci -m "svn1"
	echo "svn1 svn1" > file.txt
	cd ../svn2
	svn up
	echo "svn1 svn2" > file.txt
	cd ../git1
	echo "git1" > file.txt
	git add file.txt
	git ci -a -m "git1"
	git push
	echo "git1 git1" > file.txt
	cd ../git2
	git pull
	echo "git1 git2" > file.txt
	git ci -a -m "git2"
	echo "git1 git2 git2" > file.txt
	cd ../hg1
	echo "hg1" > file.txt
	hg add file.txt
	hg ci -m "hg1"
	hg push
	echo "hg1 hg1" > file.txt
	cd ../hg2
	hg pull
	hg update
	echo "hg1 hg2" > file.txt
	hg ci -m "hg2"
	echo "hg1 hg2 hg2" > file.txt
At this point, there are "remote" repositorues (`repo/git`, `repo/hg`, `repo/svn`), local clones with working copy changes (`wc/git1`, `wc/hg1`, `wc/svn1`, `wc/svn2`), and local clones with local commits (`wc/git2`, `wc/hg2`). The following example commands are run from the `wc` subfolder.
### Git
Git cannot check the remote server without fetching first but it does track the remote branches even after fetching. With those limitations and benefits, `onsub` can easily support six (6) operations: `get`, `put`, `download`, `upload`, `download-get`, `put-upload`:

- `get`          -- fetches and merges with working copy (remote is unchanged)
- `put`          -- commits local changes (remote is unchanged)
- `download`     -- fetches and rebases {working copy and remote are unchanged)
- `upload`       -- pushes local commits (working copy and local are unchanged)
- `download-get` -- fetches, rebases and merges with working copy (remote is unchanged)
- `put-upload`   -- commits local changes and pushes local commits to remote

Determine the  current state of the `git` clones with `{check}`:

	$ onsub --disable hg --disable svn check
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=1,sh=0,out=0,in=0" {put}
	git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	<<< ERRORS >>>
	(8) git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=1,sh=0,out=0,in=0" {put}
	(4) git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
Error `8` indicates that the `git` folder has local changes to commit. The output command for that error instructs how those folders might be brought to a clean working copy and synced local clone.

We can execute the `put` command to commit the working copy changes:

	$ onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=1,sh=0,out=0,in=0" {put}
	. (git) git commit -a -e -m "# $(pwd)"
	<<< RESULTS >>>
	. (git) git commit -a -e -m "# $(pwd)"
	[master 6c1e32b] git1
	 1 file changed, 1 insertion(+), 1 deletion(-)
	 
	 $ onsub --disable hg --disable svn check                                                 
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
	<<< ERRORS >>>
	(4) git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	(5) git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
Error `5` indicates that the `git1` folder has commits to upload to the remote server. We can execute the `upload` command to push those commits:

	$ onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
	. (git) git push
	<<< RESULTS >>>
	. (git) git push
	To /tmp/all/wc/../repo/git
	   278f253..6c1e32b  master -> master
	
	$ onsub --disable hg --disable svn check                                                    
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git1 (git) gitcheck
	[no local mods, no repository changes]
	git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=1" {download-get}
	<<< ERRORS >>>
	(6) git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=1" {download-get}
Error `6` indicates that the `git2` folder has commits to sync from the remote server. We can execute the `download-get` command to pull those commits:

	$ onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=1" {download-get}
	. (git) git fetch ; git stash ; git rebase origin/master ; git mergetool -y --tool=kdiff3 ; git rebase --continue ; git merge origin/master ; git stash pop ; git mergetool -y --tool=kdiff3 ; git reset --mixed ; git stash clear
	<<< RESULTS >>>
	. (git) git fetch ; git stash ; git rebase origin/master ; git mergetool -y --tool=kdiff3 ; git rebase --continue ; git merge origin/master ; git stash pop ; git mergetool -y --tool=kdiff3 ; git reset --mixed ; git stash clear
	Saved working directory and index state WIP on master: ff1f28a git2
	First, rewinding head to replay your work on top of it...
	Applying: git2
	Using index info to reconstruct a base tree...
	M       file.txt
	Falling back to patching base and 3-way merge...
	Auto-merging file.txt
	CONFLICT (content): Merge conflict in file.txt
	error: Failed to merge in the changes.
	hint: Use 'git am --show-current-patch' to see the failed patch
	Patch failed at 0001 git2
	Resolve all conflicts manually, mark them as resolved with "git add/rm <conflicted_files>", then run "git rebase --continue".
	You can instead skip this commit: run "git rebase --skip".
	To abort and get back to the state before "git rebase", run "git rebase --abort".
	Merging:
	file.txt
	
	Normal merge conflict for 'file.txt':
	  {local}: modified file
	  {remote}: modified file
	Applying: git2
	Already up to date.
	Auto-merging file.txt
	CONFLICT (content): Merge conflict in file.txt
	The stash entry is kept in case you need it again.
	Merging:
	file.txt
	
	Normal merge conflict for 'file.txt':
	  {local}: modified file
	  {remote}: modified file
	Unstaged changes after reset:
	M       file.txt
	
	$ onsub --disable hg --disable svn check                                                          
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	git1 (git) gitcheck
	[no local mods, no repository changes]
	<<< ERRORS >>>
	(4) git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
Error `4` indicates that the `git2` folder has local working copy changes and commits to push to the remote server. We can execute the `put-upload` command to commit and push those changesets:

	$ onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	. (git) git commit -a -e -m "# $(pwd)" ; git push
	<<< RESULTS >>>
	. (git) git commit -a -e -m "# $(pwd)" ; git push
	[master 6c6bff9] git2
	 1 file changed, 1 insertion(+), 1 deletion(-)
	To /tmp/all/wc/../repo/git
	   6c1e32b..6c6bff9  master -> master
	
	$ onsub --disable hg --disable svn check                                                        
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git2 (git) gitcheck
	[no local mods, no repository changes]
	git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=0,in=2" {get}
	<<< ERRORS >>>
	(3) git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=0,in=2" {get}
Error `3` indicates that the `git1` folder has changesets to sync with the remote server. We're going to muck things up a bit, though, and create a outgoing changeset first:

	$ cd git1
	$ echo "git1 git1 git1" > file.txt
	$ git ci -a -m "more git1"
	[master 8027957] more git1
	 1 file changed, 1 insertion(+), 1 deletion(-)
 	$ cd ..
 	$ onsub --disable hg --disable svn check                                                        
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git2 (git) gitcheck
	[no local mods, no repository changes]
	git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=2" {download}
	<<< ERRORS >>>
	(7) git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=2" {download}
Error `7` indicates that the `git1` foler has changesets to rebase with the remote server. We can execute the `download` command to pull and rebase those changesets:

	$ onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=2" {download}
	. (git) git fetch ; git stash ; git rebase origin/master ; git mergetool -y --tool=kdiff3 ; git rebase --continue
	<<< RESULTS >>>
	. (git) git fetch ; git stash ; git rebase origin/master ; git mergetool -y --tool=kdiff3 ; git rebase --continue
	No local changes to save
	First, rewinding head to replay your work on top of it...
	Applying: more git1
	Using index info to reconstruct a base tree...
	M       file.txt
	Falling back to patching base and 3-way merge...
	Auto-merging file.txt
	CONFLICT (content): Merge conflict in file.txt
	error: Failed to merge in the changes.
	hint: Use 'git am --show-current-patch' to see the failed patch
	Patch failed at 0001 more git1
	Resolve all conflicts manually, mark them as resolved with "git add/rm <conflicted_files>", then run "git rebase --continue".
	You can instead skip this commit: run "git rebase --skip".
	To abort and get back to the state before "git rebase", run "git rebase --abort".
	Merging:
	file.txt
	
	Normal merge conflict for 'file.txt':
	  {local}: modified file
	  {remote}: modified file
	Applying: more git1
	
	$ onsub --disable hg --disable svn check                                                      
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git2 (git) gitcheck
	[no local mods, no repository changes]
	git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
	<<< ERRORS >>>
	(5) git1 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
Error `5` again indicates that the `git1` folder has commits to upload to the remote server. We can execute the `upload` command to push those commits:

	$ onsub --chdir /private/tmp/all/wc/git1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
	. (git) git push
	<<< RESULTS >>>
	. (git) git push
	To /tmp/all/wc/../repo/git
	   6c6bff9..624c52a  master -> master
	
	$ onsub --disable hg --disable svn check                                                    
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=0,sh=0,out=0,in=1" {get}
	git1 (git) gitcheck
	[no local mods, no repository changes]
	<<< ERRORS >>>
	(3) git2 (git) gitcheck
	onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=0,sh=0,out=0,in=1" {get}
Error `3` indicates that the `git2` folder has commits to pull from the remote server. We can execute the `get` command to pull those commits:

	$ onsub --chdir /private/tmp/all/wc/git2 --depth 1 --comment "wc=0,sh=0,out=0,in=1" {get}
	. (git) git stash pop ; git mergetool -y --tool=kdiff3 ; git reset --mixed ; git stash clear ; git stash ; git merge origin/master ; git stash pop ; git mergetool -y --tool=kdiff3 ; git reset --mixed ; git stash clear
	<<< RESULTS >>>
	. (git) git stash pop ; git mergetool -y --tool=kdiff3 ; git reset --mixed ; git stash clear ; git stash ; git merge origin/master ; git stash pop ; git mergetool -y --tool=kdiff3 ; git reset --mixed ; git stash clear
	No stash entries found.
	No files need merging
	No local changes to save
	Updating 6c6bff9..624c52a
	Fast-forward
	 file.txt | 2 +-
	 1 file changed, 1 insertion(+), 1 deletion(-)
	No stash entries found.
	No files need merging
	
	$ onsub --disable hg --disable svn check                                                 
	git2 (git) gitcheck
	git1 (git) gitcheck
	<<< RESULTS >>>
	git2 (git) gitcheck
	[no local mods, no repository changes]
	git1 (git) gitcheck
	[no local mods, no repository changes]
Now, all `Git` repositories are up to date.
### Mercurial
Mercurial can check the remote server without pulling but it does not track the remote branches after pulling. With those limitations and benefits, `onsub` can only easily support four (4) operations: `put`, `upload`, `put-upload` and `download-get`:

- `put`          -- commits local changes (remote is unchanged)
- `upload`       -- pushes local commits (working copy and local are unchanged)
- `put-upload`   -- commits local changes and pushes local commits to remote
- `download-get` -- pulls, rebases and merges with working copy (remote is unchanged)

Determine the current state of the `hg` clones with `{check}`:

	$ onsub --disable git --disable svn check
	hg1 (hg) hgcheck
	hg2 (hg) hgcheck
	<<< RESULTS >>>
	hg1 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=1,sh=0,out=0,in=0" {put}
	hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	<<< ERRORS >>>
	(8) hg1 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=1,sh=0,out=0,in=0" {put}
	(4) hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
Error `8` indicates that the `hg1` folder has local changes to commit. The output command for that error instructs how those folders might be brought to a clean working copy and synced local clone.

We can execute the `put` command to commit the working copy changes:

	$ onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=1,sh=0,out=0,in=0" {put}
	. (hg) hg commit -e -m "HG: $(pwd)"
	<<< RESULTS >>>
	. (hg) hg commit -e -m "HG: $(pwd)"
	
	$ onsub --disable git --disable svn check                                               
	hg1 (hg) hgcheck
	hg2 (hg) hgcheck
	<<< RESULTS >>>
	hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	hg1 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
	<<< ERRORS >>>
	(4) hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	(5) hg1 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
Error `5` indicates that the `hg1` folder has commits to upload to the remote server. We can execute the `upload` command to push those commits:

	$ onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=0,sh=0,out=1,in=0" {upload}
	. (hg) hg push
	<<< RESULTS >>>
	. (hg) hg push
	pushing to /private/tmp/all/repo/hg
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files
	
	$ onsub --disable git --disable svn check                                                  
	hg1 (hg) hgcheck
	hg2 (hg) hgcheck
	<<< RESULTS >>>
	hg1 (hg) hgcheck
	[no local mods, no repository changes]
	hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=1" {download-get}
	<<< ERRORS >>>
	(6) hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=1" {download-get}
Error `6` indicates that the `hg2` folder has commits to sync from the remote server. We can execute the `download-get` command to pull those commits:

	$ onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=1" {download-get}
	. (hg) hg shelve ; hg pull --rebase ; hg update ; hg unshelve
	<<< RESULTS >>>
	. (hg) hg shelve ; hg pull --rebase ; hg update ; hg unshelve
	shelved as default
	1 files updated, 0 files merged, 0 files removed, 0 files unresolved
	pulling from /private/tmp/all/repo/hg
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 1 changesets with 1 changes to 1 files (+1 heads)
	new changesets 0adefd4c3fbb
	rebasing 1:f3fd648e6321 "hg2"
	merging file.txt
	running merge tool kdiff3 for file file.txt
	saved backup bundle to /private/tmp/all/wc/hg2/.hg/strip-backup/f3fd648e6321-a76485e0-rebase.hg
	0 files updated, 0 files merged, 0 files removed, 0 files unresolved
	unshelving change 'default'
	rebasing shelved changes
	merging file.txt
	running merge tool kdiff3 for file file.txt
	
	$ onsub --disable git --disable svn check                                                        
	hg1 (hg) hgcheck
	hg2 (hg) hgcheck
	<<< RESULTS >>>
	hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
	hg1 (hg) hgcheck
	[no local mods, no repository changes]
	<<< ERRORS >>>
	(4) hg2 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}
Error `4` indicates that the `hg2` folder has local working copy changes and commits to push to the remote server. We can execute the `put-upload` command to commit and push those changesets:

	$ onsub --chdir /private/tmp/all/wc/hg2 --depth 1 --comment "wc=1,sh=0,out=1,in=0" {put-upload}  
	. (hg) hg commit -e -m "HG: $(pwd)" ; hg push
	<<< RESULTS >>>
	. (hg) hg commit -e -m "HG: $(pwd)" ; hg push
	pushing to /private/tmp/all/repo/hg
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 2 changesets with 2 changes to 1 files
	
	$ onsub --disable git --disable svn check                                                      
	hg1 (hg) hgcheck
	hg2 (hg) hgcheck
	<<< RESULTS >>>
	hg2 (hg) hgcheck
	[no local mods, no repository changes]
	hg1 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=0,sh=0,out=0,in=2" {download-get}
	<<< ERRORS >>>
	(3) hg1 (hg) hgcheck
	onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=0,sh=0,out=0,in=2" {download-get}
Error `3` again indicates that the `hg1` folder has commits to sync from the remote server. Executing one last `download-get` command:

	$ onsub --chdir /private/tmp/all/wc/hg1 --depth 1 --comment "wc=0,sh=0,out=0,in=2" {download-get}
	. (hg) hg shelve ; hg pull --rebase ; hg update ; hg unshelve
	<<< RESULTS >>>
	. (hg) hg shelve ; hg pull --rebase ; hg update ; hg unshelve
	nothing changed
	pulling from /private/tmp/all/repo/hg
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 2 changesets with 2 changes to 1 files
	new changesets 0151632719df:24003a29bcf6
	nothing to rebase - updating instead
	1 files updated, 0 files merged, 0 files removed, 0 files unresolved
	0 files updated, 0 files merged, 0 files removed, 0 files unresolved
	abort: no shelved changes to apply!
	<<< ERRORS >>>
	(255) . (hg) hg shelve ; hg pull --rebase ; hg update ; hg unshelve
	nothing changed
	pulling from /private/tmp/all/repo/hg
	searching for changes
	adding changesets
	adding manifests
	adding file changes
	added 2 changesets with 2 changes to 1 files
	new changesets 0151632719df:24003a29bcf6
	nothing to rebase - updating instead
	1 files updated, 0 files merged, 0 files removed, 0 files unresolved
	0 files updated, 0 files merged, 0 files removed, 0 files unresolved
	abort: no shelved changes to apply!
	
	$ onsub --disable git --disable svn check                                                        
	hg1 (hg) hgcheck
	hg2 (hg) hgcheck
	<<< RESULTS >>>
	hg1 (hg) hgcheck
	[no local mods, no repository changes]
	hg2 (hg) hgcheck
	[no local mods, no repository changes]
Now, all `Mercurial` repositories are up to date.
### Subversion
Subversion does not support local changesets. With that limitation, `onsub` can only support two (2) operations: `put-upload` and `download-get`:

- `put-upload`   -- commits local to remote
- `download-get` -- merges with working copy (remote is unchanged)

Determine the current state of the `svn` clones with `{check}`:

	$ onsub --disable git --disable hg check
	svn2 (svn) svncheck
	svn1 (svn) svncheck
	<<< RESULTS >>>
	svn2 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=0" {put-upload}
	svn1 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn1 --depth 1 --comment "wc=1,in=0" {put-upload}
	<<< ERRORS >>>
	(3) svn2 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=0" {put-upload}
	(3) svn1 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn1 --depth 1 --comment "wc=1,in=0" {put-upload}
Error `3` indicates that the `svn1` and `svn2` folders have local changes to commit. The output command for that error instructs how those folders might be brought to a clean working copy and synced local clone.

We can execute the `put-upload` command to sync the `svn1` working copy with the remote server:

	$ onsub --chdir /private/tmp/all/wc/svn1 --depth 1 --comment "wc=1,in=0" {put-upload}
	. (svn) svn commit
	<<< RESULTS >>>
	. (svn) svn commit
	Sending        file.txt
	Transmitting file data .done
	Committing transaction...
	Committed revision 2.
	
	$ onsub --disable git --disable hg check                                             
	svn2 (svn) svncheck
	svn1 (svn) svncheck
	<<< RESULTS >>>
	svn1 (svn) svncheck
	[no local mods, no repository changes]
	svn2 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=1" {download-get}
	<<< ERRORS >>>
	(2) svn2 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=1" {download-get}
Error `2` indicates that the `svn2` working copy has remote changes to merge. We can execute a `download-get` command to merge with the `svn2` working copy:

	$ onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=1" {download-get}
	. (svn) svn update --accept l
	<<< RESULTS >>>
	. (svn) svn update --accept l
	Updating '.':
	C    file.txt
	Updated to revision 2.
	Merge conflicts in 'file.txt' marked as resolved.
	Summary of conflicts:
	  Text conflicts: 0 remaining (and 1 already resolved)
	
	$ onsub --disable git --disable hg check                                               
	svn2 (svn) svncheck
	svn1 (svn) svncheck
	<<< RESULTS >>>
	svn2 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=0" {put-upload}
	svn1 (svn) svncheck
	[no local mods, no repository changes]
	<<< ERRORS >>>
	(3) svn2 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=0" {put-upload}
Error `3` again indicates that the `svn2` folder has local changes to sync with the remote server. We can execute another `put-upload` command to sync the `svn2` working copy with the remote server:

	$onsub --chdir /private/tmp/all/wc/svn2 --depth 1 --comment "wc=1,in=0" {put-upload}
	. (svn) svn commit
	<<< RESULTS >>>
	. (svn) svn commit
	Sending        file.txt
	Transmitting file data .done
	Committing transaction...
	Committed revision 3.
	
	$ onsub --disable git --disable hg check                                             
	svn2 (svn) svncheck
	svn1 (svn) svncheck
	<<< RESULTS >>>
	svn2 (svn) svncheck
	[no local mods, no repository changes]
	svn1 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn1 --depth 1 --comment "wc=0,in=1" {download-get}
	<<< ERRORS >>>
	(2) svn1 (svn) svncheck
	onsub --chdir /private/tmp/all/wc/svn1 --depth 1 --comment "wc=0,in=1" {download-get}
Error `2` again indicates that the `svn1` folder has remote changes to update. We can execute another `download-get` command to sync the `svn1` workding copy with the remote server:

	$ onsub --chdir /private/tmp/all/wc/svn1 --depth 1 --comment "wc=0,in=1" {download-get}
	. (svn) svn update --accept l
	<<< RESULTS >>>
	. (svn) svn update --accept l
	Updating '.':
	U    file.txt
	Updated to revision 3.
	
	$ onsub --disable git --disable hg check                                               
	svn2 (svn) svncheck
	svn1 (svn) svncheck
	<<< RESULTS >>>
	svn2 (svn) svncheck
	[no local mods, no repository changes]
	svn1 (svn) svncheck
	[no local mods, no repository changes]
Now, all `Subversion` working copies are up to date.
## Notes
The code is completely undocumented right now but it's pretty short and leverages a bunch of Python magic to provide a ton of flexibility. It can be compiled into executables as well but we can provide those later if this approach gains traction.
