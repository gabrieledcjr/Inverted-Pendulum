/********************************************************
 *   File Name: main.c
 *
 *   Description:
 *              main file,
 *
 *
 *********************************************************/

//Clock settings

// PIC32MX340F512H Configuration Bit Settings

// 'C' source line config statements

#include <xc.h>

/* Oscillator Settings
*/
#pragma config FNOSC = PRIPLL // Oscillator selection
#pragma config POSCMOD = HS // Primary oscillator mode
#pragma config FPLLIDIV = DIV_2 // PLL input divider
#pragma config FPLLMUL = MUL_20 // PLL multiplier
#pragma config FPLLODIV = DIV_1 // PLL output divider
#pragma config FPBDIV = DIV_2 // Peripheral bus clock divider
#pragma config FSOSCEN = OFF // Secondary oscillator enable


//includes
#include "system.h"

/*************************************************************************
 Constants
 ************************************************************************/

/*************************************************************************
 Structure Definitions
 ************************************************************************/

/*************************************************************************
 Enums
 ************************************************************************/

/*************************************************************************
 Global Variables
 ************************************************************************/
uint8 tx1buff[100] = {0};
uint8 rx1buff[50] = {0};
uint8 packet[6] = {0};
sint16 ArmCount = 0;
sint16 MotorCount = 0;
uint8 data = 0;
uint8 prev_data = 0;

/*************************************************************************
 Function Declarations
 ************************************************************************/
void setupUART(void);
void setupPorts(void);
void updateTicks(void);
void packetize(void);

/*************************************************************************
 Main Code
 ************************************************************************/

/*
    uint8 command = 0xE0;
    if ((data & 0b1) == 0b1)
    {
       // send_UART (UART2, 1, command);
        U2TXREG = command;
    }
    else if ((data & 0b10) == 0b10)
    {
        //send_UART (UART2, 1, command);
        U2TXREG = command;
    }
 */
int main(void) {
    setupUART();
    setupPorts();

    //Timer setup
    //Need the timer for periodic transmission of data ot the computer
    TRISDbits.TRISD0 = 0;
    T1CONbits.TCKPS = 0;
    PR1 = 1;
    T1CONbits.ON = 1;
    IEC0bits.T1IE =1;
    IPC1bits.T1IP = 7;

    INTEnableSystemMultiVectoredInt();
    INTEnableInterrupts();

    while (1) {
        data = (PORTB & 0b111100) | ((PORTG & 0b110000000) >> 7);
        
        if(data ^ prev_data){
            //update the counters
            updateTicks();
            
            //U1TXREG = data;
            //send_UART(UART1, 1, &data);
        }
        prev_data = data;
    }

    return 0;
}

//setup the required ports for digital inputs
void setupPorts(void)
{
    //Ensure the Analog Pins are set to digital inputs
    AD1PCFGSET = 0xFF;

    TRISBSET = 0b111100;
    TRISGSET = 0b110000000;
}

//Function that computes ticks
void updateTicks(void)
{
    /*
     * Arm Encoder Data
     */

    //save the previous state of the arm
    uint8 LastState = prev_data >> 4;
        
    switch (data >> 4)
    {
            case 0: //current state = 00
                    //if LastState=01, increment Count (CW)
                    //else LastState=10, decrement Count (CCW)
                    LastState==1 ? ArmCount++ : ArmCount--;
                    break;
            case 1: //current state = 01
                    //if LastState=11, increment Count (CW)
                    //else LastState=00, decrement Count (CCW)
                    LastState==3 ? ArmCount++ : ArmCount--;
                    break;
            case 2: //current state = 10
                    //if LastState=00, increment Count (CW)
                    //else LastState=11, decrement Count (CCW)
                    LastState==0 ? ArmCount++ : ArmCount--;
                    break;
            case 3: //current state = 11
                    //if LastState=10, increment Count (CW)
                    //else LastState=01, decrement Count (CCW)
                    LastState==2 ? ArmCount++ : ArmCount--;
                    break;
    }

    /*
     * Motor Encoder Data Processing
     */

    //save the previous state of the motor
    uint8 LastState = prev_data & 0b1100 >> 2;
    
    switch (data & 0b1100 >> 2)
    {
            case 0: //current state = 00
                    //if LastState=01, increment Count (CW)
                    //else LastState=10, decrement Count (CCW)
                    LastState==1 ? MotorCount++ : MotorCount--;
                    break;
            case 1: //current state = 01
                    //if LastState=11, increment Count (CW)
                    //else LastState=00, decrement Count (CCW)
                    LastState==3 ? MotorCount++ : MotorCount--;
                    break;
            case 2: //current state = 10
                    //if LastState=00, increment Count (CW)
                    //else LastState=11, decrement Count (CCW)
                    LastState==0 ? MotorCount++ : MotorCount--;
                    break;
            case 3: //current state = 11
                    //if LastState=10, increment Count (CW)
                    //else LastState=01, decrement Count (CCW)
                    LastState==2 ? MotorCount++ : MotorCount--;
                    break;
    }

    //update the previous data for next update
    prev_data = data;
}

//Setup the UART communication
void setupUART(void)
{
    //Initialize the UART signals
    initialize_UART(2000000, 40000000, UART1, rx1buff, 50, tx1buff, 100, TRUE, TRUE, NULL, NULL);
}

void packetize(void)
{
    //Packetize the data to send
    packet[0] = 0x0A;
    packet[1] = ArmCount >> 8; //High data of ArmCount
    packet[2] = ArmCount & 0xFF; //Low data of ArmCount
    packet[3] = MotorCount >> 8;
    packet[4] = MotorCount & 0xFF;
    packet[5] = data & 3;
}

void __ISR(_TIMER_1_VECTOR, IPL7AUTO) Timer_Handler_1(void) {
    asm volatile ("di"); //disable interrupt

    //LATDbits.LATD0 = ~LATDbits.LATD0;
    packetize();
    //Send the latest values to the computer
    send_UART(UART1, 6, packet);

    IFS0bits.T1IF = 0; //clear the interrupt flag
    asm volatile ("ei"); //reenable interrupts
}

/*
void UartStuff(uint speed, uint pb_clk, boolean tx_en, boolean rx_en) {
    U1BRG = pb_clk / (16 * speed) - 1; //calculate the proper baud rate

    U1MODEbits.PDSEL = 0; //parity and data size selection bits (no parity, 8bit)


    IEC0bits.U1TXIE = (tx_en & 0b1); //enable or disable the rx/tx interrupts
    IEC0bits.U1RXIE = (rx_en & 0b1);
    IPC6bits.U1IP = 7; //set interrupt priority to 7

    U1STAbits.UTXISEL = 2; //set tx interrupt to fire when the tx buffer is empty
    U1STAbits.URXISEL = 0; //set rx interrupt to fire whenever a new byte is received

    U1STAbits.UTXEN = (tx_en & 0b1); //enable or disable the rx/tx modules
    U1STAbits.URXEN = (rx_en & 0b1); //enable or disable the rx/tx modules

    U1MODEbits.ON = 1; //enable the UART
}
*/