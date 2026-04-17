import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# RFC 3526 2048-bit MODP Group 14. Using a fixed, well-known group means both
# peers agree on p and g without transmitting them.
_P_HEX = (
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
    "15728E5A8AACAA68FFFFFFFFFFFFFFFF"
)
_G = 2
_PARAMETERS = dh.DHParameterNumbers(int(_P_HEX, 16), _G).parameters()
_HKDF_INFO = b"cmp2204-p2p-chat/v1"


def generate_keypair():
    private_key = _PARAMETERS.generate_private_key()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key, public_pem


def derive_fernet_key(private_key, peer_public_pem):
    peer_public = serialization.load_pem_public_key(peer_public_pem)
    shared_secret = private_key.exchange(peer_public)
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_HKDF_INFO,
    ).derive(shared_secret)
    return base64.urlsafe_b64encode(derived)


def public_key_to_wire(public_pem):
    return base64.b64encode(public_pem).decode("ascii")


def public_key_from_wire(wire):
    return base64.b64decode(wire.encode("ascii"))
