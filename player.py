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


p1 = Player(name="철수", mbti="enfj")
p2 = Player(name="영희", gender="woman")
p3 = Player(name="영수", mbti="intp")
p4 = Player(name="영철", mbti="estj")
p5 = Player(name="영호", mbti="infp")
p6 = Player(name="옥순", gender="woman", mbti="entj")
p7 = Player(name="영자", gender="woman", mbti="esfp")
p8 = Player(name="남수")
p9 = Player(name="경수", mbti="isfj")
p10 = Player(name="유리", gender="woman", mbti="enfp")
p11 = Player(name="정숙", gender="woman", mbti="istj")
p12 = Player(name="짱구", mbti="enfp")
