import sys
import getopt
import socket
import time

import Checksum
import BasicSender



CHUNK = 1400
WINDOW = 7

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
	def __init__(self, dest, port, filename, debug=False, sackMode=False):
		super(Sender, self).__init__(dest, port, filename, debug)
		self.sackMode = sackMode
		self.debug = debug
		self.dest = dest
		self.port = port
		# self.filename = filename

		# Main sending loop.
	def start(self):
		fd = open (filename, "rb")
		rd = fd.read()
		data = [rd[i:i + CHUNK] for i in xrange(0, len(rd), CHUNK)]
		n = len (data)
		data = dict (zip (xrange (1, n + 1), data))
		seq = 0

		rc, is_valid = self.received ('syn', seq, '')
		while not is_valid:
			rc, is_valid = self.received ('syn', seq, '')

		seq = start = 1
		start_time = time.time()
		repeat_count = 0

		while True:
			if seq > min (n, start + WINDOW): 
				seq = start

			if time.time() - start_time >= 0.5 and start < seq:
				seq = start
				start_time = time.time()
			if not seq in data:
				seq += 1
				continue

			sd_type = 'dat' 
			if seq == n: sd_type = 'fin'
			rc, is_valid = self.received (sd_type, seq, data[seq])

			if is_valid:
				rc_type, seq_rc, data_rc, cs = self.split_packet (rc)
				if rc_type == 'ack':
					seq = int (seq_rc)

				if rc_type == 'sack':
					seq_s, sent = seq_rc.split(';')
					if len (sent) > 0:
						sent = map (int, sent.split (','))
						for i in sent: 
							if i in data: data.pop (i)
					seq = int (seq_s)
				start = seq - 1
				start_time = time.time()
				if start >= n:
					break
			else: seq += 1


	def received (self, msg_type, seq, data):
		msg = self.make_packet (msg_type, seq, data)
		self.send (msg, address=(self.dest, self.port))
		rc = self.receive (0.15)
		return rc, Checksum.validate_checksum (rc)
		
		

'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
	def usage():
		print "BEARS-TP Sender"
		print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
		print "-p PORT | --port=PORT The destination port, defaults to 33122"
		print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
		print "-d | --debug Print debug messages"
		print "-h | --help Print this usage message"
		print "-k | --sack Enable selective acknowledgement mode"

	try:
		opts, args = getopt.getopt(sys.argv[1:],
				"f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
	except:
		usage()
		exit()

	port = 33122
	dest = "localhost"
	filename = None
	debug = False
	sackMode = False

	for o,a in opts:
		if o in ("-f", "--file="):
			filename = a
		elif o in ("-p", "--port="):
			port = int(a)
		elif o in ("-a", "--address="):
			dest = a
		elif o in ("-d", "--debug="):
			debug = True
		elif o in ("-k", "--sack="):
			sackMode = True

	s = Sender(dest, port, filename, debug, sackMode)
	try:
		s.start()
	except (KeyboardInterrupt, SystemExit):
		exit()
