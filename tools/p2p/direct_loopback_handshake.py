"""Research-only signed two-peer direct TCP handshake, no discovery server.

Proves local socket transport and mutual Ed25519 transcript authentication.
Does NOT prove WAN/NAT traversal, durable trust, production framing or game sync.
"""
import hashlib,json,os,re,socket,struct
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

DOMAIN=b'UR-Recomp-p2p-loopback-research-v1\x00'
MAX_FRAME=4096

def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('duplicate JSON key')
        d[k]=v
    return d

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()

def public_hex(key):
    return key.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw).hex()

def signed(key,kind,payload):
    msg=DOMAIN+kind.encode()+b'\x00'+canonical(payload)
    return {'kind':kind,'payload':payload,'sig':key.sign(msg).hex()}

def verify(packet,kind,expected_public):
    if type(packet) is not dict or set(packet)!={'kind','payload','sig'} or packet['kind']!=kind or type(packet['payload']) is not dict:
        raise ValueError('malformed signed packet')
    if type(packet['sig']) is not str or len(packet['sig'])!=128:raise ValueError('bad signature encoding')
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(expected_public)).verify(
        bytes.fromhex(packet['sig']),DOMAIN+kind.encode()+b'\x00'+canonical(packet['payload']))
    return packet['payload']

def read_exact(sock,n):
    chunks=[]
    while n:
        part=sock.recv(n)
        if not part:raise ValueError('short framed read')
        chunks.append(part);n-=len(part)
    return b''.join(chunks)

def recv(sock):
    n=struct.unpack('!I',read_exact(sock,4))[0]
    if not 1<=n<=MAX_FRAME:raise ValueError('oversized framed payload')
    return json.loads(read_exact(sock,n),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def send(sock,packet):
    raw=canonical(packet)
    if len(raw)>MAX_FRAME:raise ValueError('oversized send')
    sock.sendall(struct.pack('!I',len(raw))+raw)

def make_invite(initiator,responder_public,*,build='a'*64,session='b'*32,nonce=None,course='course:02'):
    payload={'version':1,'session':session,'build':build,'course':course,'mode':'2p',
             'inviter':public_hex(initiator),'invitee':responder_public,
             'nonce':nonce or os.urandom(16).hex()}
    return signed(initiator,'invite',payload)

def validate_invite(payload,expected_inviter,expected_invitee,expected_build,seen):
    if (set(payload)!={'version','session','build','course','mode','inviter','invitee','nonce'} or
        type(payload['version']) is not int or payload['version']!=1 or
        payload['mode']!='2p' or payload['course']!='course:02' or
        payload['inviter']!=expected_inviter or payload['invitee']!=expected_invitee or
        payload['build']!=expected_build or type(payload['nonce']) is not str or
        re.fullmatch('[0-9a-f]{32}',payload['nonce']) is None or
        type(payload['session']) is not str or re.fullmatch('[0-9a-f]{32}',payload['session']) is None or
        type(payload['build']) is not str or re.fullmatch('[0-9a-f]{64}',payload['build']) is None or
        any(type(payload[k]) is not str or re.fullmatch('[0-9a-f]{64}',payload[k]) is None
            for k in ('inviter','invitee'))):
        raise ValueError('invitation context mismatch')
    replay_key=(payload['inviter'],payload['session'],payload['nonce'])
    if replay_key in seen:raise ValueError('replayed invite')
    return replay_key

def responder_once(listener,responder,expected_inviter,expected_build,seen):
    conn,_=listener.accept()
    with conn:
        conn.settimeout(3)
        invite=recv(conn)
        payload=verify(invite,'invite',expected_inviter)
        replay_key=validate_invite(payload,expected_inviter,public_hex(responder),expected_build,seen)
        # In-memory single-process replay control only; not persistent storage.
        invite_digest=hashlib.sha256(canonical(invite)).hexdigest()
        response={'invite_digest':invite_digest,'session':payload['session'],'build':payload['build'],
                  'course':payload['course'],'mode':'2p','responder':public_hex(responder),
                  'nonce':os.urandom(16).hex()}
        packet=signed(responder,'response',response)
        send(conn,packet)
        finish=verify(recv(conn),'finish',expected_inviter)
        if finish!={'invite_digest':invite_digest,'response_digest':hashlib.sha256(canonical(packet)).hexdigest()}:
            raise ValueError('final transcript not bound')
        # Only a completed mutually authenticated transcript commits replay state.
        seen.add(replay_key)
        send(conn,{'status':'authenticated-loopback-only'})
        return response

def initiator_connect(address,initiator,responder_public,invite):
    with socket.create_connection(address,timeout=3) as conn:
        conn.settimeout(3)
        send(conn,invite)
        packet=recv(conn)
        response=verify(packet,'response',responder_public)
        p=invite['payload'];expected={'invite_digest':hashlib.sha256(canonical(invite)).hexdigest(),
            'session':p['session'],'build':p['build'],'course':p['course'],'mode':'2p',
            'responder':responder_public}
        if (set(response)!=set(expected)|{'nonce'} or
            any(response.get(k)!=v for k,v in expected.items()) or
            type(response.get('nonce')) is not str or
            re.fullmatch('[0-9a-f]{32}',response['nonce']) is None):
            raise ValueError('unbound responder context')
        send(conn,signed(initiator,'finish',{'invite_digest':expected['invite_digest'],
            'response_digest':hashlib.sha256(canonical(packet)).hexdigest()}))
        final=recv(conn)
        if final!={'status':'authenticated-loopback-only'}:raise ValueError('no peer acknowledgment')
        return response
