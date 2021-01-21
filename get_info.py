import requests
import time
import csv
import numpy as np
from argparse import ArgumentParser
from tqdm import tqdm


def get_likes(list_users, type_content, owner_id, count, token, quiet):
	print(f'Get likes on {type_content}s:')
	base_url = 'https://api.vk.com/method/'
	if type_content == 'post':
		resp = requests.post(base_url + 'wall.get', data={
		   'owner_id': owner_id, 'count': count, 'v': '5.80', 
		   'access_token': token}).json()
		counter_name = 'posts_likes'
	elif type_content == 'photo':
		resp = requests.post(base_url + 'photos.get', data={
		   'owner_id': owner_id, 'album_id': 'profile', 'count': count, 
		   'rev': '1', 'v': '5.80', 'access_token': token}).json()
		counter_name = 'photos_likes'
	
	try:
		resp = resp['response']
	except KeyError as e:
		print(owner_id, ':', resp['error'])
	items = [item['id'] for item in resp['items']]
	if not quiet:
		print(f'{type_content}: {items}')

	for item_id in tqdm(items):
		resp_item = requests.post(base_url + 'likes.getList', data={
					'type': type_content, 'owner_id': owner_id, 'item_id': item_id, 
					'filter': 'likes', 'v': '5.80', 'access_token': token}).json()
		if not quiet:
			print(f'{type_content}_{item_id}: {resp_item}')
		for user in resp_item['response']['items']:
			if user not in list_users:
				list_users[user] = {'posts_likes': 0,
									'photos_likes': 0,
									'gifts': 0}
				list_users[user][counter_name] = 1
			else:
				list_users[user][counter_name] += 1
		time.sleep(1)
	return list_users


def get_gifts(list_users, owner_id, token, quiet):
	print(f'Get gifts:')
	base_url = 'https://api.vk.com/method/'
	resp = requests.post(base_url + 'gifts.get', data={'user_id': owner_id, 'v': '5.80', 'access_token': token}).json()
	if not quiet:
		print(f'Gifts response: {resp}')
	for gift in tqdm(resp['response']['items']):
		user = gift['from_id']
		message = gift['message']
		if len(message) != 0 and user > 0:
			with open('gift_message.txt', 'a') as f:
				new_mes = f'from {user} to {owner_id}: {message}\n'
				f.write(new_mes)
		if user > 0:
			if user not in list_users:
				list_users[user] = {'posts_likes': 0,
									'photos_likes': 0,
									'gifts': 1}
			else:
				list_users[user]['gifts'] += 1
	return list_users


def get_likes_by_user(list_users, type_content, user_id, count, token, quiet):
	print(f'Get likes on {type_content}s by id{user_id}:')
	base_url = 'https://api.vk.com/method/'
	for owner_id in tqdm(list_users):
		if not quiet:
			print(f'{type_content}s by {owner_id}')
		if type_content == 'post':
			resp = requests.post(base_url + 'wall.get', data={
			   'owner_id': owner_id, 'count': count, 'v': '5.80', 
			   'access_token': token}).json()
			counter_name = 'posts_likes_by_user'
		elif type_content == 'photo':
			resp = requests.post(base_url + 'photos.get', data={
			   'owner_id': owner_id, 'album_id': 'profile', 'count': count, 
			   'rev': '1', 'v': '5.80', 'access_token': token}).json()
			counter_name = 'photos_likes_by_user'
		list_users[owner_id][counter_name] = 0
		try:
			resp = resp['response']
		except KeyError as e:
			if not quiet:
				print(owner_id, ':', resp['error'])
			continue
	
		items = [item['id'] for item in resp['items']]
		if not quiet:
			print(f'{type_content} of {owner_id}: {items}')

		for item_id in items:
			resp_item = requests.post(base_url + 'likes.isLiked', data={
				'user_id': user_id, 'type': type_content, 'owner_id': owner_id,
				'item_id': item_id, 'v': '5.80', 'access_token': token}).json()
			if not quiet:
				print(f'likes_by_user {owner_id}: {resp_item}')
			if resp_item['response']['liked']:
				list_users[owner_id][counter_name] += 1
			time.sleep(1)
		#time.sleep(1)
	return list_users


def get_gifts_by_user(list_users, user_id, token, quiet):
	print(f'Get gifts by id{user_id}:')
	base_url = 'https://api.vk.com/method/'
	for owner_id in tqdm(list_users):
		list_users[owner_id]['gifts_by_user'] = 0
		resp = requests.post(base_url + 'gifts.get', data={
			   'user_id': owner_id, 'v': '5.80', 'access_token': token}).json()
		try:
			resp = resp['response']
		except KeyError as e:
			if not quiet:
				print(owner_id, ':', resp['error'])
			continue
			
		if not quiet:
			print(f'Gifts response: {resp}')
		for gift in resp['items']:
			id_from = gift['from_id']
			message = gift['message']
			if len(message) != 0 and id_from > 0:
				with open('gift_message.txt', 'a') as f:
					new_mes = f'from {id_from} to {owner_id}: {message}\n'
					f.write(new_mes)
			if id_from == user_id:
				list_users[owner_id]['gifts_by_user'] += 1
		time.sleep(1)
	return list_users


def get_users_info(list_users, token, quiet):
	base_url = 'https://api.vk.com/method/'
	resp = requests.post(base_url + 'users.get', data={'user_ids': ','.join([str(i) for i in list_users.keys()]), 'fields': 'sex,common_count,friend_status,relation', 'v': '5.89', 'access_token': token}).json()
	if not quiet:
		print(f'Users response: {resp}')
	for user in resp['response']:
		user_id = user['id']
		list_users[user_id]['name'] = ' '.join([user['first_name'], user['last_name']])
		if 'is_closed' in user:
			list_users[user_id]['is_closed'] = user['is_closed']
		else:
			list_users[user_id]['is_closed'] = 1
		if 'sex' in user:
			list_users[user_id]['sex'] = user['sex']
		else:
			list_users[user_id]['sex'] = 0
		if 'friend_status' in user:
			list_users[user_id]['friend_status'] = user['friend_status']
		else:
			list_users[user_id]['friend_status'] = 0
		if 'common_count' in user:
			list_users[user_id]['common_count'] = user['common_count']
		else:
			list_users[user_id]['common_count'] = 0
		if 'relation' in user:
			list_users[user_id]['relation'] = user['relation']
		else:
			list_users[user_id]['relation'] = 0
	return list_users

	
def to_csv(list_users, user_id):
	file_name = 'info_id' + str(user_id) + '.csv'
	with open(file_name, 'w') as f:
		fieldnames = ['id', 'name', 'sex', 'is_closed', 'posts_likes', 'photos_likes', 'gifts', 'posts_likes_by_user', 'photos_likes_by_user', 'gifts_by_user', 'friend_status', 'common_count', 'relation']
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		for user, item in list_users.items():
			item['id'] = user
			writer.writerow(item)		


def parse_args():
	parser = ArgumentParser()
	parser.add_argument('--id',
						default=48245655,
						help='user id you want to get information')
	parser.add_argument('--count', '-c',
						default='5',
						help='number of photos/posts to be examined')
	parser.add_argument('--quiet', '-q',
						help='do not display the text on command line',
						action='store_true')
	return parser.parse_args()		



if __name__ == '__main__':
	token = # insert your token here

	args = parse_args()
	my_id = args.id
	count = args.count
	quiet = args.quiet
	
	related_users = {}
	# get users and number of likes on posts of the user:
	related_users = get_likes(list_users=related_users, 
							  type_content='post', 
							  owner_id=my_id, 
							  count=count, 
							  token=token, 
							  quiet=quiet)
	# get users and number of likes on photos of the user:
	related_users = get_likes(list_users=related_users, 
							  type_content='photo', 
							  owner_id=my_id, 
							  count=count, 
							  token=token, 
							  quiet=quiet)
	# get users and number of gifts to the user:
	related_users = get_gifts(list_users=related_users, 
							  owner_id=my_id, 
							  token=token, 
							  quiet=quiet)

	# get number of likes on posts of each user:
	related_users = get_likes_by_user(list_users=related_users, 
									  type_content='post',
									  user_id=my_id, 
									  count=count, 
									  token=token, 
									  quiet=quiet)
	# get number of likes on photos of each user:
	related_users = get_likes_by_user(list_users=related_users, 
									  type_content='photo',
									  user_id=my_id, 
									  count=count, 
									  token=token, 
									  quiet=quiet)
	# get number of gifts to each user:
	related_users = get_gifts_by_user(list_users=related_users, 
									  user_id=my_id,
									  token=token, 
									  quiet=quiet)	
									  
	related_users = get_users_info(list_users=related_users, 
								   token=token, 
								   quiet=quiet)
	if not quiet:
		print(f'\nRelated: {related_users}\n')
	
	to_csv(related_users, my_id)
	
	

