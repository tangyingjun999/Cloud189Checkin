from requests import get, post
import hashlib, time, uuid, random, os
from notify import send, pushplus_bot, push_config, wecom_app

# cron 30 7 * * *
# 只需要抓 X-SESSION-ID 即可,多账号#分割
# 青龙环境变量名 tdra_py = "X-SESSION-ID#X-SESSION-ID"


# 不是,或者不想用变量名,也可以把ck填在下面
user_list = ''
# 推送开关
isnotify = 1

##############  下面是代码  ################

msg_list = []


def format_msg():
	str1 = ''
	for item in msg_list:
		str1 += str(item) + "\r\n"
	return str1


def SignNature(url):
	api = url.split('api')[1].split('?')[0]
	timestamp = str(int(time.time() * 1000))
	requestid = str(uuid.uuid1())
	b = f'/api{api}&&{sessionid}&&{requestid}&&{timestamp}&&FR*r!isE5W&&48'
	b = hashlib.sha256(b.encode()).hexdigest()
	header = {'X-TIMESTAMP': timestamp, 'X-SESSION-ID': sessionid, 'X-SIGNATURE': b, 'X-TENANT-ID': '48',
	          'X-REQUEST-ID': requestid}
	tdra_headers.update(header)


def getauth():
	url = f'https://vapp.tmuyun.com/api/user_mumber/account_detail?osTypeCode=2'
	SignNature(url)
	resp = get(url, headers=tdra_headers).json()
	global account_id, phone
	phone = resp['data']['rst']['mobile']
	account_id = resp['data']['rst']['id']
	tdra_headers['X-ACCOUNT-ID'] = account_id
	msg = f'【{phone}】'
	print(msg)
	msg_list.append(msg)

	url = 'https://crm.rabtv.cn/v2/user/oauth'
	data = {"mobile": "18662778525"}
	resp = post(url, json=data).json()
	access_token = resp['data']['access_token']
	# print(access_token)
	tdra_headers['Authorization'] = 'Bearer ' + access_token


# 共富签——签到
def sign_In():
	getauth()
	url = f'https://crm.rabtv.cn/v2/index/signIn'
	resp = post(url, headers=tdra_headers).json()
	print(resp)
	msg_list.append(resp['msg'])

	# 获取签到奖励完成情况
	url = f'https://crm.rabtv.cn/v2/user/mineContinueSignCurrentMonth'
	resp = post(url, headers=tdra_headers).json()
	# status: 1是未完成,2是完成未领取,3是已领取
	for i in resp['data']:
		status = i['status']
		id = i['id']
		text = i['text']
		if status == 2:
			# 领取奖励
			print(f'正在领取  {text}  奖励')
			url = f'https://crm.rabtv.cn/v2/user/getPrizeV'
			#SignNature(url)
			data = f'id={id}'
			resp = post(url, data=data,headers=tdra_headers).json()
			print(resp)
		elif status == 1:
			print(f'{text}  还未完成')
		elif status == 3:
			print(f'{text}  已经领取')


# 获取任务完成情况
def task_list():
	timetemp = str(int(time.time() * 1000))
	sign = hashlib.md5(timetemp.encode()).hexdigest()
	url = f'https://crm.rabtv.cn/read/task/index?sign={sign}'
	resp = get(url, headers=tdra_headers).json()
	# print(resp)
	for data in resp['data']:
		name = data['name']
		done = data['allCheck']
		msg = f'{name}  {done}'
		print(msg)
		msg_list.append(msg)
		if done == False:
			for data_1 in data['data']:
				task_id = data_1['id']
				task_done(task_id)

# 共富签 完成任务
def task_done(id):
	url = f'https://crm.rabtv.cn/read/task/add'
	data = f'account_id={account_id}&task_child_id={id}'
	resp = post(url, data=data, headers=tdra_headers).json()
	print(resp)
	msg_list.append(resp['msg'])


# 阅读大奖,还有当前阅读积分
def curr_gift():
	timetemp = str(int(time.time() * 1000))
	sign = hashlib.md5(timetemp.encode()).hexdigest()
	url = f'https://crm.rabtv.cn/read/gift/current?sign={sign}'
	resp = get(url, headers=tdra_headers).json()
	msg = f'当月阅读积分礼品为:'
	print(msg)
	msg_list.append(msg)
	for i in resp['data']:
		title = i['title']
		open_v = i['open_v']
		msg = f'{title}    所需{open_v}阅读积分'
		print(msg)
		msg_list.append(msg)

	print('=' * 20)
	msg = f'{phone} 当前阅读积分: {resp["user"]["total_read_v"]}\n{"=" * 20}'
	print(msg)
	msg_list.append(msg)


# 日常任务
def task_day():
	url = f'https://vapp.tmuyun.com/api/user_mumber/numberCenter?is_new=1'
	SignNature(url)
	resp = get(url,headers=tdra_headers).json()
	# 这是日常签到任务
	daily_sign_info = resp['data']['daily_sign_info']
	name = daily_sign_info['name']
	reward_acquisition  = daily_sign_info['reward_acquisition']
	print(daily_sign_info)
	if reward_acquisition != 999 :
		print(f'开始 {name}')
		msg_list.append(f'开始 {name}')
		url = 'https://vapp.tmuyun.com/api/user_mumber/sign'
		SignNature(url)
		sign_resp = get(url,headers=tdra_headers).json()
		if sign_resp['message'] == 'success':
			signExperience = sign_resp['data']['signExperience']
			signIntegral = sign_resp['data']['signIntegral']
			print(f'{name}: 获得经验{signExperience}, 积分:{signIntegral}')
			msg_list.append(f'{name}: 获得经验{signExperience}, 积分:{signIntegral}')

	# 这是日常任务积分
	url = f'https://vapp.tmuyun.com/api/user_center/task?type=1&current=1&size=20'
	SignNature(url)
	resp = get(url,headers=tdra_headers).json()
	
	user_task_list = resp['data']['list']
	for task in user_task_list :
		name = task['name']
		completed = task['completed']
		member_type = task['member_task_type']
		if name == '新闻资讯阅读' and completed == 0 :
			read_news()
		elif name == '使用本地服务' and completed == 0 :
			print(f'开始任务: {name}')
			msg_list.append(f'开始任务: {name}')
			url = f'https://vapp.tmuyun.com/api/user_mumber/doTask'
			SignNature(url)
			data = f'member_type={member_type}'
			resp = post(url, data=data, headers=tdra_headers).json()
			print(resp['message'])
			msg_list.append(resp['message'])


# 阅读新闻任务/点赞/分享
def read_news():
	url = f'https://vapp.tmuyun.com/api/article/channel_list_by_code?channel_code=shizheng&channel_id=61a4d4d7fe3fc1616c96b38c&isDiFangHao=false&is_new=true&list_count=0&size=20'
	SignNature(url)
	resp = get(url, headers=tdra_headers).json()
	article_list = resp['data']['article_list']
	for article in article_list[:5]:
		article_id = article['id']
		article_name = article['list_title']
		print(f'开始阅读 {article_name}')
		msg_list.append(f'开始阅读 {article_name}')
		url = f'https://vapp.tmuyun.com/api/article/read_time?channel_article_id={article_id}&read_time={random.randint(1000, 2000)}'
		SignNature(url)
		resp = get(url, headers=tdra_headers).json()
		print(resp['message'])
		msg_list.append(resp['message'])

		print(f'开始点赞')
		msg_list.append(f'开始点赞')
		url = f'https://vapp.tmuyun.com/api/favorite/like'
		SignNature(url)
		data = f'action=1&id={article_id}'
		resp = post(url, data=data,headers=tdra_headers).json()
		print(resp['message'])
		msg_list.append(resp['message'])

		time.sleep(1)
		print(f'开始分享')
		msg_list.append(f'开始分享')
		url = f'https://vapp.tmuyun.com/api/user_mumber/doTask'
		SignNature(url)
		data = f'memberType=3&member_type=3&target_id={article_id}'
		resp = post(url, data=data,headers=tdra_headers).json()
		print(resp['message'])
		msg_list.append(resp['message'])

if __name__ == '__main__':
	# 用户名检测
	if user_list == '':
		try:
			user_list = os.environ['tdra_py2']
		except:
			print(f'没检测到CK,停止运行')
			exit()
	tdra_headers = {'Content-Type': 'application/x-www-form-urlencoded',
	                'User-Agent': '1.2.1;BA3719C4-17BE-4257-BACE-522E1CC2BC7C;iPhone11,2;IOS;13.4.1;Appstore'}
	for sessionid in user_list.split('#'):
		# getauth()
		task_day()
		sign_In()
		task_list()
		task_day()
		curr_gift()

	# 企业微信推送
	if isnotify == 1:
		content = format_msg()
		wecom_app('天地瑞安共富签', content)
