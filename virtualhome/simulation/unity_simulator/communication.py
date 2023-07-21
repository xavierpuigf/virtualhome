import os
import atexit
from sys import platform
import subprocess
import socket
import glob

class UnityLauncher(object):
    def __init__(self, port='8080', file_name=None, batch_mode=True, x_display=None, no_graphics=False, logging=False, docker_enabled=False):
        self.proc = None
        atexit.register(self.close)
        self.port_number = int(port)
        self.batchmode = batch_mode

        self.launch_executable(file_name, x_display=x_display, no_graphics=no_graphics, logging=logging, docker_enabled=docker_enabled)

    @staticmethod
    def returncode_to_signal_name(returncode: int):
        """
        Try to convert return codes into their corresponding signal name.
        E.g. returncode_to_signal_name(-2) -> "SIGINT"
        """
        try:
            # A negative value -N indicates that the child was terminated by signal N (POSIX only).
            s = signal.Signals(-returncode)  # pylint: disable=no-member
            return s.name
        except Exception:
            # Should generally be a ValueError, but catch everything just in case.
            return None


    def close(self):
        # if self.proc is not None:
        #     self.proc.kill()
        #     self.proc = None
        # return
        print('CLOSING PROC')

        if self.proc is not None:
            # Wait a bit for the process to shutdown, but kill it if it takes too long
            self.proc.kill()
            try:
                timeout_wait = 3
                self.proc.wait(timeout=timeout_wait)
                signal_name = self.returncode_to_signal_name(self.proc.returncode)
                signal_name = f" ({signal_name})" if signal_name else ""
                return_info = f"Environment shut down with return code {self.proc.returncode}{signal_name}."

                # logger.info(return_info)
            except subprocess.TimeoutExpired:
                # logger.info("Environment timed out shutting down. Killing...")
                pass
            # Set to None so we don't try to close multiple times.
            self.proc = None

    def check_x_display(self, x_display):
        with open(os.devnull, "w") as dn:
            # copying the environment so that we pickup
            # XAUTHORITY values
            env = os.environ.copy()
            env['DISPLAY'] = x_display

            if subprocess.call(['which', 'xdpyinfo'], stdout=dn) == 0:
                assert subprocess.call("xdpyinfo", stdout=dn, env=env, shell=True) == 0, \
                    ("Invalid DISPLAY %s - cannot find X server with xdpyinfo" % x_display)

    def check_port(self, port_number):
        """
        Attempts to bind to the requested communicator port, checking if it is already in use.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if platform == "linux" or platform == "linux2":
            # On linux, the port remains unusable for TIME_WAIT=60 seconds after closing
            # SO_REUSEADDR frees the port right after closing the environment
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("localhost", port_number))
        except OSError:
            raise Exception(
                "Couldn't launch the environment. "
                "The port {0} is already being used.".format(
                    port_number
                )
            )
        finally:
            s.close()

    def launch_executable(self, file_name, x_display=None, no_graphics=False, docker_enabled=False, logging=False, args=[]):
        if docker_enabled:
            return
        # based on https://github.com/Unity-Technologies/ml-agents/blob/bf12f063043e5faf4b1df567b978bb18dcb3e716/ml-agents/mlagents/trainers/learn.py
        # https://github.com/allenai/ai2thor/blob/master/ai2thor/controller.py
        cwd = os.getcwd()
        file_name = (
            file_name.strip()
                .replace(".app", "")
                .replace(".exe", "")
                .replace(".x86_64", "")
                .replace(".x86", "")
        )
        env = {}
        true_filename = os.path.basename(os.path.normpath(file_name))
        #logger.debug("The true file name is {}".format(true_filename))
        launch_string = None
        if platform == "linux" or platform == "linux2" and not docker_enabled:
            if x_display:
                env['DISPLAY'] = ':' + x_display
                self.check_x_display(env['DISPLAY'])
            elif 'DISPLAY' not in env:
                env['DISPLAY'] = ''


            self.check_port(self.port_number)

            candidates = glob.glob(os.path.join(cwd, file_name) + ".x86_64")
            if len(candidates) == 0:
                candidates = glob.glob(os.path.join(cwd, file_name) + ".x86")
            if len(candidates) == 0:
                candidates = glob.glob(file_name + ".x86_64")
            if len(candidates) == 0:
                candidates = glob.glob(file_name + ".x86")
            if len(candidates) > 0:
                launch_string = candidates[0]


        elif platform == "darwin":
            candidates = glob.glob(
                os.path.join(
                    cwd, file_name + ".app", "Contents", "MacOS", true_filename
                )
            )
            if len(candidates) == 0:
                candidates = glob.glob(
                    os.path.join(file_name + ".app", "Contents", "MacOS", true_filename)
                )
            if len(candidates) == 0:
                candidates = glob.glob(
                    os.path.join(cwd, file_name + ".app", "Contents", "MacOS", "*")
                )
            if len(candidates) == 0:
                candidates = glob.glob(
                    os.path.join(file_name + ".app", "Contents", "MacOS", "*")
                )
            if len(candidates) > 0:
                launch_string = candidates[0]
                
                
        elif platform == "windows" or platform == 'win32':
            candidates = glob.glob(os.path.join(cwd, file_name)  + ".exe")
            
            if len(candidates) > 0:
                launch_string = candidates[0]

        if launch_string is None:
            self.close()
            raise Exception(
                "Couldn't launch the {0} environment. "
                "Provided filename does not match any environments.".format(
                    true_filename
                )
            )
        else:
            docker_training = False
            if not docker_training:
                subprocess_args = [launch_string]
                if self.batchmode:
                    subprocess_args += ["-batchmode"]
                if no_graphics:
                    subprocess_args += ["-nographics"]

                file_path = os.getcwd()
                subprocess_args += ["-http-port=" + str(self.port_number), "-logFile {}/Player_{}.log".format(file_path, str(self.port_number))]
                subprocess_args += args

                if logging:
                    f = open('{}/port_{}.txt'.format(file_path, self.port_number), 'w+')
                else:
                    f = subprocess.DEVNULL
                try:
                    self.proc = subprocess.Popen(
                        subprocess_args,
                        env=env,
                        stdout=f,
                        start_new_session=True)
                    atexit.register(lambda: self.close)
                    #ret_val = self.proc.poll()
                except:
                    raise Exception('Error, environment was found but could not be launched')

                print(subprocess_args)
                # import pdb
                # pdb.set_trace()
            else:
                docker_ls = (
                    f"exec xvfb-run --auto-servernum --server-args='-screen 0 640x480x24'"
                    f" {launch_string} -http-port {self.port_number}"
                )
                self.proc = subprocess.Popen(
                    docker_ls,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                )
                raise Exception("Docker training is still not implemented")

        pass
