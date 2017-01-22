%-------------------------------------------------------------------------
%  Spellman DXM power supply control
% 
%-------------------------------------------------------------------------

%-------------------------------------------------------------------------
clc
clear all;               %clear all variables
%close all;              %close all plots
delete(instrfindall);    %clear all open ports


%Open TCP/IP connectopn to power supply
%-------------------------------------------------------------------------
TCP_IP_spellman_DXM='192.168.1.4';
port_spellman_DXM=50001;
TCPIPobj_spellman_DXM = tcpip(TCP_IP_spellman_DXM,...
        port_spellman_DXM, 'Timeout',1,'Terminator',3);
fopen(TCPIPobj_spellman_DXM);


% parameters for saving file
%-------------------------------------------------------------------------
lableStr='';            %label to append to end of file name


% parameters for operation
%-------------------------------------------------------------------------
timeInterval=0.5;       %pause time between measurements in sec

%-------------------------------------------------------------------------
%setup variables
%-------------------------------------------------------------------------
STX=char(2);    %ASCII 0x02 Start of Text character
ETX=char(3);    %ASCII 0x03 End of Text character

kV_out_Arr=[];        %voltage out array
kV_set_Arr=[];        %voltage set array
mA_out_Arr=[];        %current out array
mA_set_Arr=[];        %current set array
time_Arr=[];     %


% Display power supply information
%-------------------------------------------------------------------------
disp('Spellman DXM Control')
disp(['HV On Hours= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'21,'])])
disp(['Status= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'22,'])])
disp(['DSP Version= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'23,'])])
disp(['Hardware Version= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'24,'])])
disp(['Webserver Version= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'25,'])])
disp(['Model Number= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'26,'])])
disp(['Network Settings= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'50,'])])
disp(['Interlock Status= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'55,'])])
disp(['Faults= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'68,'])])


disp([' '])
disp(['Prog kV Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'10,0,'])])   %0-4095
disp(['Prog mA Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'11,0,'])])   %0-4095
disp(['Prog Fil Lim Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'12,0,'])])   %(0 – 4095 = 0 – 5 amps)
disp(['Prog Fil Preheat Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'13,0,'])])   %(0 – 4095 = 0 – 2.5 amps)
disp(['Req kV Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'14,'])])   %0-4095
disp(['Req mA Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'15,'])])   %0-4095
disp(['Req Fil Lim Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'16,'])])   %(0 – 4095 = 0 – 5 amps)
disp(['Req Fil Preheat Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'17,'])])   %(0 – 4095 = 0 – 2.5 amps)
disp(['Req Analog Mon= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'19,'])])   %(0 – 4095 = 0 – 2.5 amps)

disp(['Req kV Mon= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'60,'])])
disp(['Req mA Mon= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'61,'])])
disp(['Req Fil Feedback= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'62,'])])
disp(['Req -15V LVPS= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'65,'])])

disp(['Local/Remote= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'99,1,'])]) %1 = Remote, 0 = Local
disp(['HV On/Off= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'98,0,'])]) %1 = HV on, 0 = HV off





%open plot
%-------------------------------------------------------------------------
fontsize=20;
takeData=1;
figure(1);
xlabel('time[s]');
ylabel('Voltage[kV]');
grid on;

disp([' '])
disp(['Data Run'])
disp(['Local/Remote= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'99,1,'])]) %1 = Remote, 0 = Local
disp(['HV On/Off= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'98,1,'])]) %1 = HV on, 0 = HV off
pause(0.2)

tic             %start timer
kV_max=5;       %max voltage to output at time_peak
time_peak=5;    %time to reach peak voltage
disp(['Prog mA Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'11,45,'])])   %0-4095
while (takeData==1)
    time_sec=toc;
    if(time_sec<=time_peak)
        kV_set=kV_max*time_sec/time_peak;
        kV_DAC=floor(4095*kV_set/70);
    elseif((time_sec>time_peak)&&(time_sec<=2*time_peak))
        kV_set=kV_max*(2*time_peak-time_sec)/time_peak;
        kV_DAC=floor(4095*kV_set/70);
    elseif((time_sec>2*time_peak)&&(time_sec<=2*time_peak+2))
        kV_set=0;
        kV_DAC=floor(4095*kV_set/70);
    else
        takeData=0; %end loop
        continue;
    end
    
    query_TCP(TCPIPobj_spellman_DXM,[STX,'10,',num2str(kV_DAC),',']);   %program kV_out 0-4095
    pause(0.1)
    rec_string=query_TCP(TCPIPobj_spellman_DXM,[STX,'60,']);
    kV_out=70*sscanf(rec_string, [STX,'60, %f , '])/4095;
    disp(['Time= ',num2str(time_sec),' kV_set= ',num2str(kV_set),' kV_mon= ',num2str(kV_out)])
    
    kV_out_Arr=[kV_out_Arr,kV_out];        %voltage out array
    kV_set_Arr=[kV_set_Arr,kV_set];        %voltage set array
    time_Arr=[time_Arr,time_sec];          %

    plot(time_Arr,kV_out_Arr,'.-',time_Arr,kV_set_Arr,'.-');
    ylabel('Voltage[kV]');
    xlabel('Time[s]','FontSize',fontsize);
    grid on;
    set(gca,'FontSize',fontsize)
    legend({'kV Mon','kV Set'})
    
end




%set output to 0, remote prog, and HV off
disp(['Prog kV Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'10,0,'])])   %0-4095
disp(['Prog mA Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'11,0,'])])   %0-4095
disp(['Req kV Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'14,'])])   %0-4095
disp(['Req mA Set= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'15,'])])   %0-4095

disp(['Local/Remote= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'99,1,'])]) %1 = Remote, 0 = Local
disp(['HV On/Off= ',query_TCP(TCPIPobj_spellman_DXM,[STX,'98,0,'])]) %1 = HV on, 0 = HV off




% Clean up the serial object
%-------------------------------------------------------------------------
fclose(TCPIPobj_spellman_DXM);
delete(TCPIPobj_spellman_DXM);
clear TCPIPobj_spellman_DXM;

