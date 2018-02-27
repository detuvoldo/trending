# -*- coding: utf-8 -*-
"""
	Load data from JSON file to a new file with suitable format
"""
import math
import time
import params


class Trend_Computing:
    '''
        This class contains functions used in order to compute trending.
    '''
    def __init__(self, video_id, video_timestamp, current_views=params.PARAMS['SMOOTHING']):
        self.video_timestamp = video_timestamp
        self.video_id = video_id
        self.current_views = current_views

    def _compute_duration(self):
        return (int(time.time()) - (self.video_timestamp / 1000))

    def _get_total_views(self, data_file):
        count = 0
        if self.video_id in data_file['videoid'].tolist():
            for view_timestamp in data_file.loc[data_file['videoid'] == self.video_id]['view_timestamp'].iloc[0]:
                if view_timestamp >= self.video_timestamp * 1000:
                    count += 1
            if count >= params.PARAMS['SMOOTHING']:
                return float(count)
        return params.PARAMS['SMOOTHING']

    def _get_views(self, time_pivot, data_file):
        count = 0
        if self.video_id in data_file['videoid'].tolist():
            for view_timestamp in data_file.loc[data_file['videoid'] == self.video_id]['view_timestamp'].iloc[0]:
                if view_timestamp >= time_pivot * 1000:
                    count += 1
        return float(count)
    
