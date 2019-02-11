"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics


# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter (basics.DVRouterBase):
	#NO_LOG = True # Set to True on an instance to disable its logging
	POISON_MODE = True # Can override POISON_MODE here
	#DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing
	#table = {}
	#ports = {}

	def __init__ (self):
		"""
		Called when the instance is initialized.

		You probably want to do some additional initialization here.
		"""
		self.start_timer() # Starts calling handle_timer() at correct rate
		self.table = {}
		self.ports = {}
		self.hosts = {}

	def handle_link_up (self, port, latency):
		"""
		Called by the framework when a link attached to this Entity goes up.

		The port attached to the link and the link latency are passed in.
		"""
		self.ports[port] = latency
		for host in self.table.keys():
			new_packet = basics.RoutePacket (host, latency)
			self.send (new_packet, None, flood=True)		

	def handle_link_down (self, port):
		"""
		Called by the framework when a link attached to this Entity does down.

		The port number used by the link is passed in.
		"""
		#print (self.table)
		#print ('down', self, port)
		for host in self.hosts.keys():
			if self.hosts[host][1] == port:
				del self.hosts[host]

		for host in self.table.keys():
			l, p, t = self.table[host]
			if p == port:
				if self.POISON_MODE:
					if host in self.hosts:
						self.table[host] = self.hosts[host]
					else: self.table[host] = 17, p, t
					new_packet = basics.RoutePacket (host, self.table[host][0])
					self.send (new_packet, self.table[host][1], flood=True)
				else: del self.table[host]	   
		#print (self.table)

	def handle_rx (self, packet, port):
		"""
		Called by the framework when this Entity receives a packet.

		packet is a Packet (or subclass).
		port is the port number it arrived on.

		You definitely want to fill this in.
		"""
		#self.log("RX %s on %s (%s)", packet, port, api.current_time())
		
		if isinstance(packet, basics.RoutePacket):
			#print ('route', packet.src, self, packet.destination, packet.latency, port)
			
			host_n = packet.destination
		
			new_latency = packet.latency + self.ports[port]
			if host_n not in self.table or new_latency < self.table[host_n][0]:
				self.table[host_n] = new_latency, port, api.current_time()

			if host_n in self.hosts and self.hosts[host_n][0] < self.table[host_n][0]:
				self.table[host_n] = self.hosts[host_n]
		

			#print (self, self.table[host_n])

			new_packet = basics.RoutePacket (host_n, self.table[host_n][0])
			
			self.send (new_packet, self.table[host_n][1], flood=True)
			
		elif isinstance(packet, basics.HostDiscoveryPacket):
			#print ('discovery', self, packet.src, packet.dst, self, port)
			self.table[packet.src] = (self.ports[port], port, 0)
			self.hosts[packet.src] = (self.ports[port], port, 0)
			#print (self, self.table)
		else:
			#print ('rest', self, packet.src, packet.dst, port)
			#print (self, self.table)
			if packet.src == packet.dst: return
			if not packet.dst in self.table or self.table[packet.dst][0] >= 16:
				return
			self.send (packet, self.table[packet.dst][1])
		

	def handle_timer (self):
		"""
		Called periodically.

		When called, your router should send tables to neighbors.  It also might
		not be a bad place to check for whether any entries have expired.
		"""
		#print ('halp', self, self.table)
		for host in self.table.keys():
			latency, port, time = self.table[host]
			#print (host, self, latency)
			if not time == 0 and api.current_time() - time > 15:
				if self.POISON_MODE:
					if host in self.hosts:
						self.table[host] = self.hosts[host]
					else:
						self.table[host] = 17, port, -1
						continue
				else:
					del self.table[host]
					continue
			
			new_packet = basics.RoutePacket (host, self.table[host][0])
			self.send (new_packet, self.table[host][1], flood=True)
			

