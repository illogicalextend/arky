from arky import wallet
wallet.api.use("ark")

w = wallet.open("arky.awt")
w.sendArkMultisign(
	1,
	'AR1LhtKphHSAPdef8vksHWaXYFxLPjDQNU',
	keysgroup=[
		'0326f7374132b18b31b3b9e99769e323ce1a4ac5c26a43111472614bcf6c65a377',
		'03a02b9d5fdd1307c2ee4652ba54d492d1fd11a7d1bb3f3a44c4a05e79f19de933'
	],
	vendorField="arky multi signature test !"
)

import os
os.system("pause")
wallet.mgmt.stop()