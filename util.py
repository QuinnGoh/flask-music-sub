import json

import boto3
import requests  # request img from web
from boto3.dynamodb.conditions import Key, Attr
from botocore.args import logger
from botocore.exceptions import ClientError

from models import Song, User


#
def create_user_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('User')

    try:
        table.table_status in ("CREATING", "UPDATING", "DELETING", "ACTIVE")
    except ClientError:
        table = dynamodb.create_table(TableName='User',
                                      KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
                                      AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
                                      ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
        return table


#
def create_music_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Music')

    try:
        table.table_status in ("CREATING", "UPDATING", "DELETING", "ACTIVE")
    except ClientError:

        table = dynamodb.create_table(TableName='Music',
                                      KeySchema=[{'AttributeName': 'title', 'KeyType': 'HASH'  # Partition key
                                                  }, {'AttributeName': 'artist', 'KeyType': 'RANGE'  # Sort key
                                                      }
                                                 ],
                                      AttributeDefinitions=[{'AttributeName': 'title', 'AttributeType': 'S'},
                                                            {'AttributeName': 'artist', 'AttributeType': 'S'}],
                                      ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
        return table


def check_table_seeded(table, dynamodb=None) -> bool:
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table(table)

    response = table.scan()

    count = response['Count']

    if count > 1:
        return True
    else:
        return False


#
def seed_music_table():
    if not check_table_seeded('Music'):
        with open('a2.json') as data_file:
            data = json.load(data_file)

        for song in data['songs']:
            upload_file(song['img_url'], song['title'] + "_album_image", "music-images-22042022")
            put_song(song['title'], song['artist'], song['web_url'], song['img_url'], song['year'])


#
def seed_user_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('User')

    for i in range(10):
        response = table.put_item(
            Item={'email': 's3724287' + str(i) + '@student.rmit.edu.au', 'user_name': 'Quinn Goh' + str(i),
                  'password': str(i) + '12345'})
        return response


#
def put_song(title, artist, web_url, img_url, year, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('Music')
    response = table.put_item(
        Item={'artist': artist, 'title': title, 'web_url': web_url, 'img_url': img_url, 'year': year})
    return response


#
def check_exist_email(email, dynamodb=None) -> bool:
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('User')

    try:
        response = table.query(
            KeyConditionExpression=Key('email').eq(email)
        )
        count = response['Count']

    except ClientError as e:
        print(e.response['Error']['Message'])

    if count >= 1:
        return True
    else:
        return False


#
def get_user_id(email, user_name, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('User')

    try:
        response = table.get_item(Key={'email': email})
        return response['Item']['user_id']

    except ClientError as e:
        print(e.response['Error']['Message'])


#
def retrieve_user_table(user_id, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table(user_id)

    song_objects = []

    response = table.scan()
    songs = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        songs.extend(response['Items'])

    for song in songs:
        url_title = song['title'].replace(" ", "+")
        img_url = 'https://music-images-22042022.s3.amazonaws.com/' + url_title + '_album_image'
        song_objects.append(Song(song['title'], song['artist'], song['year'], img_url, img_url))

    return song_objects


#
def create_user_music_table(user_id, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(TableName=user_id,
                                  KeySchema=[{'AttributeName': 'title', 'KeyType': 'HASH'  # Partition key
                                              }],
                                  AttributeDefinitions=[{'AttributeName': 'title'
                                                            , 'AttributeType': 'S'}],
                                  ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
    return table


#
def add_user_music_table(img_url, year, title, artist, user_id, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table(user_id)

    table.put_item(Item={'artist': artist, 'title': title, 'img_url': img_url, 'year': year, 'user_id': user_id})


#
def remove_user_music_table(title, user_id, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    print(title)

    table = dynamodb.Table(user_id)

    resp = table.delete_item(
        Key={
            'title': title
        }
    )

    print(resp)


#
def query(function, artist, title, year):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Music')

    songs = []
    song_objects = []

    if function == 'a':
        scan_kwargs = {
            'FilterExpression': Key('artist').eq(artist)}

    if function == 't':
        scan_kwargs = {
            'FilterExpression': Key('title').eq(title)}

    if function == 'y':
        scan_kwargs = {
            'FilterExpression': Attr('year').eq(year)}

    if function == 'at':
        scan_kwargs = {
            'FilterExpression': Key('artist').eq(artist) & Key('title').eq(title)}

    if function == 'ay':
        scan_kwargs = {
            'FilterExpression': Key('artist').eq(artist) & Attr('year').eq(year)}

    if function == 'aty':
        scan_kwargs = {
            'FilterExpression': Key('artist').eq(artist) & Key('title').eq(title) & Attr('year').eq(year)}

    try:
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            songs.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None
    except ClientError as err:
        logger.error(
            "Couldn't scan for movies. Here's why: %s: %s",
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise

    for song in songs:
        url_title = song['title'].replace(" ", "+")
        img_url = 'https://music-images-22042022.s3.amazonaws.com/' + url_title + '_album_image'

        song_objects.append(Song(song['title'], song['artist'], song['year'], song['web_url'], img_url))

    return song_objects


#
def put_user(user: User, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('User')
    response = table.put_item(
        Item={'user_name': user.username, 'email': user.email, 'password': user.password,
              'user_id': hash(user.email)})
    return response


#
def check_credentials(email, user_name, password, dynamodb=None) -> bool:
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    if check_exist_email(email):

        table = dynamodb.Table('User')

        try:
            response = table.get_item(Key={'email': email})

            if response['Item']['password'] == password and response['Item']['email'] == email:
                return True
            else:
                return False
        except ClientError as e:
            print(e.response['Error']['Message'])
            return False
        else:
            return False

    else:
        return False


#
def upload_file(url, file_name, bucket_name):
    r = requests.get(url, stream=True)

    session = boto3.Session()
    s3 = session.resource('s3')

    key = file_name

    bucket = s3.Bucket(bucket_name)
    bucket.upload_fileobj(r.raw, key, ExtraArgs={'ACL': 'public-read'})


#
class database(object):
    create_user_table()
    create_music_table()
    seed_music_table()
    #seed_user_table()
