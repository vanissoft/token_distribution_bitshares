#
# (c) 2017 elias/vanissoft
#
#
#


from browser import window, document, ajax, alert
import wglobals
import json

Callbacks = {}
Asset_data = None
AssetHold_data = None

Status_list = []
Msg_list = []
Msg_sel = 0
Cnt = 0




def gotasset(rtn):
	global Asset_data
	print("gotasset", rtn)
	Asset_data = rtn['data']
	document['lidasset'].innerHTML = rtn['data']['td_msg']
	if AssetHold_data is not None:
		document['btnsnapshot'].disabled = False
	document['lblsnapshot_holders'].innerHTML = " ?"
	document['lblsnapshot_balance'].innerHTML = " ?"


def gotassethold(rtn):
	global AssetHold_data
	AssetHold_data = rtn['data']
	if Asset_data is not None:
		document['btnsnapshot'].disabled = False
	document['lidassethold'].innerHTML = rtn['data']['td_msg']
	document['lblsnapshot_status'].innerHTML = "Ready"
	document['btnsnapshot'].disabled = False



def query(url, callback):
	global Cnt
	url = url+"&nonce="+str(Cnt)
	Callbacks[url] = callback
	req = ajax.ajax()
	req.open('GET', url, True)
	req.send()
	req.bind('complete', ajax_end)
	Cnt += 1

def ajax_end(request):
	global Cnt
	try:
		rtn = json.loads(request.responseText)
	except Exception as err:
		print(err.__repr__())
		return
	if rtn is None:
		print("error\n"+request.responseText)
		return
	print(rtn['request'])
	if rtn['request'] in Callbacks:
		print("callback ok")
		Callbacks[rtn['request']](rtn)
		del Callbacks[rtn['request']]

def post(url, data, callback):
	Callbacks[url] = callback
	req = ajax.ajax()
	req.open('POST', url, True)
	req.send(json.dumps(data))
	req.bind('complete', ajax_end)


def launch_requested(rtn):
	global Msg_sel
	document['table-container'].clear()
	Msg_sel = 1

def snapshot_requested(rtn):
	global Msg_sel
	document['table-container'].clear()
	Msg_sel = 0


def launch_distribution(dummy):
	dat = {'form': {}}
	dat['form']['key'] = document['fkey'].value
	dat['form']['message'] = document['fmessage'].value
	post("/post/launch?key=null", dat, launch_requested)


def launch_snapshot(dummy):
	document['lblsnapshot_holders'].innerHTML = " ?"
	document['lblsnapshot_balance'].innerHTML = " ?"
	document['lblsnapshot_status'].innerHTML = " ?"
	document['dcsv'].innerHTML = ''
	dat = {'form': {}}
	dat['form']['assethold_id'] = AssetHold_data['id']
	dat['form']['asset_id'] = Asset_data['id']
	dat['form']['amount'] = document['famount'].value
	dat['form']['ratio'] = document['fratio'].value
	dat['form']['hold_minimum'] = document['fholdminimum'].value
	dat['form']['minimum'] = document['fminimum'].value
	dat['form']['transfer_fee'] = document['ftransferfee'].value
	post("/post/snapshot?key=null", dat, snapshot_requested)


def table_summary(dat):
	from browser.html import TABLE, TR, TH, TD
	from browser import html
	tbl = TABLE()
	row = TR()
	for h in dat[0].split(";"):
		row <= TH(h)
	tbl <= row
	for r in dat[1].split("#"):
		row = TR()
		for f in r.split(";"):
			row <= TD(f)
		tbl <= row
	document['table-container'].clear()
	document['table-container'] <= html.H5("Summary of first 10 accounts")
	document['table-container'] <= tbl


def broker(op):
	if op[0] == "snapshot_start":
		document['lblsnapshot_status'].innerHTML = "<strong> {}</strong>".format("Calculating")
		document['lblsnapshot_holders'].innerHTML = " ?"
		document['lblsnapshot_balance'].innerHTML = " ?"
	elif op[0] == "snapshot_end":
		document['lblsnapshot_holders'].innerHTML = "<strong> {}</strong>".format(op[3])
		document['lblsnapshot_balance'].innerHTML = "<strong> {}</strong>".format(op[2])
		document['lblsnapshot_costs'].innerHTML = "<strong> {}</strong>".format(op[4])
		document['lblsnapshot_status'].innerHTML = "<strong> {}</strong>".format("OK")
		document['btnsnapshot'].disabled = False
		document['btnlaunch'].disabled = False
	elif op[0] == "csv_exported":
		document['dcsv'].innerHTML = '<a href="{}">{}</a>'.format(op[2], "Top holders CSV")
	elif op[0] == "csv_data":
		table_summary(op[2:])
	elif op[0] == "launch_error":
		alert(op[1])


def status_act():
	global Msg_list, Status_list, Msg_sel
	while True:
		if len(Msg_list) == 0:
			print("No data.", end='')
			break
		print("status data")
		msg = Msg_list.pop(0)
		if msg[0] == "*":  # action message
			print("status data", msg)
			broker(msg.split("|")[1:])
		else:
			Status_list.append(msg)
		st = ''
		for lin in Status_list[::-1]:
			st += lin +"<br>"
		Status_list = Status_list[-10:]
		if Msg_sel == 0:
			document['message-area1'].innerHTML = st
		elif Msg_sel == 1:
			document['message-area2'].innerHTML = st
		print("status_act")

def gotmessage(rtn):
	global Msg_list
	if rtn['data'] == None:
		print("no message.", end='')
		return
	Msg_list.extend(rtn['data'])
	print(Msg_list)
	status_act()


def messages_refresh():
	query("/get/getmessage?key=null", gotmessage)


def famount_chg(ev):
	if float(ev.target.value) > 0:
		document['fratio'].value = 0
		document['fratio'].disabled = True
	else:
		document['fratio'].disabled = False

def fratio_chg(ev):
	if float(ev.target.value) > 0:
		document['famount'].value = 0
		document['famount'].disabled = True
	else:
		document['famount'].disabled = False

def faccount_chg(ev):
	if ev.target.value.strip() == '':
		return
	query("/get/getaccount?account=" + ev.target.value, gotaccount)

def fasset_chg(ev):
	if ev.target.value.strip() == '':
		return
	query("/get/getasset?asset=" + ev.target.value, gotasset)

def fassethold_chg(ev):
	if ev.target.value.strip() == '':
		return
	query("/get/getasset?asset=" + ev.target.value, gotassethold)







#table_summary(["HEAD1;head2;head3","sadf;fgdfg;erwer#a234;32432;32434"])

document['fasset'].value = ''
document['fasset'].bind('change', fasset_chg)

document['fassethold'].value = ''
document['fassethold'].bind('change', fassethold_chg)

document['fkey'].value = ''
document['famount'].value = 0
document['famount'].bind('change', famount_chg)

document['fratio'].value = 0
document['fratio'].bind('change', fratio_chg)

document['fholdminimum'].value = 0
document['fminimum'].value = 0
document['ftransferfee'].value = 0.04

document['lidasset'].innerHTML = 'id: ???'
document['lidassethold'].innerHTML = 'id: ???'

document['lblsnapshot_holders'].innerHTML = " ?"
document['lblsnapshot_balance'].innerHTML = " ?"
document['lblsnapshot_status'].innerHTML = " ?"
document['dcsv'].innerHTML = ''

document['btnlaunch'].disabled = True
document['btnsnapshot'].disabled = True

document['btnlaunch'].bind('click', launch_distribution)
document['btnsnapshot'].bind('click', launch_snapshot)

wglobals.set_timer(0, messages_refresh, 2)


