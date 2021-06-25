import logging
from gdbserver import GDBServer
from gdbstub import GDBStub, GDBPacket, GDBCmd, GDBSignal, PACKET_SIZE
import re

log = logging.getLogger('server')

logging.basicConfig(level=logging.DEBUG)


class LibVMIStub(GDBStub):

    def __init__(self, conn, addr, vm_name, process):
        super().__init__(conn, addr)
        self.vm_name = vm_name
        self.process = process
        self.cmd_to_handler = {
            GDBCmd.GEN_QUERY_GET: self.gen_query_get,
            GDBCmd.GEN_QUERY_SET: self.dummy,
            GDBCmd.SET_THREAD_ID: self.dummy,
            GDBCmd.TARGET_STATUS: self.dummy,
            GDBCmd.ENABLE_EXTENDED_MODE: self.dummy,
            GDBCmd.READ_REGISTERS: self.dummy,
            GDBCmd.WRITE_REGISTERS: self.dummy,
            GDBCmd.DETACH: self.dummy,
            GDBCmd.READ_MEMORY: self.dummy,
            GDBCmd.WRITE_MEMORY: self.dummy,
            GDBCmd.WRITE_DATA_MEMORY: self.dummy,
            GDBCmd.CONTINUE: self.dummy,
            GDBCmd.SINGLESTEP: self.dummy,
            GDBCmd.BACKWARD_CONTINUE: self.dummy,
            GDBCmd.BACKWARD_SINGLESTEP: self.dummy,
            GDBCmd.IS_THREAD_ALIVE: self.dummy,
            GDBCmd.REMOVE_XPOINT: self.dummy,
            GDBCmd.INSERT_XPOINT: self.dummy,
            GDBCmd.BREAKIN: self.dummy,
            GDBCmd.V_FEATURES: self.dummy,
            GDBCmd.KILL_REQUEST: self.dummy
        }
        self.features = {
            b'multiprocess': False,
            b'swbreak': False,
            b'hwbreak': False,
            b'qRelocInsn': False,
            b'fork-events': False,
            b'vfork-events': False,
            b'exec-events': False,
            b'vContSupported': False,
            b'QThreadEvents': False,
            b'QStartNoAckMode': False,
            b'no-resumed': False,
            b'xmlRegisters': False,
            b'qXfer:memory-map:read': False
        }

        self.attached = True

    def dummy(self, packet_data):
        log.debug("asdf")
        return False

    def target_status(self, packet_data):
        msg = b'S%.2x' % GDBSignal.TRAP.value
        self.send_packet(GDBPacket(msg))
        return True

    def gen_query_get(self, packet_data):
        if re.match(b'Supported', packet_data):
            reply = self.set_supported_features(packet_data)
            pkt = GDBPacket(reply)
            self.send_packet(pkt)
            return True
        if re.match(b'TStatus', packet_data):
            # Ask the stub if there is a trace experiment running right now
            # reply: No trace has been run yet
            self.send_packet(GDBPacket(b'T0;tnotrun:0'))
            return True
        if re.match(b'TfV', packet_data):
            # TODO
            return False
        if re.match(b'fThreadInfo', packet_data):
            reply = b'm'
            fake_threads = [1337, 31337]
            for thread in fake_threads:
                if reply != b'm':
                    reply += b','
                reply += b'%x' % thread
            self.send_packet(GDBPacket(reply))
            return True
        if re.match(b'sThreadInfo', packet_data):
            # send end of thread list
            self.send_packet(GDBPacket(b'l'))
            return True
        m = re.match(b'ThreadExtraInfo,(?P<thread_id>.+)', packet_data)
        if m:
            tid = int(m.group('thread_id'), 16)
            # thread = self.ctx.get_thread(tid)
            thread = None # dummy
            if not thread:
                return False
            self.send_packet(GDBPacket(thread.name.encode()))
            return True
        if re.match(b'Attached', packet_data):
            # attach existing process: 0
            # attach new process: 1
            self.send_packet(GDBPacket(b'0'))
            return True
        if re.match(b'C', packet_data):
            # return current thread id
            current_tid = 1337
            self.send_packet(GDBPacket(b'QC%x' % current_tid))
            return True
        m = re.match(b'Xfer:memory-map:read::(?P<offset>.*),(?P<length>.*)', packet_data)
        if m:
            offset = int(m.group('offset'), 16)
            length = int(m.group('length'), 16)
            xml = self.get_memory_map_xml()
            chunk = xml[offset:offset+length]
            msg = b'm%s' % chunk
            if len(chunk) < length or offset+length >= len(xml):
                # last chunk
                msg = b'l%s' % chunk
            self.send_packet(GDBPacket(msg))
            return True
        return False

    def set_supported_features(self, packet_data):
        # split string and get features in a list
        # trash 'Supported
        req_features = re.split(b'[:|;]', packet_data)[1:]
        for f in req_features:
            if f[-1:] in [b'+', b'-']:
                name = f[:-1]
                value = True if f[-1:] == b'+' else False
            else:
                groups = f.split(b'=')
                name = groups[0]
                value = groups[1]
            # TODO check supported features
        reply_msg = b'PacketSize=%x' % PACKET_SIZE
        for name, value in self.features.items():
            if isinstance(value, bool):
                reply_msg += b';%s%s' % (name, b'+' if value else b'-')
            else:
                reply_msg += b';%s=%s' % (name, value)
        return reply_msg


log.debug("hey")

with GDBServer("127.0.0.1", 44444, stub_cls=LibVMIStub, stub_args=("1337", 1337)) as server:
    server.listen()
