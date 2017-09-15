
# SEND TiD
				self.bci.id_msg_bus.SetEvent(NUMERO AQUI)
				self.bci.iDsock_bus.sendall(self.bci.id_serializer_bus.Serialize());				


# RECIBIR TiD

	# Handle TOBI iD
	def handle_tobiid_input(self):
		data = None
		try:
			data = self.bci.iDsock_bus.recv(512)
			self.bci.idStreamer_bus.Append(data)	
		except:
			self.nS = False
			self.dec = 0
			pass	

		# deserialize ID message
		if data:
			if self.bci.idStreamer_bus.Has("<tobiid","/>"):
				msg = self.bci.idStreamer_bus.Extract("<tobiid","/>")
				self.bci.id_serializer_bus.Deserialize(msg)
				self.bci.idStreamer_bus.Clear()
				tmpmsg = int(self.bci.id_msg_bus.GetEvent())
				print 'Received event! %d' % (tmpmsg)
				
				if (tmpmsg == self.TID_EXIT):
					if (self.connect_eye):
						self.eyetracker.close(self.filename)
					exit()
				elif (tmpmsg > self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER):
					self.update_target_and_state_and_letter(tmpmsg)
					self.update_phase(self.REST_PHASE)

				elif (tmpmsg > self.TID_TARGET_AND_STATE_MULTIPLIER):
					self.update_target_and_state(tmpmsg)
					self.update_phase(self.REST_PHASE)
				elif (tmpmsg > self.TID_LETTER):
					self.update_text(tmpmsg)
				elif (tmpmsg > self.TID_PHASE):
					#ignore for the moment
					self.update_phase(tmpmsg - self.TID_PHASE)
				elif (tmpmsg > self.TID_TARGET):
					self.update_target(tmpmsg - self.TID_TARGET)
				elif (tmpmsg > self.TID_STATE):
					self.update_state(tmpmsg - self.TID_STATE)
				elif (tmpmsg > self.TID_ACTION):
					self.first_move = 1;
					self.execute_action(tmpmsg - self.TID_ACTION)

					
			elif self.bci.idStreamer_bus.Has("<tcstatus","/>"):
				MsgNum = self.bci.idStreamer_bus.Count("<tcstatus")
				for i in range(1,MsgNum-1):
					# Extract most of these messages and trash them		
					msg_useless = self.bci.idStreamer_bus.Extract("<tcstatus","/>")       
