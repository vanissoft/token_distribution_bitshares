#
# (c) 2017 elias/vanissoft
#
#




import subprocess
import time
import socket


from asyncio import sleep
from sanic import Sanic
from sanic_compress import Compress
from sanic.response import json as response_json, text as response_text, html as response_html, file as response_file
from sanic.exceptions import ServerError

import redis
from rq import Queue

from render import Render
import mreq
import pickle
import snapshot
import distribution

Procs = []
Develop = False


# ----------- CONSTANTS
from config import *

app = Sanic()
app.config['COMPRESS_MIMETYPES'] = ('text/x-python', 'application/javascript', 'text/css', 'text/html', 'text/plain')
Compress(app)

@app.middleware('request')
async def req1(req):
	print("req1", req.url)
	if '/get/' in req.path or '/do/' in req.path or '/post/' in req.path:
		return
	ext = req.path.split('.')[-1]
	if ext in ('mp3', 'js', 'jpg', 'css', 'ttf', 'png', 'woff', 'woff2', 'ico', 'gif', 'map', 'mem', 'pck', 'mp4', 'csv'):
		pfil = './web' + req.path
		return await response_file(location=pfil, headers={"cache-control": "public,max-age=216000"})
	elif ext in 'html':
		pfil = './web' + req.path
		tmp = Render(pfil)
		rtn = await tmp.parse()
		return response_html(body=rtn, headers={"cache-control": "public,max-age=216000"})
	elif ext in 'py':
		pfil = '.' + req.path
		# /w*.py y /vs_widgets will be served not server side .py
		if (req.path[:2] == '/w' or "/vs_widgets" in req.path) and ".." not in req.path:
			return await response_file(pfil, headers={"cache-control": "public,max-age=216000"})
		else:
			return response_text("error")
	else:
		return response_text("error")

@app.route('/<tag>')
async def route1(req, tag):
	return response_text(tag)


@app.route('/get/<tag>', methods=['GET'])
async def getinfo(req, tag):
	global Q_normal
	if Develop:
		rtn = mreq.getinfo(req.args, tag, req.path, req.query_string)
	else:
		job = Q_normal.enqueue_call(func=mreq.getinfo, args=[req.args, tag, req.path, req.query_string], timeout=20)
		while True:
			await sleep(.01)
			if job.result is not None:
				rtn = job.result
				break
	return response_json(rtn)


@app.route('/post/<tag>', methods=['POST'])
async def postinfo(req, tag):
	if Develop:
		rtn = mreq.postinfo(req.args, tag, req.path, req.query_string, req.json)
	else:
		job = Q_normal.enqueue_call(func=mreq.postinfo, args=(req.args, tag, req.path, req.query_string, req.json), timeout=20)
		while True:
			await sleep(.01)
			if job.result is not None:
				rtn = job.result
				break
	return response_text(rtn)




def dummy(param):
	print(param)



async def broker():
	global Q_bg
	while True:
		while True:
			rtn = Redisdb.lpop("operations")
			if rtn is None:
				break
			op = pickle.loads(rtn)
			if op['operation'] == 'launch_distribution':
				distribution.enqueue(op, Q_bg)
			elif op['operation'] == 'distribution_batch':
				distribution.batch_enqueue(op, Q_bg)
			elif op['operation'] == 'distribution_check':
				distribution.endcheck_enqueue(Q_bg)
			elif op['operation'] == 'launch_snapshot':
				snapshot.enqueue(op, Q_bg)
			elif op['operation'] == 'snapshot_batch':
				snapshot.batch_enqueue(op, Q_bg)
			elif op['operation'] == 'snapshot_end':
				snapshot.snapshot_end_enqueue(Q_bg)
			elif op['operation'] == 'db_save':
				Redisdb.bgsave()
			elif op['operation'] == 'csv_generation':
				snapshot.csvgen_enqueue(Q_bg)

		await sleep(0.5)





if __name__ == '__main__':
	Develop = ('Z68X' in socket.getfqdn()) and True
	proc1 = subprocess.Popen("redis-server --port "+str(REDIS_PORT), shell=True)
	time.sleep(2)
	Redisdb = redis.StrictRedis(host='127.0.0.1', port=REDIS_PORT, db=1)

	# cleanup
	Redisdb.delete('messages')
	Redisdb.delete('operations')
	Redisdb.delete("batch_jobs")

	Q_normal = Queue('web', connection=redis.Redis(host='127.0.0.1', port=REDIS_PORT))
	Q_normal.empty()
	Q_bg = Queue('background', connection=redis.Redis(host='127.0.0.1', port=REDIS_PORT))
	#Q_bg.empty()


	proc3 = []
	for pr in range(0, 4):
		proc3.append(subprocess.Popen("./rq_td_worker2.py web --url redis://127.0.0.1:"+str(REDIS_PORT), shell=True))
	for pr in range(0, 4):
		proc3.append(subprocess.Popen("./rq_td_worker2.py background --url redis://127.0.0.1:"+str(REDIS_PORT), shell=True))
	time.sleep(0.2)

	app.add_task(broker())

	app.run(host="0.0.0.0", port=PORT, workers=1)

	proc1.kill()
	time.sleep(1)
	for p in proc3:
		p.kill()
	time.sleep(1)
