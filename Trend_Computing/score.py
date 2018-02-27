# -*- coding: utf-8 -*-
# score.py

class Score:
    """
        This class is used to save important values of a video in a Sliding Window.

    """
    def __init__(self, video_id, duration=0, probability=0.0, expectation=0.0, kl_score=0.0):
        self.video_id = video_id
        self.duration = duration
        self.probability = probability
        self.expectation = expectation
        #self.maximum = maximum
        self.kl_score = kl_score

    def _get_score_list(self):
        score_list = {'videoid': self.video_id, 'kl_score': self.kl_score}
        return score_list
