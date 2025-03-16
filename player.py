# 마피아 게임에 참여하는 모든 참여자는 이 객체를 사용한다.

class Player:
    def __init__(self, name, age=18, gender="man", mbti="entp", job="학생"):
        self.name = name
        self.age = age
        self.gender = gender
        self.mbti = mbti
        self.real_job = job
        self.alive = True

    def speak(self):
    def vote(self, target):
        """타겟 플레이어에게 투표"""
        pass

    def die(self):
        """플레이어 사망 처리"""
        self.alive = False


minsung = Player(name="구민성")
kloud = Player(name="구름", age=45)

