import spidev
from gpiozero import DigitalOutputDevice, Button
from time import sleep

# Configurazione pin GPIO
cs = DigitalOutputDevice(23)  # Chip Select (NSS) su GPIO 8
reset = DigitalOutputDevice(25)  # Reset su GPIO 25
dio0 = Button(24)  # DIO0 su GPIO 24 per gestire l'interrupt

# Configurazione SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # Usa il bus SPI 0 e seleziona il dispositivo 0
spi.max_speed_hz = 500000  # Imposta la velocità SPI

# Funzione per scrivere su un registro del LoRa
def write_register(register, value):
    cs.off()  # Attiva il chip
    spi.xfer([register | 0x80, value])  # Imposta il bit più alto per scrivere
    cs.on()  # Disattiva il chip

# Funzione per leggere da un registro del LoRa
def read_register(register):
    cs.off()  # Attiva il chip
    response = spi.xfer([register & 0x7F, 0])  # Il bit più alto è 0 per leggere
    cs.on()  # Disattiva il chip
    return response[1]

# Inizializzazione del LoRa
def setup_lora():
    reset.off()  # Porta il modulo in reset
    sleep(0.01)
    reset.on()  # Riporta il modulo dallo stato di reset
    sleep(0.01)
    
    # Configura il modulo LoRa a 433 MHz
    write_register(0x01, 0x81)  # Modalità sleep e LoRa
    write_register(0x06, 0x6C)  # Freq a 433 MHz
    write_register(0x07, 0x80)
    write_register(0x08, 0x00)
    # Imposta la banda, spreading factor, e coding rate
    write_register(0x1D, 0x72)  # BW = 500kHz, CR = 4/5
    write_register(0x1E, 0x74)  # SF = 7

# Funzione per gestire la ricezione tramite interrupt
def on_receive():
    if read_register(0x12) & 0x40:  # Verifica se ci sono dati ricevuti (flag RX_DONE)
        payload_length = read_register(0x13)  # Legge la lunghezza del pacchetto
        cs.off()
        payload = spi.xfer([0x00] * payload_length)
        cs.on()
        print("Received:", bytes(payload).decode('utf-8', 'ignore'))
        print("Payload length:", payload_length)
        write_register(0x12, 0x40)  # Pulisce il flag RX_DONE

# Inizializzazione del LoRa e gestione del reset
setup_lora()

# Imposta un listener sul pin DIO0 per rilevare pacchetti ricevuti
dio0.when_pressed = on_receive

print("Waiting for incoming messages...")  # Stampa che indica lo stato di attesa

# Loop principale per mantenere attivo il programma
while True:
    sleep(1)
