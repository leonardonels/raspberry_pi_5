import spidev
import time

# Impostazioni del modulo SX1278
REG_OP_MODE = 0x01
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_RX_CONTINUOUS = 0x05

REG_FIFO = 0x00
REG_FIFO_RX_BASE_ADDR = 0x0F
REG_FIFO_ADDR_PTR = 0x0D
REG_PAYLOAD_LENGTH = 0x22

# Frequenze
FREQUENCY_MSB = 0x6C  # MSB parte della frequenza (per esempio 434 MHz)
FREQUENCY_MID = 0x80  # MID parte della frequenza
FREQUENCY_LSB = 0x00  # LSB parte della frequenza

class LoRa:
    def __init__(self, spi_channel=0, spi_speed=500000):
        # Inizializza l'interfaccia SPI
        self.spi = spidev.SpiDev()
        self.spi.open(0, spi_channel)
        self.spi.max_speed_hz = spi_speed
        self.reset()

    def reset(self):
        # Metti il dispositivo in modalità sleep
        self.write_register(REG_OP_MODE, MODE_SLEEP)
        time.sleep(0.1)

        # Imposta la frequenza (qui 434 MHz come esempio)
        self.write_register(0x06, FREQUENCY_MSB)
        self.write_register(0x07, FREQUENCY_MID)
        self.write_register(0x08, FREQUENCY_LSB)

        # Imposta la base FIFO
        self.write_register(REG_FIFO_RX_BASE_ADDR, 0x00)
        self.write_register(REG_FIFO_ADDR_PTR, 0x00)

        # Imposta la modalità in standby
        self.write_register(REG_OP_MODE, MODE_STDBY)

    def write_register(self, reg, value):
        self.spi.xfer2([reg | 0x80, value])  # 0x80 indica scrittura

    def read_register(self, reg):
        return self.spi.xfer2([reg & 0x7F, 0x00])[1]  # 0x7F indica lettura

    def start_receiving(self):
        # Imposta la modalità ricezione continua
        self.write_register(REG_OP_MODE, MODE_RX_CONTINUOUS)

    def read_payload(self):
        # Leggi la lunghezza del payload
        payload_length = self.read_register(REG_PAYLOAD_LENGTH)

        # Leggi i dati dal FIFO
        self.write_register(REG_FIFO_ADDR_PTR, 0x00)
        payload = []
        for _ in range(payload_length):
            payload.append(self.read_register(REG_FIFO))

        return bytes(payload)

# Utilizzo dello script
if __name__ == "__main__":
    lora = LoRa()
    lora.start_receiving()

    print("In attesa di messaggi LoRa...")

    try:
        while True:
            payload = lora.read_payload()
            if payload:
                try:
                    # Prova a decodificare il messaggio come stringa UTF-8
                    print("Messaggio ricevuto:", payload.decode('utf-8'))
                except UnicodeDecodeError:
                    # Se la decodifica fallisce, stampa i dati raw in formato esadecimale
                    print("Dati binari ricevuti (hex):", payload.hex())
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interruzione del programma.")
