import paho.mqtt.client as mqtt
import re
import datetime
import time


import aquaurban
from aquaurban import db
from aquaurban.model import Community, System, Bioinfo
#from aquaurban.ws_route import send_bioinfo

MQTT_ID = 'MAIN_SERVER'

BIOINFO_TOPIC		= lambda system_id: f'{system_id}/bio'
BIOINFO_TOPIC_CODE 	= r'(?P<system_id>\d+)/bio'
BIOINFO_DATA_CODE	= r'((?P<timestamp>\d+);)?(?P<waterlevel>[01-]);(?P<brightness>(\d+\.?\d*)|-);(?P<temperature>(\d+\.?\d*)|-);(?P<acidness>(\d+\.?\d*)|-)'

ACTION_TOPIC		= lambda system_id: f'{system_id}/act'
ACTION_TOPIC_CODE	= r'(?P<system_id>\d+)/act'
ACTION_DATA 		= lambda code: f'{code}'
ACTION_DATA_CODE	= r'(?P<code>\d)'

class MqttHub:
	connections = dict()

	def __init__ (self):
		for community in Community.query.all():
			self.connections[community.id] = mqttc = mqtt.Client(MQTT_ID, userdata=community.id)
			mqttc.on_connect = self.on_connect
			if community.username and community.password:
				mqttc.username_pw_set(community.username, community.password)
			mqttc.connect(community.host, community.port)
			mqttc.loop_start()
	
	def __getitem__ (self, i):
		return self.connections[i]
	
	def on_connect (self, mqttc, community_id, flags, rc):
		print(' * mqtt: connection established')
		print(' * mqtt: code =', rc)
		systems = Community.query.get(community_id).systems
		for system in systems:
			self.listen_system(system)

	def listen_system (self, system):
		mqttc = self[system.community_id]
		bioinfo_topic = BIOINFO_TOPIC(system.id)
		mqttc.subscribe(bioinfo_topic)
		mqttc.message_callback_add(bioinfo_topic, self.on_bioinfo)

	def on_bioinfo (self, mqttc, community_id, data):
		m_topic	= re.match(BIOINFO_TOPIC_CODE, data.topic)
		m_data 	= re.match(BIOINFO_DATA_CODE, data.payload.decode())
		bioinfo = Bioinfo(system_id=int(m_topic.group('system_id')))

		timestamp_str	= m_data.group('timestamp')
		waterlevel_str 	= m_data.group('waterlevel')
		brightness_str	= m_data.group('brightness')
		temperature_str = m_data.group('temperature')
		acidness_str	= m_data.group('acidness')

		bioinfo.timestamp = datetime.datetime.fromtimestamp(int(timestamp_str) if timestamp_str is not None else time.time())
		if waterlevel_str != '-': 	bioinfo.waterlevel 	= bool(int(waterlevel_str))
		if brightness_str != '-': 	bioinfo.brightness 	= float(brightness_str)
		if temperature_str != '-': 	bioinfo.temperature = float(temperature_str)
		if acidness_str != '-':		bioinfo.acidness	= float(acidness_str)

		db.session.add(bioinfo)
		db.session.commit()
		aquaurban.ws_route.send_bioinfo(bioinfo)

	def send_action (self, system, action):
		self[system.community_id].publish(ACTION_TOPIC(system.id), ACTION_DATA(action.value))