function rec_string=query_TCP(TCPIPobj,Message)

fprintf(TCPIPobj,Message);
rec_string=fscanf(TCPIPobj);






