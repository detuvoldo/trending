# -*- coding: utf-8 -*-
# get.py

import time
import math
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

import pandas as pd

from Trend_Computing.trend import Trend_Computing
from Trend_Computing.score import Score
from Trend_Computing.sliding_window import Sliding_window

from crud import *
from Trend_Computing import config

import params

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + \
    config.DATABASE_CONFIG['user'] + ':' + \
    config.DATABASE_CONFIG['password'] + '@' + \
    config.DATABASE_CONFIG['host'] + '/' + \
    config.DATABASE_CONFIG['dbname']
db = SQLAlchemy(app)
ma = Marshmallow(app)

video_schema = VideoSchema()
videos_schema = VideoSchema(many=True)

video_view_time_schema = VideoViewTimeSchema()
videos_view_time_schema = VideoViewTimeSchema(many=True)

trendings_schema = TrendingSchema(many=True)

try:
    db.session.query(Trending).delete()
    db.session.commit()
except:
    db.session.rollback()

def update_trending():
    '''Calculate kl_score periodically'''
    with app.app_context():
        time_t = time.time()
        video_arr = list()
        trend_list = list()

        # if before 10am, different parameters
        rush_hour = False

        total_videos_views = 0
        total_expect_views = 0

        total_videos_likes = 0
        total_expect_likes = 0

        videos_view_list = []
        videos_like_list = []

        today = datetime.fromtimestamp(int(time_t))
    
        daily_time_pivot = time.mktime(datetime(
            today.year, today.month, today.day, params.PARAMS_CONFIG['DAILY_PIVOT']).timetuple())

        # After 10am, use other parameters
        if today.hour >= 10:
            rash_hour = True

        #print(daily_time_pivot)
        if rash_hour:
            expectation_time_pivot = int(
                time_t) - params.PARAMS_CONFIG['DELTA_TIME_RUSHHOUR']

            view_pivot = params.PARAMS_CONFIG['VIEW_PIVOT_RUSHHOUR']
            like_view_rate = params.PARAMS_CONFIG['LIKE_VIEW_RUSHHOUR']

        else:
            expectation_time_pivot = int(
                time_t) - params.PARAMS_CONFIG['DELTA_TIME_NORMALHOUR']

            view_pivot = params.PARAMS_CONFIG['VIEW_PIVOT_NORMALHOUR']
            like_view_rate = params.PARAMS_CONFIG['LIKE_VIEW_NORMALHOUR']

        videos = Video.query.all()
        videos_pandas = videos_schema.dump(videos).data

        video_likes = video_like_schema.dump(VideoLike.query.all()).data

        for item in video_likes:
            event_timestamp_list = [*map(float, item['event_timestamp'].split(','))]
            daily_event_timestamp_list = [
                event_timestamp for event_timestamp in event_timestamp_list if event_timestamp > 1000 * daily_time_pivot]

            expect_event_timestamp_list = [
                event_timestamp for event_timestamp in event_timestamp_list if event_timestamp > 1000 * expectation_time_pivot]

            total_expect_likes += len(expect_event_timestamp_list)
            total_videos_likes += len(daily_event_timestamp_list)

            video_likes_dict = {'videoid': item['videoid'], 'expect_like': len(
                expect_event_timestamp_list), 'prob_like': len(daily_event_timestamp_list)}

            videos_like_list.append(video_likes_dict)

        for item in videos_pandas:
            item_view_time = VideoViewTime.query.filter_by(
                videoid=item['videoid']).first()

            if not item_view_time:
                continue
            else:
                if not item_view_time.view_timestamp:
                    item_view_time = [int(time_t) * 1000]
                else:
                    item_view_time = [*map(float, item_view_time.view_timestamp.split(','))]

            video_arr.append([item['videoid'], float(
                item['video_timestamp']), item_view_time])

        video_df = pd.DataFrame(
            video_arr, columns=['videoid', 'video_timestamp', 'view_timestamp'])

        for videoid in video_df['videoid']:
            temp_video_timestamp = int(
                video_df.loc[video_df['videoid'] == videoid]['video_timestamp'].iloc[0])

            new_video = Trend_Computing(videoid, temp_video_timestamp)

            prob_video_views = new_video._get_views(daily_time_pivot ,video_df)
            expect_video_views = new_video._get_views(expectation_time_pivot, video_df)

            total_videos_views += prob_video_views
            total_expect_views += expect_video_views

            videos_view_dict = {
                'videoid': videoid, 'expect_view': expect_video_views, 'prob_view': prob_video_views, 'duration': new_video._compute_duration()}

            videos_view_list.append(videos_view_dict)

        for video_view in videos_view_list:
            video_score = Score(video_view['videoid'])
            
            for video_like in videos_like_list:
                if video_view['videoid'] == video_like['videoid']:
                    if video_view['prob_view'] < view_pivot:
                        video_score.kl_score = 0.0
                        trend_list.append(video_score._get_score_list())
                    else:
                        video_score.probability = (video_view['prob_view'] + like_view_rate
                                                * video_like['prob_like']) / (total_videos_views + total_videos_likes)

                        if total_expect_views + total_expect_likes == 0:
                            video_score.expectation = 0.0
                        else:
                            video_score.expectation = (video_view['expect_view'] + like_view_rate
                                                * video_like['expect_like']) / (total_expect_views + total_expect_likes)

                        if video_score.expectation == 0:
                            video_score.kl_score = 0.0
                        else:
                            video_score.kl_score = int(1e25 * (video_score.expectation * math.log(
                                video_score.expectation / video_score.probability)) / (video_view['duration'] ** 3))
                        
                        trend_list.append(video_score._get_score_list())

        temp_sliding_window = Sliding_window(trend_list)
        results = temp_sliding_window._sort_list_trending()

        for result in results:
            new_trending_video = Trending(
                result['videoid'], result['kl_score'])
            
            if db.session.query(Trending).filter_by(videoid=result['videoid']).count() < 1:
                db.session.add(new_trending_video)
            else:
                db.session.query(Trending).filter_by(
                    videoid=result['videoid']).delete()
                db.session.add(new_trending_video)

            db.session.commit()
        print(total_expect_views, total_videos_views)
        print('Total time to calculate trending: ', time.time() - time_t)
        
def delete_old_videos():
    '''Delete videos those are too old'''
    #with app.app_context():
    time_t = time.time()
    videos = Video.query.all()
    videos_view_time = VideoViewTime.query.all()

    result = videos_schema.dump(videos).data  # List of videos
    result_view_time = videos_view_time_schema.dump(videos_view_time).data

    result_videoid = [item['videoid'] for item in result]
    pivot_storage = time.time() - params.PARAMS_CONFIG['STORAGE_TIME']
   
    update_list = [
        item for item in result if int(item['video_timestamp']) > pivot_storage * 1000]
    delete_list = [
        item for item in result if int(item['video_timestamp']) < pivot_storage * 1000]

    bonus_delete_list = [
        item for item in result_view_time if item['videoid'] not in result_videoid]

    for item in delete_list:
        db.session.query(Video).filter_by(video_timestamp=item['video_timestamp']).delete()
        db.session.query(VideoViewTime).filter_by(videoid=item['videoid']).delete()
    
    for item in bonus_delete_list:
        db.session.query(VideoViewTime).filter_by(videoid=item['videoid']).delete()

    db.session.commit()
    print('Total time to delete old videos: ', time.time() - time_t)
        
def delete_old_viewtimes():
    time_t = int(time.time())
    today = datetime.fromtimestamp(int(time_t))

    pivot_viewtime = time.mktime(datetime(
        today.year, today.month, today.day, params.PARAMS_CONFIG['DAILY_PIVOT']).timetuple())

    videos_view_time = VideoViewTime.query.all()

    result_view_time = videos_view_time_schema.dump(videos_view_time).data

    try:
        db.session.query(VideoViewTime).delete()
        db.session.commit()
    except:
        db.session.rollback()    

    for item in result_view_time:
        if not item['view_timestamp']:
            viewtime_list = [time_t * 1000]
            #print(viewtime_list)
        else:
            viewtime_list = [*map(int, item['view_timestamp'].split(','))]
            #print('else: ', viewtime_list)
         
        updated_viewtime_list = [
            viewtime for viewtime in viewtime_list if viewtime > pivot_viewtime * 1000]

        if not updated_viewtime_list:
            item['view_timestamp'] = str(1000 * pivot_viewtime)
        else:
            item['view_timestamp'] = ','.join([*map(str, updated_viewtime_list)])

        video_update_viewtime = VideoViewTime(item['videoid'], item['view_timestamp'])
        db.session.add(video_update_viewtime)

    db.session.commit()

    print('Total time to delete old viewtimes: ', time.time() - time_t)

def delete_old_videos_like():
    '''
        Delete old videos in video_like table
    '''
    time_t = int(time.time())
    pivot_storage = time.time() - params.PARAMS_CONFIG['STORAGE_TIME']

    video_like = db.session.query(VideoLike)
    result = video_like_schema.dump(video_like).data

    delete_list = [
        item for item in result if int(item['video_timestamp']) < pivot_storage * 1000]

    for item in delete_list:
        db.session.query(VideoLike).filter_by(
            video_timestamp=item['video_timestamp']).delete()
    db.session.commit()
    print('Total time to delete old video likes: ', time.time() - time_t)

delete_old_videos()
delete_old_viewtimes()
delete_old_videos_like()
update_trending()
