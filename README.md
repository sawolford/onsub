# onsub.py
[onsub.py v0.9](https://bitbucket.org/sawolford/onsub.git)
## Summary
The onsub.py command iterates over subfolders to execute arbitrary commands as dictated by command line arguments and a Python configuration file. The main code consists of 2 Python files: an example Python-configuration file that is meant to be user configurable and the onsub.py script that executes commands as dictated by command line arguments and the configuration file.
## Configuration
The default configuration file is located at `${HOME}/.onsub.py`. A partially functional [example configuration file](https://bitbucket.org/sawolford/onsub/src/master/example.onsub.py) provides sample commands for [Git](https://git-scm.com/), [Mercurial](https://www.mercurial-scm.org/) and [Subversion](https://subversion.apache.org/). It also contains a section (named "every") that will allow operations on all subfolders regardless of type.

All provided files, with a short descrption, are:

	- onsub.py            -- the main execution code (~300 lines)
	- onsub               -- very short python script that calls onsub.py
	- pushd.py            -- implements shell-like pushd capability (borrowed)
	- example.onsub.py    -- config file that implements hg, git, svn behavior
	- guestrepo2onsub.py  -- converter from guestrepo to onsub syntax
	- README.md           -- this file

### Details
#### Pseudo-section `colors`
Colors to use in colorized output. Commented lines indicate default values for each type of output.

	colors = {
	#     "path": "blue",
	#     "command": "cyan",
	#     "good": "green",
	#     "bad": "magenta",
	#     "error": "red",
	#     "partition": "yellow",
	}
#### Pseudo-section `default`
The example `default` section provides some sample Linux commands and a sample Python operation function.
##### `default` summary
	fileCheck   -- Python helper function that checks if a file exists in a folder
	defdefault  -- Pseudo-section for all OSs
	deflinux    -- Pseudo-section for Linux
	defwindows  -- Pseudo-section for Windows
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

	py:fileCheck  -- 
	echo          -- 
	lswcl         -- 
	cwd           -- 
##### `default` details
	def fileCheck(verbose, debug, path, *args):
    	if len(args) != 1: return 1, "fileCheck: wrong number of arguments"
    	fname = args[0]
    	if verbose >= 4: print("os.path.exists({fname})".format(fname=fname))
    	exists = os.path.exists(fname)
    	fpath = "{path}/{fname}".format(path=path, fname=fname)
    	if exists: return 0, "{fpath} exists".format(fpath=fpath)
    	return 1, "{fpath} does not exist".format(fpath=fpath)
	
	defdefault = {
		"py:fileCheck": fileCheck,
	}
	
	deflinux = {
		"echo": "/bin/echo",
    	"lswcl": "ls | wc -l",
	}
	if os.name != "nt": deflinux["cwd"] = f'{sp.check_output("pwd").strip().decode()}'
	
	defwindows = {}
	
	default = {}
	default.update(defdefault)
	if os.name =="nt": default.update(defwindows)
	else: default.update(deflinux)
#### Section `git`
The example `git` section provides sample `git` commands.
##### `git` summary
	gitmakecommand  -- Python helper function that makes a git clone
	gitdefault      -- Pseudo-section for all OSs
	gitlinux        -- Pseudo-section for all Linux
	gitwindows      -- Pseudo-section for all Windows
	git             -- Configuration section for git
##### `git` Linux
Composite:

	git = {
        py:fileCheck = <function fileCheck at 0x106c3a710>
        echo = /bin/echo
        lswcl = ls | wc -l
        cwd = <current working directory>
        py:include = <function <lambda> at 0x106c3a830>
        py:makecommand = <function gitmakecommand at 0x106c3a7a0>
        cmd = git
        get = {cmd} pull
        remotes = {cmd} remote -v
        allremotes = {remotes}
        py:enable = True
	}
Explanation:

	py:fileCheck    -- Inherited from default pseudo-section
	echo            -- Inherited from default pseudo-section
	lswcl           -- Inherited from default pseudo-section
	cwd             -- Inherited from default pseudo-section
	py:include      -- Python function that establishes a folder applies to this section
	py:makecommand  -- Python function that returns a shell command for cloning git folder
	cmd             -- String that tells how to execute git
	get             -- Command alias
	remotes         -- Command alias
	allremotes      -- Command alias
	py:enable       -- Python flag indicating that this section is enabled by default
##### `git` details
	def gitmakecommand(verbose, debug, path, *rest):
		assert len(rest) >= 1
	    url = rest[0]
	    cmd = "git clone {url} {path}".format(path=path, url=url)
	    if debug: print(cmd)
	    return cmd

	gitdefault = {
	    "py:include": lambda verbose, debug, path: os.path.exists(".git"),
	    "py:makecommand": gitmakecommand,
	    "cmd": "git",
	    "get": "{cmd} pull",
	    "remotes": "{cmd} remote -v",
	    "allremotes": "{remotes}",
	}
	
	gitlinux = {}
	gitwindows = {}
	
	git = {}
	git.update(default)
	git.update(gitdefault)
	if os.name == "nt": git.update(gitwindows)
	else: git.update(gitlinux)
	git["py:enable"] = True
#### Section `hg`
The example `hg` section provides sample `hg` commands.
##### `hg` summary
	hgmakecommand  -- Python helper function that makes an hg clone
	hgdefault      -- Pseudo-section for all OSs
	hglinux        -- Pseudo-section for all Linux
	hgwindows      -- Pseudo-section for all Windows
	hg             -- Configuration section for hg
##### `hg` Linux
Composite:

	hg = {
		py:fileCheck = <function fileCheck at 0x1055dc710>
		echo = /bin/echo
		lswcl = ls | wc -l
		cwd = <current working directory>
		py:include = <function <lambda> at 0x1055dc950>
		py:makecommand = <function hgmakecommand at 0x1055dc8c0>
		cmd = hg
		get = {cmd} pull --update
		remotes = {echo} -n "default = "; {cmd} paths default
		allremotes = {remotes}; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull
		py:enable = True
	}
Explanation:

		py:fileCheck    -- Inherited from default pseudo-section
		echo            -- Inherited from default pseudo-section
		lswcl           -- Inherited from default pseudo-section
		cwd             -- Inherited from default pseudo-section
		py:include      -- Python function that establishes a folder applies to this section
		py:makecommand  -- Python function that returns a shell command for cloning hg folder
		cmd             -- String that tells how to execute hg
		get             -- Command alias
		remotes         -- Command alias
		allremotes      -- Command alias
		py:enable       -- Python flag indicating that this section is enabled by default
##### `hg` details
	def hgmakecommand(verbose, debug, path, *rest):
		assert len(rest) >= 1
		rrev = ""
		if len(rest) >= 2: rrev = "-r {rev}".format(rev=rest[1])
		url = rest[0]
		cmd = "hg clone {url} {path} {rrev}".format(path=path, url=url, rrev=rrev)
		if debug: print(cmd)
		return cmd

	hgdefault =  {
		"py:include": lambda verbose, debug, path: os.path.exists(".hg"),
		"py:makecommand": hgmakecommand,
		"cmd": "hg",
		"get": "{cmd} pull --update",
	}
	
	hglinux = {
		"remotes": '{echo} -n "default = "; {cmd} paths default',
		"allremotes": '{remotes}; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull',
	}
	
	hgwindows = {
		"remotes": '{cmd} paths default',
		"allremotes": '{remotes}; {cmd} paths default-push; {cmd} paths default-pull',
	}
	
	hg = {}
	hg.update(default)
	hg.update(hgdefault)
	if os.name == "nt": hg.update(hgwindows)
	else: hg.update(hglinux)
	hg["py:enable"] = True
#### Section `svn`
The example `svn` section provides some sample Linux commands and a sample Python operation function.
##### `svn` summary
	svnmakecommand  -- Python helper function that makes an svn checkout
	svndefault      -- Pseudo-section for all OSs
	svnlinux        -- Pseudo-section for all Linux
	svnwindows      -- Pseudo-section for all Windows
	svn             -- Configuration section for svn
##### `svn` Linux
Composite:

	svn = {
		py:fileCheck = <function fileCheck at 0x10e7a0710>
		echo = /bin/echo
		lswcl = ls | wc -l
		cwd = <current working directory>
		py:include = <function <lambda> at 0x10e7a0a70>
		py:makecommand = <function svnmakecommand at 0x10e7a09e0>
		cmd = svn
		get = {cmd} up
		remotes = {cmd} info --show-item url
		allremotes = {remotes}
		py:enable = True
	}
Explanation:

		py:fileCheck    -- Inherited from default pseudo-section
		echo            -- Inherited from default pseudo-section
		lswcl           -- Inherited from default pseudo-section
		cwd             -- Inherited from default pseudo-section
		py:include      -- Python function that establishes a folder applies to this section
		py:makecommand  -- Python function that returns a shell command for checking out svn folder
		cmd             -- String that tells how to execute svn
		get             -- Command alias
		remotes         -- Command alias
		allremotes      -- Command alias
		py:enable       -- Python flag indicating that this section is enabled by default
##### `svn` details
	def svnmakecommand(verbose, debug, path, *rest):
		assert len(rest) >= 1
		rev = "head"
		if len(rest) >= 2: rev = rest[1]
		url = rest[0]
		cmd = "svn checkout {url}@{rev} {path}".format(path=path, url=url, rev=rev)
		if debug: print(cmd)
		return cmd
	
	svndefault = {
		"py:include": lambda verbose, debug, path: os.path.exists(".svn"),
		"py:makecommand": svnmakecommand,
		"cmd": "svn",
		"get": "{cmd} up",
		"remotes": "{cmd} info --show-item url",
		"allremotes": "{remotes}",
	}
	
	svnlinux = {}
	svnwindows = {}
	
	svn = {}
	svn.update(default)
	svn.update(svndefault)
	if os.name == "nt": svn.update(svnwindows)
	else: svn.update(svnlinux)
	svn["py:enable"] = True
#### Section `every`
The example `every ` section provides some sample Linux commands and a sample Python operation function.
##### `every ` summary
	everymakefunction  -- Python helper function that makes a folder
	everydefault      -- Pseudo-section for all OSs
	everylinux        -- Pseudo-section for all Linux
	everywindows      -- Pseudo-section for all Windows
	every             -- Configuration section for all folders
##### `every ` Linux
Composite:

	every = {
		py:fileCheck = <function fileCheck at 0x110831710>
		echo = /bin/echo
		lswcl = ls | wc -l
		cwd = <current working directory>
		py:include = <function <lambda> at 0x110831b90>
		py:makefunction = <function everymakefunction at 0x110831b00>
	}
Explanation:

	py:fileCheck     -- Inherited from default pseudo-section
	echo             -- Inherited from default pseudo-section
	lswcl            -- Inherited from default pseudo-section
	cwd              -- Inherited from default pseudo-section
	py:include       -- Python function that establishes a folder applies to this section
	py:makefunction  -- Python function that makes a folder
##### `every ` details
	def everymakefunction(verbose, debug, path, *rest):
		if verbose >=4: print("os.makedirs({path})".format(path=path))
		os.makedirs(path)
		return 0, "os.makedirs({path})".format(path=path)
	
	everydefault = {
		"py:include": lambda verbose, debug, path: True,
		"py:makefunction": everymakefunction,
	}
	
	everylinux = {}
	everywindows = {}
	
	every = {}
	every.update(default)
	every.update(everydefault)
	if os.name == "nt": every.update(everywindows)
	else: every.update(everylinux)
## Command line options
The basic command line options, with variable outputs specified by <>, are:

	usage: onsub [-h] [--command] [--config CONFIG] [--configfile CONFIGFILE] [--count COUNT] [--debug] [--depth DEPTH]
                 [--disable DISABLE] [--dump DUMP] [--dumpall] [--enable ENABLE] [--file FILE] [--noenable] [--noop]
                 [--py:include PYINCLUDE] [--py:makecommand PYMAKECOMMAND] [--py:makefunction PYMAKEFUNCTION]
                 [--py:enable PYENABLE] [--suppress] [--verbose VERBOSE] [--workers WORKERS]
                 ...
   
	Walks filesystem executing arbitrary commands
	
	positional arguments:
  		rest
	
	optional arguments:
  	  -h, --help                        show this help message and exit
  	  --command                         prefix {cmd} (default: False)
  	  --config CONFIG                   config option (default: None)
  	  --configfile CONFIGFILE           config file (default: <home folder>/.onsub.py)
  	  --count COUNT                     count for substitutions (default: 10)
  	  --debug                           debug flag (default: False)
  	  --depth DEPTH                     walk depth (default: -1)
  	  --disable DISABLE                 disabled sections (default: None)
  	  --dump DUMP                       dump section (default: None)
  	  --dumpall                         dump all sections (default: False)
	  --enable ENABLE                   enabled sections (default: None)
  	  --file FILE                       file with folder names (default: None)
  	  --nocolor                         disables colorized output (default: False)
  	  --noenable                        no longer enable any sections (default: False)
  	  --noop                            no command execution (default: False)
  	  --py:include PYINCLUDE            key for py:include (default: py:include)
  	  --py:makecommand PYMAKECOMMAND    key for py:makecommand (default: py:makecommand)
  	  --py:makefunction PYMAKEFUNCTION  key for py:makefunction (default: py:makefunction)
  	  --py:disable PYDISABLE            key for py:disable (default: py:disable)
  	  --suppress                        suppress repeated error output (default: False)
  	  --verbose VERBOSE                 verbose level (default: 4)
  	  --workers WORKERS                 number of workers (default: <number of cores>)
### -h, --help
	-h, --help                        show this help message and exit
Type: Flag<br>
Default: \<none><br>
Option: \<none><br>
Repeat: No<br><br>
Outputs command line options (see above).
### --command
	--command                         prefix {cmd} (default: False)
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repate: No<br><br>
Causes command substituion to be prefixed with `{cmd} `.
### --config CONFIG
	--config CONFIG                   config option (default: None)
Type: Option<br>
Default: None<br>
Option: `CONFIG`<br>
Repeate: Yes<br><br>
Appends `CONFIG` lines to configuration, one at a time. Can be used to alter configuration for a single command execution.
### --configfile CONFIGFILE
	--configfile CONFIGFILE           config file (default: <home folder>/.onsub.py)
Type: Option<br>
Default: \<home folder>/.onsub.py<br>
Option: `CONFIGFILE`<br>
Repeat: No<br><br>
Names `CONFIGFILE` to be the configuration file to be loaded.
### --count COUNT
	--count COUNT                     count for substitutions (default: 10)
Type: Option<br>
Default: 10<br>
Option: `COUNT`<br>
Repeat: No<br><br>
Indicates that `COUNT` is the maximum number of times to recursively substitute configuration entries to prevent infinite recursion.
### --debug
	--debug                           debug flag (default: False)
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeate: No<br><br>
Causes `onsub` to output more diagnostic information. Is also passed to `py:` functions where they occur in configuration entries.
### --depth DEPTH
	--depth DEPTH                     walk depth (default: -1)
Type: Option<br>
Default: -1<br>
Option: `DEPTH`<br>
Repeat: No<br><br>
If greater than zero, limits the filesystem depth that is walked by `onsub` to folder entries with up to `DEPTH`-many subdirectories.
### --disable DISABLE
	--disable DISABLE                 disabled sections (default: None)
Type: Option<br>
Default: None<br>
Option: `DISABLE`<br>
Repeat: Yes<br><br>
Disables section `DISABLE` that would otherwise be enabled by configuration file or command line option. Takes precedence over all other means of enabling sections.
### --dump DUMP
	--dump DUMP                       dump section (default: None)
Type: Option<br>
Default: None<br>
Option: `DUMP`<br>
Repeat: Yes<br><br>
Outputs configuration section `DUMP`. Can be dump multiple configuration sections. Can be used to remember how command substitutions will be generated.
### --dumpall
	--dumpall                         dump all sections (default: False)
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Dumps all configuration sections.
### --enable ENABLE
	--enable ENABLE                   enabled sections (default: None)
Type: Option<br>
Default: None<br>
Option: `ENABLE`<br>
Repeat: Yes<br><br>
Enables section `ENABLE` that would otherwise be disabled by configuration file or command line option. Takes precedence over default disable and configuration file.
### --file FILE
	--file FILE                       file with folder names (default: None)
Type: Option<br>
Default: None<br>
Option: `FILE`<br>
Repeat: No<br><br>
Reads `FILE` as list of folders to be operated on instead of recursively scanning filesystem. Missing folders will be generated by `py:makecommand` or `py:makefunction` if available and in that order.
### --nocolor
	--nocolor                         disables colorized output (default: False)
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Turns off color in output.
### --noenable
	--noenable                        no longer enable any sections (default: False)
Type: Option<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Defaults all configuration sections to not be enabled. This can be change later for each configuration section with other command line options.
### --noop
	--noop                            no command execution (default: False)
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Indicates that no command should be run in any folder. This can be useful when folders will be generated because of `--file FILE` command line option. Since no command is run, the folder generation can be run in parallel.
### --py:include PYINCLUDE
	--py:include INCLUDE              key for py:include (default: py:include)
Type: Option<br>
Default: py:include<br>
Option: `PYINCLUDE`<br>
Repeat: No<br><br>
Names `PYINCLUDE` as the key to look up in each configuration section for checking to see if a section applies to a folder.
### --py:makecommand PYMAKECOMMAND
	--py:makecommand PYMAKECOMMAND    key for py:makecommand (default: py:makecommand)
Type: Option<br>
Default: py:makecommand<br>
Option: `PYMAKECOMMAND`<br>
Repeat: No<br><br>
Names `PYMAKECOMMAND` as the key to look up in each configuration section for generating commands to make folders.
### --py:makefunction PYMAKEFUNCTION
	--py:makefunction PYMAKEFUNCTION  key for py:makefunction (default: py:makefunction)
Type: Option<br>
Default: py:makefunction<br>
Option: `PYMAKEFUNCTION`<br>
Repeat: No<br><br>
Names `PYMAKEFUNCTION` as the key to look up in each configuration section for executing python commands to make folders.
### --py:enable PYENABLE
	--py:enable PYENABLE            key for py:enable (default: py:enable)
Type: Option<br>
Default: py:enable<br>
Option: `PYENABLE `<br>
Repeat: No<br><br>
Names `PYENABLE ` as the key to look up in each configuration section for determining if the section is enabled by default.
### --suppress
	--suppress                        suppress repeated error output (default: False)
Type: Flag<br>
Default: False<br>
Option: \<none><br>
Repeat: No<br><br>
Indicates that summary information for errors should not be output at end of execution. Output will otherwise be included depending on `--verbose` flag.
### --verbose VERBOSE
	--verbose VERBOSE                 verbose level (default: 4)
Type: Option<br>
Default: 4<br>
Option: `VERBOSE`<br>
Repeat: No<br><br>
Sets the level of output to be included in command execution where higher numbers include output of lower numbers:<br>
0. No output<br>
1. Only errors, subsequent to parallel execution<br>
2. Output of commands, subsequent to parallel execution<br>
3. Output path, applicable section and command, subsequent to parallel execution<br>
4. Output one line for each command, prior to parallel execution<br>
### --workers WORKERS
	--workers WORKERS                 number of workers (default: <number of cores>)
Type: Option<br>
Default: \<number of cores><br>
Option: `WORKERS`<br>
Repeate: No<br><br>
Sets the number of simultaneous worker processes to use.
## Examples
Examples of using onsub are below. The config file is assumed to be [example.onsub.py](https://bitbucket.org/sawolford/onsub/src/master/example.onsub.py) and it is executed on a Linux workstation. The directory structure is assumed to be the following:

	git/
	git/.git
	git/file.txt # contains string "file.txt"
	hg/
	hg/.hg
	normal/
	svn/
	svn/.svn
Due to the limited quoting ability of the Windows `CMD.EXE` command shell, some of these examples are too sophisticated to run correctly in that environment.
### Dump config (--dump DUMP [--dump DUMP ...])
With no arguments:

	usage: onsub [-h] [--command] [--config CONFIG] [--configfile CONFIGFILE] [--count COUNT] [--debug] [--depth DEPTH]
                 [--disable DISABLE] [--dump DUMP] [--dumpall] [--enable ENABLE] [--file FILE] [--noenable] [--noop]
                 [--py:include PYINCLUDE] [--py:makecommand PYMAKECOMMAND] [--py:makefunction PYMAKEFUNCTION]
                 [--py:enable PYENABLE] [--suppress] [--verbose VERBOSE] [--workers WORKERS]
                 ...
	onsub: error: argument --dump: expected one argument


With `--dump default`:

	$ onsub --dump default
	default = {
        py:fileCheck = <function fileCheck at 0x1070867a0>
        echo = /bin/echo
        lswcl = ls | wc -l
        cwd = <current working directory>
	}

With `--dump hg`:

	$ onsub --dump hg
	hg = {
		py:fileCheck = <function fileCheck at 0x10b476830>
		echo = /bin/echo
		lswcl = ls | wc -l
		cwd = <current working directory>
		py:include = <function <lambda> at 0x10b476950>
		py:makecommand = <function hgmakecommand at 0x10b4768c0>
		cmd = hg
		get = {cmd} pull --update
		remotes = {echo} -n "default = "; {cmd} paths default
		allremotes = {remotes}; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull
		py:enable = True
	}

With `--dump git`:

	$ onsub --dump git
	git = {
		py:fileCheck = <function fileCheck at 0x10fea5830>
		echo = /bin/echo
		lswcl = ls | wc -l
		cwd = <current working directory>
		py:include = <function <lambda> at 0x10fea5a70>
		py:makecommand = <function gitmakecommand at 0x10fea59e0>
		cmd = git
		get = {cmd} pull
		remotes = {cmd} remote -v
		allremotes = {remotes}
		py:enable = True
	}

With `--dump svn`:

	$ onsub --dump svn
	svn = {
		py:fileCheck = <function fileCheck at 0x10ff6f830>
		echo = /bin/echo
		lswcl = ls | wc -l
		cwd = <current working directory>
		py:include = <function <lambda> at 0x10ff6fb90>
		py:makecommand = <function svnmakecommand at 0x10ff6fb00>
		cmd = svn
		get = {cmd} up
		remotes = {cmd} info --show-item url
		allremotes = {remotes}
		py:enable = True
	}

With `--dump every`:

	$ onsub --dump every
	every = {
		py:fileCheck = <function fileCheck at 0x1045e2830>
		echo = /bin/echo
		lswcl = ls | wc -l
		cwd = <current working directory>
		py:include = <function <lambda> at 0x1045e2cb0>
		py:makefunction = <function everymakefunction at 0x1045e2c20>
		py:enable = False
	}
## Notes
The code is completely undocumented right now but it's pretty short and leverages a bunch of Python magic to provide a ton of flexibility. It can be compiled into executables as well but we can provide those later if this approach gains traction.
