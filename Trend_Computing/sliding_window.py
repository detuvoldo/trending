# -*- coding: utf-8 -*-
# trending.py

'''
    Thuật toán:
    1. Chia thời gian lưu trữ 1 tuần thành các khoảng nhỏ 5 phút (bins). 
    Thuật toán sử dụng xác suất kỳ vọng để tính ranking cho mỗi video 
    bằng cách tính kỳ vọng trong 1 tuần để các video cũ sẽ bị lãng quên đi.
    
    2. Với mỗi video, một bộ đếm sẽ đếm lượt view của video đó trong "bin" hiện tại
    
    3. Tính độ hội tụ KL theo các bước sau:
        - Tính xác suất của bin đầy đủ gần nhất (5 phút gần nhất, video có bao nhiêu lượt views???).
        - Tính xác suất kỳ vọng trên toàn bộ các khoảng, bao gồm cả khoảng gần nhất.
        - Tính độ hội tụ KL theo công thức.
    
    4. Lưu trữ điểm KL cao nhất cùng với timestamp của video

    5. Tính độ phân rã hàm mũ và nhân với điểm KL cao nhất
'''

class Sliding_window:
    """
        Mỗi cửa sổ trượt sẽ lưu những thông tin bao gồm 1 mốc thời gian t (từ thời điểm t-5 phút đến t phút)
        Đồng thời, với mỗi key là video_id, sẽ có các values đi cùng là list các thông số về score tính toán 
        được thông qua class Video và lưu trong class Score
    """
    def __init__(self, score_list=[]):
        self.score_list = score_list

    def _sort_list_trending(self):
        # sort score list based on each video's kl_score
        return sorted(self.score_list, key=lambda x: x['kl_score'])
