# 마피아 게임에 참여하는 모든 참여자는 이 객체를 사용한다.

class Player:
    def __init__(self, name, age=18, gender="man", mbti="entp", job="학생", is_player=False):
        self.name = name #이름
        self.age = age #나이
        self.gender = gender #성별
        self.mbti = mbti #MBTI 유형
        self.real_job = job #실제 직업
        self.is_player = is_player #나인가?

        #마피아 게임 관련 속성
        self.job = None #마피아 직업
        self.alive = True #생존 여부

    def speak(self):
        pass

    def vote(self, target):
        """타겟 플레이어에게 투표"""
        pass

    def die(self):
        """플레이어 사망 처리"""
        self.alive = False

