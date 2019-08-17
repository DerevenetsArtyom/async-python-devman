import subprocess


# ## Start a process in Python:
def first():
    # You can start a process in Python using the Popen function call.
    # The program below starts the unix program ‘cat’ and the second parameter
    # is the argument. This is equivalent to ‘cat test.py’.
    # You can start any program with any parameter.

    from subprocess import Popen, PIPE

    process = Popen(["cat", "README.md"], stdout=PIPE, stderr=PIPE)

    # The process.communicate() call reads input and output from the process.
    # stdout is the process output.
    # stderr will be written only if an error occurs.
    # If you want to wait for the program to finish you can call Popen.wait().
    stdout, stderr = process.communicate()
    print(stdout)


# ## Subprocess call():
def second():
    # Subprocess has a method call() which can be used to start a program.
    # The parameter is list of which the first argument must be the program name
    # The full definition is:
    # subprocess.call(args, *, stdin=None, stdout=None, stderr=None, shell=False
    # Run the command described by args.
    # Wait for command to complete, then return the returncode attribute.

    # In the example below the full command would be “ls -l”
    subprocess.call(["ls", "-l"])


# ## Save process output (stdout)
def third():
    # We can get the output of a program and store it in a string directly
    # using check_output. The method is defined as:
    # subprocess.check_output(args, *, stdin=None, stderr=None,
    #                         shell=False, universal_newlines=False)
    # Run command with arguments and return its output as a byte string.

    s = subprocess.check_output(["echo", "Hello World!"])
    print("s = " + s.decode("utf-8"))


first()
second()
third()
