import sys
import socket
import time

"""
FTP Client
NAME: TYE ZASACKY


Accepted Commands:
	CONNECT<SP>+<server-host><SP>+<server-port><EOL>
	GET<SP>+<pathname><EOL>
	QUIT<EOL>
"""


def processConnect(line, clientSocket):
	# Check that line is formatted correctly
	if len(line) != 3:
		print("ERROR -- server-host")
		return False

	#Check that host is valid
	host = line[1]
	if not host.replace(".", "").isalnum():
		print("ERROR -- server-host")
		return False

	# Check that port is valid
	port = line[2]
	if not port.isdigit() or port.startswith('0') or int(port) > 65535 :
		print("ERROR -- server-port")
		return False

	# Valid
	print("CONNECT accepted for FTP server at host {} and port {}".format(host, port))
	try:
		clientSocket.connect((host, int(port)))
	except:
		print("CONNECT failed")
		return False
	receiveReply(clientSocket)
	sendAndReceive(clientSocket, "USER anonymous\r\n")
	sendAndReceive(clientSocket, "PASS guest@\r\n")
	sendAndReceive(clientSocket, "SYST\r\n")
	sendAndReceive(clientSocket, "TYPE I\r\n")
	return True

def processGet(line, fileNum):
	#Check for invalid characters
	try:
		line.encode('ascii')
	except UnicodeEncodeError:
		print("ERROR -- pathname")
		return False

	#Tokenize here because different method than other commands
	#Check number of tokens and connection status
	tokens = line.split(None, 1)
	if len(tokens) != 2:
		print("ERROR -- pathname")
		return False

	pathName = tokens[1]
	print("GET accepted for {}".format(pathName))

	transferSocket = createTransferSocket(clientPort)

	# Format host address and send to server
	my_ip = socket.gethostbyname(socket.gethostname())
	my_ip = my_ip.replace('.', ',')
	portNums = divmod(clientPort, 256)
	if sendAndReceive(clientSocket, "PORT {},{},{}\r\n".format(my_ip, portNums[0], portNums[1])) != '200':
		transferSocket.close()
		return False


	if sendAndReceive(clientSocket, "RETR {}\r\n".format(pathName)) == '550': #File not found or access denied
		return False

	transferSocket, addr = transferSocket.accept()

	if(transferFile(transferSocket, fileNum)):
		return True



def processQuit(line):
	# Ensure quit isolated
	if len(line) == 1:
		print("QUIT accepted, terminating FTP client")
		sendAndReceive(clientSocket, "QUIT\r\n")
		return True
	else:
		print("ERROR -- request")
		return False

def createTransferSocket(clientPort):
	my_ip = socket.gethostbyname(socket.gethostname())
	transferSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	transferSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	transferSocket.bind((my_ip, clientPort))
	transferSocket.listen(1)  # Allow only one connection at a time
	return transferSocket

def transferFile(transferSocket, fileNum):
	file = open("retr_files/file{}".format(fileNum), "wb")
	stream = transferSocket.recv(1024)
	while (stream):
		file.write(stream)
		stream = transferSocket.recv(1024)
	transferSocket.close()
	return True

def replyParse(message):
	#Check for CRLF
	reply = ' '
	for line in message.splitlines(keepends=True):
		if line[-2:] != "\r\n":
			print("ERROR -- <CRLF>")
		else:
			#Cut off <CRLF>, split into code and text
			reply = line[:-2].split(' ', 1)

			#Check reply code is number
			if not reply[0].isdigit():
				print("ERROR -- reply-code")
			#Check reply code in range
			elif int(reply[0]) < 100 or int(reply[0]) >= 600:
				print("ERROR -- reply-code")
			#Reply code valid, check text
			else:
				try:
					reply[1].encode('ascii')
				except UnicodeEncodeError:
					print('ERROR -- reply-text')
				else:
					#Make sure no leading whitespace (except one space)
					if reply[1][0] == ' ':
						print('ERROR -- reply-text')
					#Everything valid, accept
					else:
						print("FTP reply {} accepted. Text is: {}".format(reply[0], reply[1]))
	return reply[0]

def receiveReply(clientSocket):
	message = clientSocket.recv(1024).decode()
	return replyParse(message)

def sendAndReceive(clientSocket, message):
	sys.stdout.write(message)
	clientSocket.send(message.encode())
	time.sleep(.1) #To ensure things come in correct order in typical use
	return receiveReply(clientSocket)


if __name__ == '__main__':
	#Initialize state-keeping variables
	connected = False
	clientPort = int(sys.argv[1])
	commands = ["connect", "get", "quit"]
	fileNum = 1

	#Initialize TCP socket for later connect
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	while True:
		for line in sys.stdin.read().splitlines(keepends = False):
			#Echo the line of input
			print(line)

			#Tokenize string, isolate command
			tokens = line.split()
			cmd = tokens[0].lower()

			#Isolated check because this takes precedence, but does not preempt other errors
			if cmd != "connect" and connected == False:
				print("ERROR -- expecting CONNECT")

			if cmd in commands:
				if cmd == 'connect':
					#Reset state if valid connect command
					if processConnect(tokens, clientSocket):
						connected = True
				elif cmd == 'get':
					#Increment port for valid get commands
					if connected:
						if processGet(line, fileNum):
							clientPort += 1
							fileNum += 1
				elif cmd == 'quit':
					#End processing if valid quit encountered
					if connected:
						if processQuit(tokens):
							break
			else:
				print("ERROR -- request")