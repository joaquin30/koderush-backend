
import socketio

# Crear cliente Socket.IO
sio = socketio.Client()

# Evento de conexión exitosa
@sio.event
def connect():
    print('Conectado al servidor.')

# Evento de desconexión
@sio.event
def disconnect():
    print('Desconectado del servidor.')

# Evento recibido si el match es inválido
@sio.on('invalid_match')
def on_invalid_match():
    print("Match inválido.")

def main():
    # IP del servidor (puede ser 'http://localhost:5000' o IP pública)
    server_url = 'http://127.0.0.1:5000' #input('Ingrese IP: ')
    
    try:
        sio.connect(server_url)
    except Exception as e:
        print(f'No se pudo conectar: {e}')
        return

    match_id = "match001" #input("Ingrese el Match ID: ").strip()

    # Emitir prepare_match
    print(f"Enviando evento prepare_match para el match {match_id}")
    sio.emit('prepare_match', {'match_id': match_id})

    input("Presione Enter para iniciar el match...")

    # Emitir start_match
    print(f"Iniciando match {match_id}")
    sio.emit('start_match', {'match_id': match_id})

    input("Presione Enter para salir...")
    sio.disconnect()

if __name__ == '__main__':
    main()
