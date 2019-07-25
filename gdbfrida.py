import logging
from gdbserver import GDBServer
from gdbstub import GDBStub, GDBPacket, GDBCmd, GDBSignal, PACKET_SIZE

log = logging.getLogger('server')

logging.basicConfig(level=logging.DEBUG)


class LibVMIStub(GDBStub):

    def __init__(self, conn, addr, vm_name, process):
        super().__init__(conn, addr)
        self.vm_name = vm_name
        self.process = process
        self.cmd_to_handler = {
            GDBCmd.GEN_QUERY_GET: self.dummy,
            GDBCmd.GEN_QUERY_SET: self.dummy,
            GDBCmd.SET_THREAD_ID: self.dummy,
            GDBCmd.TARGET_STATUS: self.dummy,
            GDBCmd.READ_REGISTERS: self.dummy,
            GDBCmd.WRITE_REGISTERS: self.dummy,
            GDBCmd.DETACH: self.dummy,
            GDBCmd.READ_MEMORY: self.dummy,
            GDBCmd.WRITE_MEMORY: self.dummy,
            GDBCmd.WRITE_DATA_MEMORY: self.dummy,
            GDBCmd.CONTINUE: self.dummy,
            GDBCmd.SINGLESTEP: self.dummy,
            GDBCmd.IS_THREAD_ALIVE: self.dummy,
            GDBCmd.REMOVE_XPOINT: self.dummy,
            GDBCmd.INSERT_XPOINT: self.dummy,
            GDBCmd.BREAKIN: self.dummy,
            GDBCmd.V_FEATURES: self.dummy,
            GDBCmd.KILL_REQUEST: self.dummy
        }
        self.features = {
            b'multiprocess': False,
            b'swbreak': True,
            b'hwbreak': False,
            b'qRelocInsn': False,
            b'fork-events': False,
            b'vfork-events': False,
            b'exec-events': False,
            b'vContSupported': True,
            b'QThreadEvents': False,
            b'QStartNoAckMode': True,
            b'no-resumed': False,
            b'xmlRegisters': False,
            b'qXfer:memory-map:read': True
        }

        self.attached = True

    def dummy(self, packet_data):
        log.debug("asdf")
        return False

    def target_status(self, packet_data):
        msg = b'S%.2x' % GDBSignal.TRAP.value
        self.send_packet(GDBPacket(msg))
        return True


log.debug("hey")

with GDBServer("127.0.0.1", 44444, stub_cls=LibVMIStub, stub_args=("1337", 1337)) as server:
    server.listen()
