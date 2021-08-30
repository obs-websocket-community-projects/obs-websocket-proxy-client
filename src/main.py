import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s")
import sys
import argparse
import asyncio
import websockets
import msgpack
import simpleobsws
import pyqrcode

obs = None
ws = None
isIdentified = False

def print_qr(text):
    qr = pyqrcode.create(text)
    lines = qr.text().replace('0', '██').replace('1', '░░').split('\n')
    newLines = []
    for line in lines[3:-4]:
        newLines.append(line[6:-6])
    out = '\n'.join(newLines)
    print(out)

async def handle_obs_event(eventType, eventIntent, eventData):
    if not isIdentified or not ws.open:
        return
    emitData = {
        'op': 5,
        'd': {
            't': eventType,
            'i': eventIntent,
            'd': eventData
        }
    }
    await ws.send(msgpack.packb(emitData))

async def main():
    global obs
    global ws
    global isIdentified
    obs = simpleobsws.WebSocketClient(url='ws://{}:{}'.format(flags.obsHost, flags.obsPort), password=flags.obsPassword)
    obs.register_event_callback(handle_obs_event)
    try:
        await obs.connect()
        logging.info('Connected to the obs-websocket server.')
    except:
        logging.exception('Connection to obs-websocket failed:\n')
        return
    if not await obs.wait_until_identified():
        logging.error('Failed to identify with obs-websocket.')
        return
    logging.info('Successfully identified with the obs-websocket server.')

    try:
        ws = await websockets.connect('wss://{}:{}'.format(flags.proxyHost, flags.proxyPort))
        logging.info('Connected to the proxy server.')
    except:
        logging.exception('Connection to proxy server failed:\n')
        return
    cloudRegion = None
    try:
        while True:
            try:
                msg = await ws.recv()
            except websockets.exceptions.WebSocketException:
                logging.warning('Got websocket exception. Exiting Session.')
                break
            try:
                messageData = msgpack.unpackb(msg)
            except:
                logging.warning('Unable to decode incoming binary message (MsgPack). Bytes: {}'.format(msg))
                break
            #logging.info('Incoming message: {}'.format(messageData))
            opCode = messageData.get('op')
            if opCode == 0: # Hello
                cloudRegion = messageData['d']['region']
                originalHello = obs._get_hello_data()
                responseData = {
                    'op': 1,
                    'd': {
                        'sessionKey': flags.sessionKey,
                        'obsWebSocketVersion': originalHello.get('obsWebSocketVersion', '5.0.0'),
                        'obsRpcVersion': originalHello.get('rpcVersion', 1)
                    }
                }
                await ws.send(msgpack.packb(responseData))
            elif opCode == 2: # Identified
                isIdentified = True
                logging.info('Successfully identified with the proxy server.\n\nConnect Port: `{}`\nConnect Password: `{}`\n\nConnect QR:'.format(messageData['d']['cloudConnectPort'], messageData['d']['cloudConnectPassword']))
                print_qr('obswss://{}.proxy.obs-websocket.io:{}/{}'.format(cloudRegion, messageData['d']['cloudConnectPort'], messageData['d']['cloudConnectPassword']))
            elif opCode == 6: # Request
                requestType = messageData['d']['t']
                requestData = messageData['d'].get('d')
                req = simpleobsws.Request(requestType, requestData)
                ret = await obs.call(req)
                emitData = {
                    'op': 7,
                    'd': {
                        'cid': messageData['d'].get('cid'),
                        't': requestType,
                        'id': messageData['d'].get('id'),
                        's': {},
                        'd': None
                    }
                }
                if ret.ok():
                    emitData['d']['s']['result'] = True
                    emitData['d']['s']['code'] = 100
                else:
                    emitData['d']['s']['result'] = False
                    emitData['d']['s']['code'] = ret.requestStatus.code
                    if ret.requestStatus.comment:
                        emitData['d']['s']['comment'] = ret.requestStatus.comment
                if ret.has_data():
                    emitData['d']['d'] = ret.responseData
                await ws.send(msgpack.packb(emitData))
            elif opCode == 8: # RequestBatch
                pass # TODO: Handle
            else:
                logging.warning('Received message with unknown OP code: `{}`'.format(opCode))
    except:
        logging.exception('Got exception in connection handling:\n')
    await obs.disconnect()
    await ws.close()

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost', type=str, help='obs-websocket host', dest='obsHost')
parser.add_argument('--port', default='4444', type=int, help='obs-websocket port', dest='obsPort')
parser.add_argument('--password', default='', type=str, help='obs-websocket password', dest='obsPassword')
parser.add_argument('--proxy-host', default='', type=str, help='proxy.obs-websocket.io region domain', dest='proxyHost')
parser.add_argument('--proxy-port', default='4000', type=int, help='proxy.obs-websocket.io region port', dest='proxyPort')
parser.add_argument('--proxy-session-key', default='', type=str, help='proxy.obs-websocket.io session key', dest='sessionKey')
flags = parser.parse_args()

if not flags.proxyHost:
    logging.error('Please specify the proxy host domain.')
    sys.exit(1)

if not flags.proxyHost.endswith('.proxy.obs-websocket.io'):
    logging.error('Proxy host not recognized. Please use an official proxy host.')
    sys.exit(1)

if not flags.sessionKey:
    logging.error('Please specify the proxy session key.')
    sys.exit(1)

asyncio.run(main())
