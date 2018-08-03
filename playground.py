import script


def run_test(line, *args):
    script.parse_script_line(line)


if __name__ == '__main__':
    run_test('[PUT] <bottle> (1) <table> (1)', 'a', 1)
