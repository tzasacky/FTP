# FTP
FTP Client/Server made for internet services &amp; protocols at UNC Chapel Hill 

FTP
Simple FTP server client program built for Internet Services & Protocols @ UNC Chapel Hill

Client/Server are interoperable with arbitrary FTP programs. Login feature is unimplemented (not required by class), so any USER/PASS combination is valid. Program is unaware of filetype, so user may need to append the correct file extension to open file.

Server:

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

Client:

  CONNECT<SP>+<server-host><SP>+<server-port><EOL>
  GET<SP>+<pathname><EOL>
  QUIT<EOL>
