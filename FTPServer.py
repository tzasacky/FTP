import sys
import os
import socket
"""
FTP Server
NAME: TYE ZASACKY

Commands Requiring Arguments
USER<SP+><username><CRLF>
PASS<SP+><password><CRLF>
TYPE<SP+><type-code><CRLF>
PORT<SP+><host-port><CRLF>
RETR<SP+><pathname><CRLF>

Standalone Commands
SYST<CRLF>
NOOP<CRLF>
QUIT<CRLF>
"""


def build_msg_dict():
	"""
	Builds dictionary of messages corresponding to code
	Several 200 codes exist so they are split in dictionary

	Output: Dictionary of messages
	"""
	codes = [150, 200, 201, 202, 203, 215, 220, 221, 230, 250, 331, 500, 501, 502, 503, 530, 550]
	strings = ["150 File status okay.",
			   "200 Command OK.", 												 #200
			   "200 Type set to I.",											 #201
			   "200 Type set to A.",											 #202
			   "200 Port command successful ({}.{}.{}.{},{}).", 				 #203
			   "215 UNIX Type: L8.",
			   "220 COMP 431 FTP server ready.",
			   "221 Goodbye.",
			   "230 Guest login OK.",
			   "250 Requested file action completed.",
			   "331 Guest access OK, send password.",
			   "500 Syntax error, command unrecognized.",
			   "501 Syntax error in parameter.",
			   "502 Command not implemented.",
			   "503 Bad sequence of commands.",
			   "530 Not logged in.",
			   "550 File not found or access denied."]
	return dict(zip(codes, strings))
	
def chk_syntax(line):
	# check for CRLF
	if line[-2:] != "\r\n":
		return False
	# check that param is ascii characters only
	try:
		line.encode('ascii')
	except UnicodeEncodeError:
		return False
	else:
		return True

def transfer_file(param):
	# isolate to just parameter. Did it already elsewhere.
	if param[0] == '/' or param[0] == '\\':
		param = param[1:]

	if not os.path.isfile(param):
		write_and_send(msg.get(550) + "\r\n")
		return False
	try:
		file = open(param, "rb")
		transferSocket.sendfile(file)
		transferSocket.close()
	except:
		write_and_send(msg.get(550) + "\r\n")
		return False
	write_and_send(msg.get(150) + "\r\n")
	write_and_send(msg.get(250) + "\r\n")
	return True

def type_cmd(param):
	if param == "I":
		write_and_send(msg.get(201) + "\r\n")
	elif param == "A":
		write_and_send(msg.get(202) + "\r\n")
	else:
		write_and_send(msg.get(501) + "\r\n")


def port_cmd(param):
	# Split by commas, check numbers for validity
	param = param.split(',')
	if len(param) != 6:
		write_and_send(msg.get(501) + "\r\n")
		return False
	else:
		for num in param:
			if int(num) > 255 or int(num) < 0:
				write_and_send(msg.get(501) + "\r\n")
				return False
		# Tests passed. Calculate port and return specially formatted string
		port = int(param[4]) * 256 + int(param[5])
		write_and_send(msg.get(203).format(param[0], param[1], param[2], param[3], port) + "\r\n")

		#set up transfer connection
		transferSocket.connect(("{}.{}.{}.{}".format(param[0], param[1], param[2], param[3]), port))
		return True


def createSocket(PortNum):
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serverSocket.bind(("", PortNum))
	serverSocket.listen(1)  # Allow only one connection at a time
	return serverSocket

def write_and_send(message):
	sys.stdout.write(message)
	sock.send(message.encode())


if __name__ == "__main__":
	#Initialize selector socket for connect requests
	PortNum = int(sys.argv[1])
	serverSocket = createSocket(PortNum)
	msg = build_msg_dict()
	while True:
		# Listen for accepts, send ready message
		(sock, address) = serverSocket.accept()
		write_and_send(msg.get(220) + "\r\n")

		# Set flags for state-keeping, create command list
		user = False
		login = False
		port = False
		fileNum = 1
		arg_commands = ['USER', 'PASS', 'TYPE', 'PORT', 'RETR']
		solo_commands = ['SYST', 'NOOP', 'QUIT']

		while True:
			#Try to read continuously
			command = sock.recv(1024).decode()
			if not command:
				continue

			# echo command
			sys.stdout.write(command)

			# check that command is valid
			commandCode = command.split()[0].upper()
			if commandCode not in arg_commands and commandCode not in solo_commands:
				if (len(commandCode) == 3 or len(commandCode) == 4):
					write_and_send(msg.get(502) + "\r\n")
				else:
					write_and_send(msg.get(500) + "\r\n")
				continue

			# check syntax
			if chk_syntax(command):
				param = command[5:-2].lstrip()

				# Quit pre-empts all other commands
				if commandCode == 'QUIT':
					if len(command) == 6:
						write_and_send(msg.get(221) + "\r\n")
						break
					else:  # Invalid syntax
						write_and_send(msg.get(501) + "\r\n")

				# Check against state for validity.
				# Activate FTP if PORT, RETR pair identified
				if login:
					if commandCode == 'TYPE':
						type_cmd(param)
					elif commandCode == "PORT":
						transferSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						if port_cmd(param):
							port = True
					elif commandCode == "RETR":
						if port:
							if transfer_file(param):
								port = False
						else:
							write_and_send(msg.get(503) + "\r\n")
					elif commandCode == 'SYST':
						if len(command) == 6:
							write_and_send(msg.get(215) + "\r\n")
						else:  # Invalid syntax
							write_and_send(msg.get(501) + "\r\n")
					elif commandCode == 'NOOP':
						if len(command) == 6:
							write_and_send(msg.get(200) + "\r\n")
						else:  # Invalid syntax
							write_and_send(msg.get(501) + "\r\n")
				else:
					if commandCode == 'USER':
						user = True
						write_and_send(msg.get(331) + "\r\n")
					elif user:
						if commandCode == 'PASS':
							login = True
							write_and_send(msg.get(230) + "\r\n")
						else:
							write_and_send(msg.get(503) + "\r\n")
					else:
						write_and_send(msg.get(530) + "\r\n")
			else:  # Invalid command
				write_and_send(msg.get(500) + "\r\n")