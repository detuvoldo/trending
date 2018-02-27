# -*- coding: utf-8 -*-
# crud.py

import time

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from Trend_Computing import config

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + \
    config.DATABASE_CONFIG['user'] + ':' + \
    config.DATABASE_CONFIG['password'] + '@' + \
    config.DATABASE_CONFIG['host'] + '/' + \
    config.DATABASE_CONFIG['dbname']
db = SQLAlchemy(app)
ma = Marshmallow(app)

ref_values_organic = ['NEWVIDEO',
                      'NOTIFICATIONPERSONAL', 'NOTIFICATIONFRIEND', 'RELATEDVIDEO', 'NOTIFICATIONSYSTEM']

'''
ref_values = ['MYVIDEO', 'USERPROFILE','IDOLVIDEO','LIKEDVIDEO','TRENDINGVIDEO','HOTVIDEO','NOTIFICATIONPERSONAL',
   'AUDIODETAIL','HASHTAG','EXPLOREVIDEO','NOTIFICATIONFRIEND','EXPLOREHOTVIDEO',
   'RELATEDVIDEO','NOTIFICATIONSYSTEM','NEWVIDEO',
   'APP','WEB','LOOP']
'''

class Video(db.Model):
    '''
        Structure of Video database, including 2 columns: videoid and video_timestamp.
    '''
    id = db.Column(db.Integer, primary_key=True)
    videoid = db.Column(db.String(80), unique=True)
    video_timestamp = db.Column(db.String(20), unique=True)

    def __init__(self, videoid, video_timestamp):
        self.videoid = videoid
        self.video_timestamp = video_timestamp


class VideoSchema(ma.Schema):
    '''
        Format of output data in Video table.
    '''
    class Meta:
        # Fields to expose
        fields = ('videoid', 'video_timestamp')


class VideoViewTime(db.Model):
    '''
        Structure of View Time database, including 2 columns: videoid and view_timestamp.
    '''
    id = db.Column(db.Integer, primary_key=True)
    videoid = db.Column(db.String(80), unique=True)
    view_timestamp = db.Column(db.String(100000), index=True)

    def __init__(self, videoid, view_timestamp):
        self.videoid = videoid
        self.view_timestamp = view_timestamp


class VideoViewTimeSchema(ma.Schema):
    '''
        Format of output data in View Time table.
    '''
    class Meta:
        fields = ('videoid', 'view_timestamp')


class Trending(db.Model):
    '''
        Structure of Trending database, including 2 columns: videoid and view_timestamp.
    '''
    id = db.Column(db.Integer, primary_key=True)
    videoid = db.Column(db.String(80), unique=True)
    kl_score = db.Column(db.Float, default=0.0)

    def __init__(self, videoid, kl_score):
        self.videoid = videoid
        self.kl_score = kl_score


class TrendingSchema(ma.Schema):
    '''
        Format of output data in Trending table.
    '''
    class Meta:
        fields = ('videoid', 'kl_score')


class VideoLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    videoid = db.Column(db.String(80), unique=True)
    video_timestamp = db.Column(db.String(20), unique=True)
    total_likes = db.Column(db.Float, default=0.0)
    event_timestamp = db.Column(db.String(10000))

    def __init__(self, videoid, video_timestamp, total_likes, event_timestamp):
        self.videoid = videoid
        self.video_timestamp = video_timestamp
        self.total_likes = total_likes
        self.event_timestamp = event_timestamp


class VideoLikeSchema(ma.Schema):
    '''
        Format of output data in VideoLike table. 
    '''
    class Meta:
        fields = ('videoid', 'video_timestamp', 'total_likes', 'event_timestamp')

video_schema = VideoSchema()
videos_schema = VideoSchema(many=True)

video_view_time_schema = VideoViewTimeSchema()
videos_view_time_schema = VideoViewTimeSchema(many=True)

trendings_schema = TrendingSchema(many=True)
video_like_schema = VideoLikeSchema(many=True)

# endpoint to create new video
@app.route("/video", methods=["POST"])
def add_video():
    '''Add new videos to database'''
    time_t = (time.time())
    datas = request.json
    if not datas:
        return jsonify("Nothing added!!!")
    else:
        #print(datas)
        for data in datas:
            videoid = data.get('videoid')
            video_timestamp = data.get('video_timestamp')
            view_timestamp = ','.join([*map(str, data.get('view_timestamp'))])

            # If videoid not in database, commit new video to database
            changed_vid = db.session.query(
                Video).filter_by(videoid=videoid).first()

            if not changed_vid:
                new_vid = Video(videoid, video_timestamp)
                #new_vid_view_time = VideoViewTime(videoid, view_timestamp)
                db.session.add(new_vid)
                #db.session.add(new_vid_view_time)
                db.session.commit()
            else:
                changed_vid_view_time = db.session.query(
                    VideoViewTime).filter_by(videoid=videoid).first()

                if not changed_vid_view_time:
                    changed_vid_view_time = VideoViewTime(videoid, view_timestamp)
                    db.session.add(changed_vid_view_time)
                else:
                    changed_vid_view_time.view_timestamp += ',' + view_timestamp
            db.session.commit()
    print('Total time to add videos: ', time.time() - time_t)
    return jsonify("YES")

# endpoint to show all videos
@app.route("/video", methods=["GET"])
def get_video():
    '''Get list of videos to screen'''
    time_t = time.time()
    videos = Video.query.all()
    result = videos_schema.dump(videos)
    print('Total time to show videos: ', time.time() - time_t)
    return jsonify(sorted(result.data, key=lambda k: k['video_timestamp'], reverse=True))

@app.route("/viewtime", methods=["GET"])
def get_view_time():
    '''Get list of view times to screen'''
    time_t = time.time()
    videos_view_time = VideoViewTime.query.all()
    result = videos_view_time_schema.dump(videos_view_time).data

    print('Total time to show video view time: ', time.time() - time_t)
    return jsonify(sorted(result, key=lambda k: len(k['view_timestamp']), reverse=True))

#@app.route("/compute", methods=["GET"])
@app.route("/trending", methods=["GET"])
def get_trending():
    time_t = time.time()
    '''Get list of trending based on kl_score in the order of kl_score'''
    trending_list = Trending.query.all()

    trend_list = trendings_schema.dump(trending_list).data
    trend_list = [item for item in trend_list if item['kl_score'] > 0]
    print('Total time to show trending:', time.time() - time_t)
    return jsonify(sorted(trend_list, key=lambda k: k['kl_score'], reverse=True))

@app.route('/like', methods=['POST'])
def add_video_like():
    '''
        Get video likes to view
    '''
    time_t = time.time()
    datas = request.json
    if not datas:
        return "Nothing added!!!"
    else:
        for data in datas:
            videoid = data.get('videoid')
            ref = data.get('ref')
            video_timestamp = data.get('video_timestamp')
            event_timestamp = data.get('event_timestamp')

            if ref not in ref_values_organic:
                continue
            else:
                if db.session.query(VideoLike).filter_by(videoid=videoid).count() < 1:

                    new_video_like = VideoLike(videoid, video_timestamp, len(event_timestamp), ','.join([*map(str, event_timestamp)]))
                    db.session.add(new_video_like)
                else:
                    video_like = db.session.query(
                        VideoLike).filter_by(videoid=videoid).first()

                    video_like.total_likes += len(event_timestamp)
                    video_like.event_timestamp += ',' + ','.join([*map(str, event_timestamp)])
        db.session.commit()
    print('Total time to POST: ', time.time() - time_t)

    return jsonify('POST video likes successfully')


@app.route("/likes", methods=["GET"])
def get_like():
    time_t = time.time()
    '''Get list of trending based on kl_score in the order of kl_score'''
    like_list = VideoLike.query.all()
    like_list = video_like_schema.dump(like_list).data

    print('Total time to show likes:', time.time() - time_t)
    return jsonify(like_list)

db.create_all()
#update_trending()
#video_delete()


if __name__ == '__main__':
    app.run(host=config.CONNECTION_CONFIG['host'], debug=True)
    