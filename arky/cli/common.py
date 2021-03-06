# -*- encoding: utf8 -*-
# © Toons

from ecdsa.keys import SigningKey
from .. import __PY3__, ROOT, ArkyDict, api, core, cfg, util

import io, os, sys, json, getpass, logging, binascii

input = raw_input if not __PY3__ else input

COLDTXS = os.path.normpath(os.path.join(ROOT, ".coldtx"))
try: os.makedirs(COLDTXS)
except: pass

TOKENS = os.path.normpath(os.path.join(ROOT, ".token"))
try: os.makedirs(TOKENS)
except: pass

def checkFolderExists(filename):
	folder = os.path.dirname(filename)
	if not os.path.exists(folder):
		os.makedirs(folder)

def askSecondSignature(address):
	secondPublicKey = api.Account.getAccount(address, returnKey="account").get('secondPublicKey', None)
	if secondPublicKey:
		keys = core.getKeys(getpass.getpass("Enter second passphrase: ").encode("ascii"))
		spk = hexlify(keys.public)
		if spk == secondPublicKey:
			return keys.signingKey
		else:	
			sys.stdout.write("Incorrect second passphrase !\n")
			return False
	return None

def shortAddress(addr, sep="...", n=5):
	return addr[:n]+sep+addr[-n:]

def hexlify(data):
	result = binascii.hexlify(data)
	return result.decode() if isinstance(result, bytes) else result

def unhexlify(data):
	result = binascii.unhexlify(data)
	return result if isinstance(result, bytes) else result.encode()

def signingKey2Hex(signingKey):
	return hexlify(signingKey.to_pem())

def hex2SigningKey(hexa):
	return SigningKey.from_pem(unhexlify(hexa))

def prettyfy(dic, tab="    "):
	result = ""
	if len(dic):
		maxlen = max([len(e) for e in dic.keys()])
		for k,v in dic.items():
			if isinstance(v, dict):
				result += tab + "%s:" % k.ljust(maxlen)
				result += prettyfy(v, tab*2)
			else:
				result += tab + "%s: %s" % (k.rjust(maxlen),v)
			result += "\n"
		return result

def prettyPrint(dic, tab="    ", log=False):
	pretty = prettyfy(dic, tab)
	if len(dic):
		sys.stdout.write(pretty)
		if log: logging.info("\n"+pretty.rstrip())
	else:
		sys.stdout.write("Nothing to print here\n")
		if log: logging.info("Nothing to log here")

def floatAmount(amount, address):
	if amount.endswith("%"):
		return (float(amount[:-1])/100 * float(api.Account.getBalance(address, returnKey="balance")) - cfg.__FEES__["send"])/100000000.
	elif amount[0] in "$€£¥":
		price = util.getArkPrice({"$":"usd", "€":"eur", "£":"gbp", "¥":"cny"}[amount[0]])
		result = float(amount[1:])/price
		if askYesOrNo("%s=A%f (A/%s=%f) - Validate ?" % (amount, result, amount[0], price)):
			return result
		else:
			return False
		return result
	else:
		return float(amount)

def findNetworks():
	try:
		return [os.path.splitext(name)[0] for name in os.listdir(ROOT) if name.endswith(".net")]
	except:
		return []

def findTokens(ext="tok"):
	try:
		return [os.path.splitext(name)[0] for name in os.listdir(os.path.join(TOKENS, cfg.__NET__)) if name.endswith("."+ext)]
	except:
		return []

def findColdTx(ext="ctx"):
	try:
		return [os.path.splitext(name)[0] for name in os.listdir(os.path.join(COLDTXS, cfg.__NET__)) if name.endswith("."+ext)]
	except:
		return []

def chooseItem(msg, *elem):
	n = len(elem)
	if n > 1:
		sys.stdout.write(msg + "\n")
		for i in range(n):
			sys.stdout.write("    %d - %s\n" % (i+1, elem[i]))
		i = 0
		while i < 1 or i > n:
			i = input("Choose an item: [1-%d]> " % n)
			try: i = int(i)
			except: i = 0
		return elem[i-1]
	elif n == 1:
		return elem[0]
	else:
		sys.stdout.write("Nothing to choose...\n")
		return False

def askYesOrNo(msg):
	answer = ""
	while answer not in ["y", "Y", "n", "N"]:
		answer = input("%s [y-n]> " % msg)
	return False if answer in ["n", "N"] else True

def coldTxPath(name):
	name = name.decode() if isinstance(name, bytes) else name
	if not name.endswith(".ctx"): name += ".ctx"
	return os.path.join(COLDTXS, cfg.__NET__, name)

def generateColdTx(signingKey, publicKey, secondSigningKey=None, **kw):
	tx = core.Transaction(**kw)
	object.__setattr__(tx, "key_one", ArkyDict(public=publicKey, signingKey=signingKey))
	if secondSigningKey:
		object.__setattr__(tx, "key_two", ArkyDict(signingKey=secondSigningKey))
	tx.sign()
	return tx.serialize()

def dropColdTx(tx, name=None):
	filename = coldTxPath(tx.id if name == None else name)
	checkFolderExists(filename)
	out = io.open(filename, "w" if __PY3__ else "wb")
	json.dump(tx, out, indent=2)
	out.close()
	return os.path.basename(filename)

def loadColdTx(name):
	filename = coldTxPath(name)
	if os.path.exists(filename):
		in_ = io.open(filename, "r" if __PY3__ else "rb")
		tx = json.load(in_)
		in_.close()
		return tx

def reprColdTx(ctx):
	return "<type-%(type)d transaction(A%(amount).8f) from %(from)s to %(to)s>" % {
		"type": ctx["type"],
		"amount": ctx["amount"]/100000000.,
		"from": shortAddress(ctx["address"]),
		"to": shortAddress(ctx["recipientId"])
	}

def tokenPath(name, token="tok"):
	ext = "."+token
	name = name.decode() if isinstance(name, bytes) else name
	if not name.endswith(ext): name += ext
	return os.path.join(TOKENS, cfg.__NET__, name)

def dropToken(filename, address, publicKey, signingKey):
	checkFolderExists(filename)
	out = io.open(filename, "w")
	out.write("%s%s%s" % (address, hexlify(publicKey), signingKey2Hex(signingKey)))
	out.close()

def loadToken(filename):
	in_ = io.open(filename, "r")
	data = in_.read()
	in_.close()
	return (data[:34], unhexlify(data[34:34+66]), hex2SigningKey(data[34+66:]))
