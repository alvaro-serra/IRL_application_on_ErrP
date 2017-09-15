# -*- coding: utf-8 -*-

import cnbiloop
import ConfigParser
import sys, time, math, string
from PyQt4 import QtGui, QtCore
from cnbiloop import BCI
from time import *
from cnbiloop import pylpttrigger
from python_client import SerialWriter
# import EyeLink
import datetime
import SerialWriter

class RASER(QtGui.QWidget):
    
	def __init__(self):
		super(RASER, self).__init__()
		self.initUI()
        
	def initUI(self):      
		
		if (len(sys.argv) == 1):
			self.config_file = "protocol_configuration.ini"
		else:
			if (string.find(sys.argv[1], '.ini') == -1):
				self.config_file = str(sys.argv[1]) + ".ini"
			else:
				self.config_file = str(sys.argv[1])


		print "Using configuration file: ", self.config_file

		config = ConfigParser.RawConfigParser(allow_no_value=True)
		config.read("./" + self.config_file)
		
		self.connect_to_loop = 1
		
		if (self.connect_to_loop):
			self.bci = BCI.BciInterface()
			self.bci.id_msg_bus.SetEvent(400)
			self.bci.iDsock_bus.sendall(self.bci.id_serializer_bus.Serialize());	
		
		# Globals
		self.ACTION_UP = config.getint("constants", "ACTION_UP")
		self.ACTION_DOWN = config.getint("constants", "ACTION_DOWN")
		self.ACTION_LEFT = config.getint("constants", "ACTION_LEFT")
		self.ACTION_RIGHT = config.getint("constants", "ACTION_RIGHT")
		self.ACTION_END_EFFECTOR = config.getint("constants", "ACTION_END_EFFECTOR")
		self.ACTION_UP_LEFT = config.getint("constants", "ACTION_UP_LEFT")
		self.ACTION_UP_RIGHT = config.getint("constants", "ACTION_UP_RIGHT")
		self.ACTION_DOWN_LEFT = config.getint("constants", "ACTION_DOWN_LEFT")
		self.ACTION_DOWN_RIGHT = config.getint("constants", "ACTION_DOWN_RIGHT")

		self.TID_ACTION = config.getint("constants", "TID_ACTION")
		self.TID_TARGET = config.getint("constants", "TID_TARGET") 
		self.TID_STATE = config.getint("constants", "TID_STATE") 
		self.TID_PHASE = config.getint("constants", "TID_PHASE")
		self.TID_LETTER = config.getint("constants", "TID_LETTER")
		self.TID_EXIT = config.getint("constants", "TID_EXIT") 		
		self.TID_TARGET_AND_STATE_MULTIPLIER = config.getint("constants", "TID_TARGET_AND_STATE_MULTIPLIER")
		self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER = config.getint("constants", "TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER") 		
		self.REST_PHASE = config.getint("constants", "REST_PHASE") 		
		self.full_screen = config.getint("window", "full_screen")
		self.execution_mode = config.getint("protocol", "execution_mode")
		self.first_move = 0

		self.OFFLINE_RUN = config.getint("constants", "OFFLINE_RUN") 		
		self.OFFLINE_CS_RUN = config.getint("constants", "OFFLINE_CS_RUN") 		
		self.ONLINE_RUN = config.getint("constants", "ONLINE_RUN") 		
		self.ONLINE_FREE_RUN = config.getint("constants", "ONLINE_FREE_RUN") 		
		self.ONLINE_SIMULATED = config.getint("constants", "ONLINE_SIMULATED") 		

		
		self.connect_eye = config.getint("protocol", "use_eye_tracker")

		now = datetime.datetime.now()
		
		self.format = config.get("protocol", "xdf_format")
		self.subject_id = config.get("protocol", "subject_id")
		self.name_experiment = config.get("protocol", "name_experiment")

		self.filename = self.subject_id + '_' + self.name_experiment + '_' + str(now.year) + str(now.month) + str(now.day) + '_' + str(now.hour) + str(now.minute) + str(now.second) + '.' + self.format



		# Parameters
		if (self.full_screen):
			self.screen_width = QtGui.QDesktopWidget().screenGeometry().width()
			self.screen_height = QtGui.QDesktopWidget().screenGeometry().height()
			print "screen ", self.screen_width, ", ", self.screen_height
		else:
			self.screen_width = config.getint("window", "screen_width")
			self.screen_height = config.getint("window", "screen_height")
		
		self.num_tiles_x = config.getint("interface", "num_tiles_column")
		self.num_tiles_y = config.getint("interface", "num_tiles_row")
		self.grid_thickness = config.getint("interface", "grid_thickness")
		self.gap_x = config.getint("interface", "gap_x")
		self.gap_y = config.getint("interface", "gap_y")
		self.tile_width = config.getint("interface", "tile_width")
		self.tile_height = config.getint("interface", "tile_height")
		self.device_diameter = config.getint("interface", "device_diameter")
		
		self.color_grid = QtGui.QColor(float(config.get("colors", "color_grid").split(',')[0]), float(config.get("colors", "color_grid").split(',')[1]), float(config.get("colors", "color_grid").split(',')[2]))
		self.color_text = QtGui.QColor(float(config.get("colors", "color_text").split(',')[0]), float(config.get("colors", "color_text").split(',')[1]), float(config.get("colors", "color_text").split(',')[2]))
		self.color_background = QtGui.QColor(float(config.get("colors", "color_background").split(',')[0]), float(config.get("colors", "color_background").split(',')[1]), float(config.get("colors", "color_background").split(',')[2]))	
		self.color_target = QtGui.QColor(float(config.get("colors", "color_target").split(',')[0]), float(config.get("colors", "color_target").split(',')[1]), float(config.get("colors", "color_target").split(',')[2]))
		self.color_target_ONLINE_FREEMODE = QtGui.QColor(float(config.get("colors", "color_target2").split(',')[0]), float(config.get("colors", "color_target2").split(',')[1]), float(config.get("colors", "color_target2").split(',')[2]))
		self.color_device = QtGui.QColor(float(config.get("colors", "color_device").split(',')[0]), float(config.get("colors", "color_device").split(',')[1]), float(config.get("colors", "color_device").split(',')[2]))

		self.color_end_effector = QtGui.QColor(0, 0, 250)
		
		self.font = QtGui.QFont()
		self.font_size = config.getint("interface", "font_size")
		self.font.setPixelSize(self.font_size)
		self.fm = QtGui.QFontMetrics(self.font)
		self.characters = config.get("interface", "characters")

		self.position_target_y = 2		
		self.position_target_x = 2

		self.position_device_y = 1		
		self.position_device_x = 2
		
		self.tt = time()
		
		self.init_position_x = (self.screen_width - ((self.num_tiles_x*self.tile_width) + ((self.num_tiles_x-1)*self.gap_x)))/2
		self.init_position_y = (self.screen_height - ((self.num_tiles_y*self.tile_height) + ((self.num_tiles_y-1)*self.gap_y)))/2
		self.setGeometry(0,0, self.screen_width, self.screen_height)
		self.setWindowTitle('RASER')
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		self.setFocus()

		# Connect to eye-tracker
		if (self.connect_eye):
			self.eyetracker = EyeLink.tracker(self.screen_width, self.screen_height)
		else:
			print "[RaSER GUI] Eye-tracker not used"

		self.show()
		
		if (self.full_screen):
			self.showFullScreen()
		
		QtCore.QCoreApplication.processEvents()
		QtCore.QCoreApplication.flush()
		timer = QtCore.QTimer(self)
		timer.timeout.connect(self.update_loop)
		timer.start(config.getfloat("interface", "paint_cycle_time"));

		self.tt = time()
		self.end_effector_shrink_factor = config.getfloat("interface", "end_effector_shrink_factor") 
		self.increase_saliency_end_effector = config.getint("interface", "increase_saliency_end_effector") 
		self.action_end_effector = 0
		self.counter_end_effector = 0
		self.action_end_effector_time = round(config.getfloat("interface", "end_effector_action_time") / config.getfloat("interface", "paint_cycle_time"))


		self.paint_underscore = 0
		self.counter_underscore = 0
		self.underscore_blinking_time = round(config.getfloat("interface", "underscore_blinking_time") / config.getfloat("interface", "paint_cycle_time"))
		self.written_text = ""
		self.color = 1

		self.action_executed = 0
		self.draw_photodiode = config.getint("interface", "draw_photodiode")
		
		# Rest phase variables
		self.rest_phase_duration = (float(config.get("protocol", "rest_phase_duration").split(' ')[0])-1) * 1000 / config.getfloat("interface", "paint_cycle_time")
		self.counter_rest_phase = 0
		self.rest_phase_bar_length = 0.6 * self.screen_width
		self.show_rest_phase = 0
		self.color_rect = QtGui.QColor(255,100,0)
		self.color_text = QtGui.QColor(0, 128, 128)
		
		#######################################################################
		# LPT Trigger initialization
		#######################################################################
		# self.use_hwtrigger = config.getint("protocol", "use_hardware_trigger")
		self.lpt_type = config.getint("protocol", "use_hardware_trigger")
		self.use_hwtrigger = self.lpt_type > 0
		
		# Parallel port
		if (self.lpt_type == 1):
			self.lpt = pylpttrigger
			self.lpt.open(0,100,0)
		# Arduino
		elif (self.lpt_type == 2):
			SERIAL_PORT= 'Arduino Micro'
			BAUD_RATE= 115200
			self.lpt = SerialWriter.SerialWriter(SERIAL_PORT, BAUD_RATE)
		else:
			print "Unknown LPT Trigger!! Exiting..."		
			exit()

		self.send_trigger = 0
		self.counter_lpt = 0
		#######################################################################
		
	def update_loop(self):
		self.handle_tobiid_input()
		if (self.action_end_effector):
			self.counter_end_effector += 1
			if (self.counter_end_effector == self.action_end_effector_time):
				self.device_diameter = self.device_diameter / self.end_effector_shrink_factor
				self.action_end_effector = 0
				self.counter_end_effector = 0

		self.counter_underscore += 1
		if (self.counter_underscore == self.underscore_blinking_time):
			self.paint_underscore = not self.paint_underscore
			self.counter_underscore = 0


		if (self.counter_rest_phase > 0):
			self.counter_rest_phase = self.counter_rest_phase-1
			

		self.repaint()
		
		# We keep the bit ON for several cycles
		if (self.lpt_type == 2):
			if (self.counter_lpt > 0):
				self.counter_lpt -=1
			elif (self.counter_lpt == 0):
				self.lpt.write(0)
				self.counter_lpt = -1

		if (self.send_trigger):
			if (self.use_hwtrigger):

				if (self.lpt_type == 1):
					self.lpt.signal(1)
				elif (self.lpt_type == 2):
					self.lpt.write(1)
					self.counter_lpt = 5
				else:
					print "Unknown LPT Trigger!! Exiting..."		
					exit()
				self.send_trigger = 0
			else:
				bci.id_msg.SetBlockIdx(bci.CurICindex)
				bci.id_msg.SetEvent(1)
				bci.iDsock.sendall(bci.id_serializer.Serialize())

			self.send_trigger = 0
			# Send trigger to Eye-tracker
			if (self.connect_eye):
				#This supplies the title at the bottom of the eyetracker display
				message ="record_status_message 'Trial'"
				#message ="record_status_message 'Trial %d'"%(self.num_trials_executed)
				self.eyetracker.sendCommand(message)       	
				#Always send a TRIALID message before starting to record.
				#EyeLink Data Viewer defines the start of a trial by the TRIALID message.  
				#This message is different than the start of recording message START that is logged when the trial recording begins. 
				#The Data viewer will not parse any messages, events, or samples, that exist in the data file prior to this message.
				msg = "TRIALID New Event"
				#msg = "TRIALID %s"%self.num_trials_executed
				self.eyetracker.sendMessage(msg)


		#self.tt2 = time()
		#print self.tt2-self.tt
		#self.tt = self.tt2
        
	def paintEvent(self, e):
		
		qp = QtGui.QPainter()
		qp.begin(self)
		self.paintInterface(qp)
		qp.end()

        
	def paintInterface(self, qp):

		qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
		
		# Fill background
		qp.fillRect( 0, 0, self.screen_width, self.screen_height, self.color_background )
				
		# Target

		if ((self.execution_mode == self.ONLINE_RUN) | (self.execution_mode == self.ONLINE_FREE_RUN)):
		# if (self.execution_mode == 3):
			qp.setBrush(self.color_target_ONLINE_FREEMODE)
		else:
			qp.setBrush(self.color_target)	

		qp.drawRect(self.init_position_x + (self.position_target_x-1)*(self.tile_width + self.gap_x), 
					self.init_position_y + (self.position_target_y-1)*(self.tile_height + self.gap_y), 
					self.tile_width, self.tile_height)
		
		# Photodiode
		if (self.draw_photodiode):
			qp.setPen(QtGui.QColor(100,100,100))
			if (self.action_executed):
				qp.setBrush(QtGui.QColor(255,255,255))
			else:
				qp.setBrush(QtGui.QColor(0,0,0))
			qp.drawRect( self.screen_width-self.screen_width/25, 0, self.screen_width/25, self.screen_width/25 )
		


		# Grid
		self.pen = QtGui.QPen(self.color_grid)
		self.pen.setWidth(self.grid_thickness)
		qp.setPen(self.pen)
		qp.setBrush(QtCore.Qt.NoBrush)
		for x in range(0, self.num_tiles_x):
			for y in range(0, self.num_tiles_y):
				qp.drawRect(self.init_position_x + x*(self.tile_width + self.gap_x), 
							self.init_position_y + y*(self.tile_height + self.gap_y), 
							self.tile_width, self.tile_height)              
				
				
							
		
		
		# Text			
		qp.setFont(self.font)
		counter = 0
		for y in range(0, self.num_tiles_y):
			for x in range(0, self.num_tiles_x):
				qp.drawText(self.init_position_x + x*(self.tile_width + self.gap_x) + (self.tile_width - self.fm.width(self.characters[counter]))/2, 
							self.init_position_y + y*(self.tile_height + self.gap_y) + self.tile_height - (self.tile_height - (self.font.pixelSize()/6 + self.fm.height())/2)/2, 
							self.characters[counter])              
				counter += 1

		# Word in progress
		qp.setFont(self.font)
		#word = "hello world_"
		#self.written_text = 'dummy'
		if (self.paint_underscore):
			word_to_write = self.written_text + '_'
		else:
			word_to_write = self.written_text

		w = 15*len(self.written_text)		
		qp.drawText((self.screen_width - w)/2, (self.screen_height - (self.tile_height * (self.num_tiles_y + 1)) )/2,  word_to_write)	#self.screen_widt	


		# Device
		qp.setPen(QtCore.Qt.NoPen)					
		qp.setBrush(self.color_device)
		qp.drawEllipse(	self.init_position_x + (self.position_device_x-1)*(self.tile_width + self.gap_x) + (self.tile_width-self.device_diameter)/2, 
						self.init_position_y + (self.position_device_y-1)*(self.tile_height + self.gap_y) + (self.tile_height-self.device_diameter)/2, 
						self.device_diameter, self.device_diameter)
		
		# end effector			

		if (self.increase_saliency_end_effector):
			if (self.action_end_effector):
				qp.setBrush(self.color_end_effector)              	
				qp.drawRect(self.init_position_x + (self.position_device_x-1)*(self.tile_width + self.gap_x), 
						self.init_position_y + (self.position_device_y-1)*(self.tile_height + self.gap_y), 
						self.tile_width, self.tile_height)
		
		# Rest phase
		if (self.counter_rest_phase > 0):
			self.color_text.setAlpha(255 * self.counter_rest_phase / self.rest_phase_duration)
			self.color_rect.setAlpha(255 * self.counter_rest_phase / self.rest_phase_duration)
			qp.setPen(QtCore.Qt.NoPen)					
			qp.setBrush(self.color_rect)
			qp.drawRoundedRect(((self.screen_width-(self.counter_rest_phase * self.rest_phase_bar_length / self.rest_phase_duration))/2), (self.screen_height - self.fm.height())/2, 
								self.counter_rest_phase * self.rest_phase_bar_length / self.rest_phase_duration, self.fm.height(), 5, 5)
			# Rest phase
			qp.setFont(self.font)
			qp.setPen(self.color_text)
			qp.drawText((self.screen_width-self.fm.width("RESTING"))/2, (self.screen_height - self.fm.height())/2 +  self.fm.height() - self.font.pixelSize()/6, "RESTING")
							              																
	def keyPressEvent(self, event):
		key = event.key()
		if (key == QtCore.Qt.Key_Up):
			self.execute_action(self.ACTION_UP)
		elif (key == QtCore.Qt.Key_Down):	
			self.execute_action(self.ACTION_DOWN)
		elif (key == QtCore.Qt.Key_Left):	
			self.execute_action(self.ACTION_LEFT)
		elif (key == QtCore.Qt.Key_Right):	
			self.execute_action(self.ACTION_RIGHT)
		elif (key == QtCore.Qt.Key_Space):	
			self.execute_action(self.ACTION_END_EFFECTOR)
		elif (key == QtCore.Qt.Key_7):	
			self.execute_action(self.ACTION_UP_LEFT)
		elif (key == QtCore.Qt.Key_8):	
			self.execute_action(self.ACTION_UP)
		elif (key == QtCore.Qt.Key_9):	
			self.execute_action(self.ACTION_UP_RIGHT)
		elif (key == QtCore.Qt.Key_4):	
			self.execute_action(self.ACTION_LEFT)
		elif (key == QtCore.Qt.Key_5):	
			self.execute_action(self.ACTION_END_EFFECTOR)
		elif (key == QtCore.Qt.Key_6):	
			self.execute_action(self.ACTION_RIGHT)
		elif (key == QtCore.Qt.Key_1):	
			self.execute_action(self.ACTION_DOWN_LEFT)
		elif (key == QtCore.Qt.Key_2):	
			self.execute_action(self.ACTION_DOWN)
		elif (key == QtCore.Qt.Key_3):	
			self.execute_action(self.ACTION_DOWN_RIGHT)

		elif (key == QtCore.Qt.Key_Escape):	
			if (self.connect_eye):
				self.eyetracker.close(self.filename)

			self.lpt.close()
			exit()
	
	def execute_action(self, action):
		self.action_executed = not self.action_executed
		self.send_trigger = 1
		if (action == self.ACTION_UP):
			self.position_device_y = self.position_device_y-1;
		elif (action == self.ACTION_DOWN):
			self.position_device_y = self.position_device_y+1;
		elif (action == self.ACTION_LEFT):
			self.position_device_x = self.position_device_x-1;
		elif (action == self.ACTION_RIGHT):
			self.position_device_x = self.position_device_x+1;
		elif (action == self.ACTION_UP_LEFT):
			self.position_device_y = self.position_device_y-1;
			self.position_device_x = self.position_device_x-1;
		elif (action == self.ACTION_UP_RIGHT):
			self.position_device_y = self.position_device_y-1;
			self.position_device_x = self.position_device_x+1;			
		elif (action == self.ACTION_DOWN_LEFT):
			self.position_device_y = self.position_device_y+1;
			self.position_device_x = self.position_device_x-1;			
		elif (action == self.ACTION_DOWN_RIGHT):
			self.position_device_y = self.position_device_y+1;
			self.position_device_x = self.position_device_x+1;			
		elif (action == self.ACTION_END_EFFECTOR):
			self.device_diameter = self.device_diameter * self.end_effector_shrink_factor;
			self.action_end_effector = 1
	
	def update_phase(self, phase):
		if (phase == self.REST_PHASE):
			self.counter_rest_phase = self.rest_phase_duration
	
	def update_target_and_state(self, message):
		self.update_target(math.floor(message / self.TID_TARGET_AND_STATE_MULTIPLIER))
		self.update_state(message % self.TID_TARGET_AND_STATE_MULTIPLIER)
		if (self.execution_mode == 1 and self.first_move == 1):
			self.update_text((message % self.TID_TARGET_AND_STATE_MULTIPLIER) + self.TID_LETTER)

	def update_target_and_state_and_letter(self, message):
		print math.floor(message / self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER)
		print math.floor((message - (math.floor(message / self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER))*self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER)/100)
		print message % 100
		self.update_target(math.floor(message / self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER))
		self.update_state(math.floor((message - (math.floor(message / self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER))*self.TID_TARGET_AND_STATE_AND_LETTER_MULTIPLIER)/100))
		self.update_text((message % 100)+self.TID_LETTER)
	
	def update_state(self, idx_state):
		x = idx_state % self.num_tiles_x
		y = math.floor(idx_state / self.num_tiles_x) + 1
		if (x == 0):
			self.position_device_x = self.num_tiles_x;
			self.position_device_y = y-1;
		else:
			self.position_device_x = x;
			self.position_device_y = y;
			
	def update_target(self, idx_target):
		x = idx_target % self.num_tiles_x
		y = math.floor(idx_target / self.num_tiles_x) + 1
		if (x == 0):
			self.position_target_x = self.num_tiles_x;
			self.position_target_y = y-1;
		else:
			self.position_target_x = x;
			self.position_target_y = y;

	def update_text(self, idx_letter):
		self.written_text = self.written_text + self.characters[idx_letter-self.TID_LETTER-1];

	
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
		
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = RASER()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
