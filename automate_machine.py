#!/usr/bin/env python3

#
# Installing the virtualbox deps:
#   python3 -m pip install pyvbox
#   Download the VirtualBox SDK from https://www.virtualbox.org/wiki/Downloads
#   Unzip the package
#   cd sdk/installer
#   python3 vboxapisetup.py install
#

import virtualbox
import logging


class Sandbox(object):
    def __init__(self, name):
        vbox = virtualbox.VirtualBox()
        self.vm = vbox.find_machine(name)
        #self.session = virtualbox.Session()
        self.session = virtualbox.library.ISession(self.vm.create_session())

        return


    def start(self):
        logging.info('Starting the VM from Office snapshot')
        self.snapshot = self.vm.find_snapshot('Office 2007 Live')
        progress = self.session.machine.restore_snapshot(self.snapshot)
        progress.wait_for_completion()
        self.session.unlock_machine()
        progress = self.vm.launch_vm_process(self.session, '', '')
        progress.wait_for_completion()
        if self.vm.state == self.vm.state.running:
            print('Successfully running')
        print('Done')

        # Create guest session.
        self.console = virtualbox.library.IConsole(self.session.console)
        self.guest = self.console.guest
        # self.guest.sessions[0] contains our IGuestSession object
        self.os_type = self.guest.os_type_id        # Example
        self.g_session = self.guest.create_session('malware', 'password', '', '')

        return


    #
    # Username is 'malware'; password is 'password'
    #
    def guest_session_test(self):
        self.console = virtualbox.library.IConsole(self.session.console)
        self.guest = self.console.guest
        # self.guest.sessions[0] contains our IGuestSession object
        self.os_type = self.guest.os_type_id        # Example
        self.g_session = self.guest.create_session('malware', 'password', '', '')
        # 1 = R
        # 2 = 
        # 3 = RW
        flag = virtualbox.library.FileCopyFlag(0)
        # This stores the file in your user's home directory by default.
        self.g_session.file_copy_from_guest('C:/Program Files (x86)/Microsoft Office/Office12/GRAPH.EXE', 'C:/WINDOWS/Temp/graph.exe', [flag])


    def drop_artifact(self, artifact_path, destination_on_guest):
        logging.info('About to drop "{}" to "{}"'.format(artifact_path, destination_on_guest))
        flag = virtualbox.library.FileCopyFlag(0)
        progress = self.g_session.file_copy_to_guest(artifact_path, destination_on_guest, [flag])
        progress.wait_for_completion()
        logging.info('"{}" successfully dropped to guest'.format(artifact_path))

        return


    def receive_artifact(self, src_on_guest, path_host_save):
        logging.info('About to pull "{}" to "{}"'.format(src_on_guest, path_host_save))
        flag = virtualbox.library.FileCopyFlag(0)
        progress = self.g_session.file_copy_from_guest(src_on_guest, path_host_save, [flag])
        progress.wait_for_completion()
        logging.info('"{}" successfully saved to "{}"'.format(src_on_guest, path_host_save))

        return


    def execute_command(self, 
                        executable_path: str, 
                        arguments: [str],
                        environment_changes: [str],
                        process_create_flag: [virtualbox.library.ProcessCreateFlag],
                        timeout_ms: int,
                        priority: virtualbox.library.ProcessPriority,
                        affinity: [int]):
        terminate_flag = virtualbox.library.ProcessWaitForFlag(2)

        self.guest_process = self.g_session.process_create_ex(  executable_path, 
                                                                arguments, 
                                                                environment_changes,
                                                                process_create_flag,
                                                                timeout_ms,
                                                                priority,
                                                                affinity)
        logging.info('Process "{}" successfully kicked off...waiting for it to finish'.format(executable_path))
        self.process_wait_result = self.guest_process.wait_for(terminate_flag)
        if self.process_wait_result == virtualbox.library.ProcessWaitResult(5):
            logging.info('Process "{}" exceeded the timeout threashold of {} milliseconds'.format(  executable_path,
                                                                                                    str(timeout_ms))) 
        elif self.process_wait_result == virtualbox.library.ProcessWaitResult(2):
            logging.info('Process "{}" terminated gracefully'.format(executable_path))


    def stop(self):
        # Shut off VM
        progress = self.session.console.power_down()
        progress.wait_for_completion()

        return


s = Sandbox('Windows 7 Office')
s.start()
# s.guest_session_test()
s.drop_artifact('C:/WINDOWS/System32/cmd.exe', 'C:/WINDOWS/Temp/cmd_2016.exe')
#s.execute_command(  'C:/WINDOWS/Temp/cmd_2016.exe',
s.execute_command(  'C:/Program Files (x86)/Microsoft Office/Office12/GRAPH.EXE',
                    [],
                    [],
                    [virtualbox.library.ProcessCreateFlag(0)],
                    20000,
                    virtualbox.library.ProcessPriority(1),
                    [])
s.stop()

